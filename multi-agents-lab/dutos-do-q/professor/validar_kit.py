"""validar_kit.py — a checagem que o professor roda em D-1.

Executa as duas missões nos dois modos (referência e ingênuo) com o backend mock, e confere que os
números da calibração continuam batendo depois de qualquer mudança em dados, contratos ou avaliadores.

    python professor/validar_kit.py

Leva cerca de 40 segundos. Não baixa modelo de linguagem: o mock responde as lacunas e o auditor.
"""
import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))
os.environ["LLM_BACKEND"] = "mock"
os.chdir(RAIZ)

from lake import Lake                      # noqa: E402
from contrato import carregar_contratos    # noqa: E402
import agentes, avaliacao, dutos, referencia  # noqa: E402
from agente import Memoria, CacheSemantico, consumir_eventos  # noqa: E402

ESPERADO = {
    "m1_referencia": 100.0,
    "m1_caos_bonus": 20.0,
    "m2_referencia": 100.0,
    "auditor": 100.0,
    "construtor_rows_in": 2243,
    "construtor_rejeitadas": 14,
}

falhas = []


def conferir(nome, obtido, esperado):
    ok = abs(float(obtido) - float(esperado)) < 0.01
    print(f"  [{'OK  ' if ok else 'FALHA'}] {nome:<34} obtido {obtido}  esperado {esperado}")
    if not ok:
        falhas.append(nome)


def main():
    contratos = carregar_contratos()
    agentes.carregar_modelo()
    trabalho = RAIZ / "_validacao"
    shutil.rmtree(trabalho, ignore_errors=True)
    trabalho.mkdir()

    print("\n1. CONSTRUTOR (backend mock: gera, valida, executa)")
    import yaml
    contrato_yaml = yaml.safe_dump({"fontes": contratos}, allow_unicode=True, sort_keys=False)
    g = agentes.gerar(contrato_yaml, "processe clientes antes de transacoes", verboso=False)
    problemas = agentes.validar(g["codigo"])
    print(f"  [{'OK  ' if not problemas else 'FALHA'}] guardrails{'':<24} {problemas or 'passou'}")
    if problemas:
        falhas.append("guardrails do construtor")

    lake_c = Lake(str(trabalho / "lake_construtor")).criar_todas()
    inbox_c = dutos.preparar_inbox(RAIZ)
    dutos.bronze(lake_c, inbox_c)
    m = agentes.executar(g["codigo"], lake_c, {"fontes": contratos})
    conferir("linhas lidas", m["rows_in"], ESPERADO["construtor_rows_in"])
    conferir("linhas rejeitadas", m["rows_rejected"], ESPERADO["construtor_rejeitadas"])

    print("\n2. MISSÃO 1 · referência + Caos")
    lake1 = Lake(str(trabalho / "lake_m1")).criar_todas()
    r1 = avaliacao.avaliar_m1(lake1, dutos.preparar_inbox(RAIZ),
                              lambda l: referencia.pipeline(l, {"fontes": contratos}),
                              com_caos=True, pasta_caos=RAIZ / "dados" / "caos")
    conferir("score M1", r1["score"], ESPERADO["m1_referencia"])
    conferir("bônus do Caos", r1["bonus_caos"], ESPERADO["m1_caos_bonus"])

    print("\n3. MISSÃO 1 · modo ingênuo (tem que ser pior)")
    lake_i = Lake(str(trabalho / "lake_ingenuo")).criar_todas()
    inbox_i = dutos.preparar_inbox(RAIZ)
    dutos.bronze(lake_i, inbox_i, "ingenuo")
    _pipeline_ingenuo(lake_i, contratos)
    dutos.gold(lake_i, "ingenuo")
    c1 = lake_i.contar("silver.transacoes")
    dutos.bronze(lake_i, inbox_i, "ingenuo")
    _pipeline_ingenuo(lake_i, contratos)
    mi = dutos.gold(lake_i, "ingenuo")
    c2 = lake_i.contar("silver.transacoes")
    duplicou = c2 > c1
    print(f"  [{'OK  ' if duplicou else 'FALHA'}] ingênuo duplica na 2ª execução   {c1} → {c2}, re-embeddings {mi['embeds_executados']}")
    if not duplicou:
        falhas.append("o modo ingênuo deixou de ser ruim")

    print("\n4. MISSÃO 2 · referência")
    lake2 = Lake(str(trabalho / "lake_m2")).criar_todas()
    dutos.bronze(lake2, dutos.preparar_inbox(RAIZ))
    referencia.pipeline(lake2, {"fontes": contratos})
    dutos.gold(lake2)
    memoria = Memoria(str(trabalho / "agente"))
    cache = CacheSemantico(str(trabalho / "agente"))
    memoria.loja.limpar()
    cache.loja.limpar()
    for mem in json.loads((RAIZ / "dados" / "memorias_seed.json").read_text(encoding="utf-8")):
        memoria.lembrar(mem["cliente_id"], mem["texto"], mem["tipo"], mem["data"])
    linha = json.loads((RAIZ / "dados" / "linha_do_tempo.json").read_text(encoding="utf-8"))
    r2 = avaliacao.avaliar_m2(lake2, linha, memoria, cache, lambda l: dutos.sync(l), consumir_eventos)
    conferir("score M2", r2["score"], ESPERADO["m2_referencia"])
    conferir("embeddings no ciclo", r2["embeds_totais"], 2)

    print("\n5. AUDITOR · 4 cenários")
    ra = avaliacao.avaliar_auditor(agentes.REGRAS_EXEMPLO)
    conferir("score do auditor", ra["score"], ESPERADO["auditor"])

    print("\n6. DUTO EXTERNO · idempotência")
    dutos.bcb(lake2, RAIZ / "dados" / "bcb" / "snapshot.json")
    b2 = dutos.bcb(lake2, RAIZ / "dados" / "bcb" / "snapshot.json")
    conferir("linhas novas na 2ª execução", b2["novas"], 0)
    dutos.views(lake2)

    shutil.rmtree(trabalho, ignore_errors=True)
    print("\n" + "=" * 68)
    if falhas:
        print(f"KIT COM {len(falhas)} FALHA(S): " + ", ".join(falhas))
        return 1
    print("KIT VALIDADO: todos os números da calibração batem.")
    return 0


def _pipeline_ingenuo(lake, contratos):
    """O duto sem contrato: lê tudo da Bronze, converte na marra e faz APPEND. Existe para o contraste."""
    from contrato import contrato_para, ler_arquivo
    from lake import agora
    for r in lake.ler("bronze.arquivos").to_dict("records"):
        c = contrato_para(r["nome"], contratos)
        if c is None:
            continue
        try:
            df, _ = ler_arquivo(r["nome"], bytes(r["conteudo"]), c)
        except Exception:
            continue
        df = df.copy()
        df["hash"] = ""
        df["arquivo"] = r["nome"]
        df["atualizado_em"] = agora()
        if c["fonte"] == "documentos":
            df["vigente"] = True
            df["autoritativo"] = True
        lake.acrescentar(f"silver.{c['fonte']}", df)


if __name__ == "__main__":
    sys.exit(main())
