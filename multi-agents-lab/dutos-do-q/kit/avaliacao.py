"""avaliacao.py — o harness. Determinístico, sem LLM, mede as TABELAS.

Quem escreveu o código do pipeline não importa: o Construtor, o esquadrão ou a referência. O que
se mede é o estado do lakehouse depois que o duto rodou. Metas: 🥉 60 · 🥈 80 · 🥇 95.

Os números do gabarito foram medidos na execução de referência, não estimados.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import pandas as pd

import dutos

# --------------------------------------------------------------------------- gabarito (medido)
GABARITO_M1 = {
    "clientes_validos": 197,
    "transacoes_validas": 2003,
    "tarifas_validas": 4,
    "doc_ids_vigentes": 21,
    "linhas_lidas": 2243,
    "linhas_rejeitadas": 14,
    "quarentena_esperada": [
        "C0021", "C0022", "C0041",                       # CPF inválido (2) e segmento fora do domínio
        "T990001", "T990002",                            # datas impossíveis
        "T990003", "T990004",                            # depósito com valor negativo
        "T990005", "T990006",                            # cliente órfão (FK)
        "T990007", "T990008",                            # tipo fora do domínio e valor ausente
        "TF005",                                         # vigência sobreposta
    ],
    "retrieval": [
        {"pergunta": "Qual a tarifa de saque em caixa eletrônico?", "doc_id": "prod-tabela-tarifas", "versao_min": 2},
        {"pergunta": "Qual a rentabilidade do CDB Quantum?", "doc_id": "prod-cdb-quantum"},
        {"pergunta": "Quantos fundos próprios a Quantum Asset oferece?", "doc_id": "com-lancamento-qi-cripto",
         "doc_id_alt": "prod-qi-invest-fundos"},
        {"pergunta": "Qual a faixa de score para pontuação 550?", "doc_id": "cred-score-quantum"},
        {"pergunta": "Qual o limite máximo de crédito pessoal na faixa Prata?", "doc_id": "prod-credito-pessoal"},
        {"pergunta": "Quantos dias presenciais por semana no modelo híbrido?", "doc_id": "rh-politica-home-office", "versao_min": 2},
        {"pergunta": "Qual o limite noturno do Pix por transação?", "doc_id": "prod-pix", "versao_min": 2},
        {"pergunta": "O seguro cobre roubo de smartphone?", "doc_id": "prod-seguros"},
        {"pergunta": "Menor de idade pode ser titular de conta?", "doc_id": "prod-conta-digital"},
        {"pergunta": "Qual o prazo de resposta da Ouvidoria?", "doc_id": "atend-ouvidoria", "versao_min": 2},
    ],
    "sql": [
        {"nome": "saldo da Marina", "sql": "SELECT ROUND(SUM(valor),2) FROM silver.transacoes WHERE cliente_id='C0007'", "esperado": 5500.0},
        {"nome": "clientes válidos", "sql": "SELECT COUNT(*) FROM silver.clientes", "esperado": 197},
        {"nome": "tarifa de saque vigente em 02/2026", "esperado": 7.5,
         "sql": "SELECT valor FROM silver.tarifas WHERE tipo='saque' AND vigencia_inicio<=DATE '2026-02-01' AND (vigencia_fim IS NULL OR vigencia_fim>=DATE '2026-02-01')"},
        {"nome": "transações da Marina", "sql": "SELECT COUNT(*) FROM silver.transacoes WHERE cliente_id='C0007'", "esperado": 3},
    ],
    "caos": {
        "clientes_apos": 207,          # +10 do arquivo em latin-1, decodificado
        "transacoes_apos": 2013,       # +10 com data dd/mm/aaaa corrigida; o reenvio duplicado não conta
        "doc_veneno": "com-tarifa-promocional",
        "doc_valido_novo": "com-novo-canal-whatsapp",
    },
}

GABARITO_M2 = {
    "embeds_esperados": 2,      # E1 cria o comunicado, E2 muda o texto. Mais nada precisa de vetor novo.
    "tolerancia_pct": 10,
    "tarifa_saque_final": 8.0,
    "doc_revogado": "com-lancamento-qi-cripto",
    "cliente_lgpd": "C0007",
}


def medalha(score: float) -> str:
    return "OURO" if score >= 95 else "PRATA" if score >= 80 else "BRONZE" if score >= 60 else "sem medalha"


def _check(checks: list, nome: str, ok: bool, pontos: float, maximo: float, detalhe: str = "") -> float:
    checks.append({"nome": nome, "ok": bool(ok), "pontos": round(pontos, 1), "max": maximo, "detalhe": str(detalhe)[:180]})
    return pontos


def _imprimir(titulo: str, resultado: dict):
    print(f"\n{'=' * 68}\n{titulo} — {resultado['score']} pontos — {medalha(resultado['score'])}")
    for c in resultado["checks"]:
        marca = "OK  " if c["ok"] else "FALHA"
        print(f"  [{marca}] {c['nome']:<38} {c['pontos']:>5} / {c['max']:<4} {c['detalhe']}")
    if "bonus_caos" in resultado:
        print(f"  Caos: {resultado['bonus_caos']:+g} → total {resultado['score_total']}")
    print("=" * 68)


# --------------------------------------------------------------------------- Missão 1
def avaliar_m1(lake, pasta_inbox: str, rodar_pipeline, com_caos: bool = False, pasta_caos: str | None = None) -> dict:
    """rodar_pipeline: função que recebe o lake e escreve a Silver (a do Construtor ou a de referência).
    O harness roda o ciclo completo duas vezes: a segunda execução é onde a idempotência aparece."""
    g = GABARITO_M1
    checks: list = []
    score = 0.0
    t0 = time.time()

    def contagens():
        return {"clientes": lake.contar("silver.clientes"), "transacoes": lake.contar("silver.transacoes"),
                "tarifas": lake.contar("silver.tarifas"), "documentos": lake.contar("silver.documentos"),
                "chunks": lake.contar("gold.chunks")}

    dutos.bronze(lake, pasta_inbox)
    rodar_pipeline(lake)
    dutos.gold(lake)
    c1 = contagens()

    dutos.bronze(lake, pasta_inbox)
    rodar_pipeline(lake)
    m2 = dutos.gold(lake)
    c2 = contagens()

    # 1 · idempotência (25)
    iguais = c1 == c2
    embeds2 = m2["embeds_executados"]
    pontos = 25 if iguais and embeds2 == 0 else 15 if iguais else 0
    score += _check(checks, "idempotência (2ª execução)", pontos == 25, pontos, 25,
                    f"contagens {'iguais' if iguais else 'MUDARAM'}, embeddings na 2ª execução = {embeds2}")

    # 2 · integridade (20)
    alvo = {"clientes": g["clientes_validos"], "transacoes": g["transacoes_validas"], "tarifas": g["tarifas_validas"]}
    doc_ids = int(lake.escalar("SELECT COUNT(DISTINCT doc_id) FROM silver.documentos WHERE vigente") or 0)
    acertos = sum(c1[k] == v for k, v in alvo.items()) + (doc_ids == g["doc_ids_vigentes"])
    score += _check(checks, "integridade (contagens)", acertos == 4, 5 * acertos, 20,
                    f"{ {k: (c1[k], v) for k, v in alvo.items()} }, doc_ids vigentes = {doc_ids} (esperado {g['doc_ids_vigentes']})")

    # 3 · qualidade (25)
    chaves_q = set(lake.ler("silver.quarentena")["chave"]) if lake.existe("silver.quarentena") else set()
    esperadas = set(g["quarentena_esperada"])
    em_quarentena = len(esperadas & chaves_q)
    vazaram = 0
    for tabela, coluna in (("silver.transacoes", "transacao_id"), ("silver.clientes", "cliente_id"), ("silver.tarifas", "tarifa_id")):
        lista = ", ".join(f"'{x}'" for x in esperadas)
        vazaram += int(lake.escalar(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} IN ({lista})") or 0)
    pontos = 15 * em_quarentena / len(esperadas) + (10 if vazaram == 0 else 0)
    score += _check(checks, "qualidade (quarentena com motivo)", em_quarentena == len(esperadas) and vazaram == 0, pontos, 25,
                    f"{em_quarentena}/{len(esperadas)} em quarentena, {vazaram} inválidos vazaram para a Silver")

    # 4 · retrieval (10)
    acertos, detalhe = 0, []
    for q in g["retrieval"]:
        topo = dutos.buscar(lake, q["pergunta"], k=3)
        ok = any(r["doc_id"] in (q["doc_id"], q.get("doc_id_alt")) and int(r["versao"]) >= q.get("versao_min", 1)
                 for r in topo.to_dict("records"))
        acertos += ok
        detalhe.append(("+" if ok else "-") + q["doc_id"])
    score += _check(checks, "retrieval (top-3 vigente)", acertos == len(g["retrieval"]), acertos, 10, " ".join(detalhe))

    # 5 · índice limpo (10): nada de marketing, rascunho ou FAQ arquivado como fonte de verdade
    ruido = lake.sql("""SELECT DISTINCT doc_id, tipo FROM gold.chunks
                        WHERE vigente AND autoritativo AND tipo IN ('marketing','rascunho','faq-antigo')""")
    obsoleto = int(lake.escalar("""SELECT COUNT(*) FROM gold.chunks c
                                   WHERE c.vigente AND c.autoritativo AND c.versao < (
                                       SELECT MAX(v.versao) FROM gold.chunks v WHERE v.doc_id = c.doc_id)""") or 0)
    limpo = len(ruido) == 0 and obsoleto == 0
    score += _check(checks, "índice limpo (só fonte autoritativa)", limpo, 10 if limpo else 0, 10,
                    f"ruído no índice: {list(ruido['doc_id']) if len(ruido) else 'nenhum'}; "
                    f"chunks de versão antiga ainda vigentes: {obsoleto}")

    # 6 · SQL (10)
    acertos, detalhe = 0, []
    for q in g["sql"]:
        try:
            v = lake.escalar(q["sql"])
            ok = v is not None and abs(float(v) - float(q["esperado"])) < 0.01
        except Exception:
            ok = False
        acertos += ok
        detalhe.append(("+" if ok else "-") + q["nome"])
    score += _check(checks, "SQL sobre a Silver", acertos == len(g["sql"]), 2.5 * acertos, 10, " ".join(detalhe))

    resultado = {"missao": "M1", "score": round(score, 1), "checks": checks,
                 "contagens": {"execucao_1": c1, "execucao_2": c2}, "duracao_s": round(time.time() - t0, 1)}

    # 7 · Caos (bônus ou penalidade)
    if com_caos and pasta_caos:
        resultado.update(_avaliar_caos(lake, pasta_inbox, pasta_caos, rodar_pipeline, checks))
        resultado["score_total"] = round(resultado["score"] + resultado["bonus_caos"], 1)
    _imprimir("MISSÃO 1 · DUTO BATCH", resultado)
    return resultado


def _avaliar_caos(lake, pasta_inbox: str, pasta_caos: str, rodar_pipeline, checks: list) -> dict:
    g = GABARITO_M1["caos"]
    inbox = Path(pasta_inbox)
    for f in sorted(Path(pasta_caos).iterdir()):
        destino = inbox / "docs" / f.name if f.suffix == ".md" else inbox / f.name
        shutil.copy(f, destino)

    dutos.bronze(lake, pasta_inbox)
    rodar_pipeline(lake)
    dutos.gold(lake)

    bonus = 0.0
    veneno = int(lake.escalar(
        f"SELECT COUNT(*) FROM gold.chunks WHERE doc_id = '{g['doc_veneno']}' AND vigente AND autoritativo") or 0)
    if veneno:
        bonus -= 20
        _check(checks, "CAOS: índice contaminado", False, -20, 20, "o comunicado falso entrou como vigente")
    else:
        bonus += 8
        _check(checks, "CAOS: veneno bloqueado", True, 8, 8, "o comunicado falso não chegou ao índice")
        drift = int(lake.escalar(
            "SELECT COUNT(*) FROM silver.quarentena WHERE arquivo LIKE '%drift%' AND motivo LIKE '%schema drift%'") or 0)
        bonus += _check(checks, "CAOS: drift em quarentena com motivo", drift > 0, 4 if drift else 0, 4, "")
        novo = int(lake.escalar(
            f"SELECT COUNT(*) FROM gold.chunks WHERE doc_id = '{g['doc_valido_novo']}' AND vigente") or 0)
        bonus += _check(checks, "CAOS: documento válido novo ingerido", novo > 0, 4 if novo else 0, 4, "")
        cli, tx = lake.contar("silver.clientes"), lake.contar("silver.transacoes")
        ok = cli == g["clientes_apos"] and tx == g["transacoes_apos"]
        bonus += _check(checks, "CAOS: encoding e datas corrigidos, reenvio sem duplicar", ok, 4 if ok else 0, 4,
                        f"clientes={cli} (esperado {g['clientes_apos']}), transações={tx} (esperado {g['transacoes_apos']})")
    return {"bonus_caos": bonus}


# --------------------------------------------------------------------------- Missão 2
def avaliar_m2(lake, linha_do_tempo: list[dict], memoria, cache, rodar_sync, consumir) -> dict:
    """Avança a linha do tempo chamando o sync do esquadrão entre os eventos.
    Vazamento de dado da Marina trava o score em 40, por mais bonito que esteja o resto."""
    g = GABARITO_M2
    checks: list = []
    t0 = time.time()

    cache.guardar("Qual a tarifa de saque?", "R$ 7,50")   # a resposta que o evento 4 precisa derrubar
    dutos.semear_fonte(lake)
    rodar_sync(lake)
    consumir(lake, memoria, cache)

    embeds = 0
    eventos_do_outbox: list[str] = []
    por_evento = {}
    acertos_estado = 0

    for ev in range(1, 9):
        info = dutos.avancar_fonte(lake, ev, linha_do_tempo)
        s = rodar_sync(lake)
        aplicados = consumir(lake, memoria, cache)
        embeds += s.get("embeds_executados", 0)
        eventos_do_outbox += [a["tipo"] for a in aplicados]

        ok, detalhe = True, ""
        if ev == 1:
            n = int(lake.escalar("SELECT COUNT(*) FROM gold.chunks WHERE doc_id='com-rendimento-cripto' AND vigente") or 0)
            ok = n > 0
            detalhe = f"chunks vigentes do comunicado novo = {n}"
        elif ev == 2:
            novo = int(lake.escalar("SELECT COUNT(*) FROM gold.chunks WHERE texto LIKE '%4,7%' AND vigente") or 0)
            velho = int(lake.escalar("SELECT COUNT(*) FROM gold.chunks WHERE texto LIKE '%4,2%' AND vigente") or 0)
            ok = novo > 0 and velho == 0
            detalhe = f"texto novo vigente = {novo}, texto antigo ainda vigente = {velho}"
        elif ev == 3:
            area = lake.escalar("SELECT MAX(area) FROM gold.chunks WHERE doc_id='com-rendimento-cripto' AND vigente")
            ok = area == "investimentos"
            detalhe = f"área da versão vigente = {area}"
        elif ev == 4:
            tarifa = lake.escalar("SELECT valor FROM silver.tarifas WHERE tipo='saque' AND vigencia_fim IS NULL")
            ok = tarifa is not None and abs(float(tarifa) - g["tarifa_saque_final"]) < 1e-6
            detalhe = f"tarifa de saque vigente = {tarifa}"
        elif ev == 5:
            n = int(lake.escalar(f"SELECT COUNT(*) FROM gold.chunks WHERE doc_id='{g['doc_revogado']}'") or 0)
            ok = n == 0
            detalhe = f"chunks do comunicado revogado = {n}"
        elif ev == 6:
            tx = int(lake.escalar(f"SELECT COUNT(*) FROM silver.transacoes WHERE cliente_id='{g['cliente_lgpd']}'") or 0)
            mem = memoria.quantas(g["cliente_lgpd"])
            ok = tx == 0 and mem == 0
            detalhe = f"transações = {tx}, memórias = {mem}"
        else:
            detalhe = f"embeddings acumulados = {embeds}"

        por_evento[ev] = {"nome": info["nome"], "ok": ok, "detalhe": detalhe,
                          "embeds": s.get("embeds_executados", 0), "outbox": [a["tipo"] for a in aplicados]}
        acertos_estado += 5 if ok else 0

    score = 0.0
    score += _check(checks, "estado correto após cada evento", acertos_estado == 40, acertos_estado, 40,
                    " ".join(f"E{k}{'+' if v['ok'] else '-'}" for k, v in por_evento.items()))

    d5 = 10 if por_evento[5]["ok"] else 0
    d6 = 10 if por_evento[6]["ok"] else 0
    score += _check(checks, "deleção propagada (revogação e LGPD)", d5 + d6 == 20, d5 + d6, 20, por_evento[6]["detalhe"])

    limite = g["embeds_esperados"] * (1 + g["tolerancia_pct"] / 100)
    pontos = 20 if embeds <= limite else 10 if embeds <= 2 * g["embeds_esperados"] else 0
    score += _check(checks, "custo (embeddings no ciclo)", pontos == 20, pontos, 20,
                    f"executados = {embeds}, mínimo possível = {g['embeds_esperados']}")

    fresco = por_evento[4]["ok"] and cache.itens_do_topico("tarifa") == 0 and "invalidar_cache" in eventos_do_outbox
    score += _check(checks, "freshness (cache invalidado no ciclo)", fresco, 20 if fresco else 0, 20,
                    f"itens de tarifa no cache = {cache.itens_do_topico('tarifa')}")

    vazou = memoria.quantas(g["cliente_lgpd"]) > 0
    if vazou:
        score = min(score, 40)
        _check(checks, "REPROVAÇÃO: memória da Marina sobreviveu ao pedido LGPD", False, 0, 0, "score travado em 40")

    resultado = {"missao": "M2", "score": round(score, 1), "checks": checks,
                 "por_evento": por_evento, "embeds_totais": embeds, "duracao_s": round(time.time() - t0, 1)}
    _imprimir("MISSÃO 2 · DUTO INCREMENTAL", resultado)
    return resultado


# --------------------------------------------------------------------------- Auditor
EVIDENCIAS_BASE = {
    "linhas_lidas": 2243, "linhas_rejeitadas": 14, "taxa_rejeicao_pct": 0.62,
    "quarentena_linhas": 14, "quarentena_arquivos_inteiros": 0, "docs_vigentes": 21,
    "docs_nao_autoritativos_vigentes": 0, "chunks_sem_embedding": 0,
    "lgpd_pedidos_recebidos": 1, "lgpd_pedidos_executados": 1,
    "transacoes_C0007": 0, "memorias_C0007": 0, "outbox_pendentes": 0,
    "indicador_ultima_data": "2026-09-16", "indicador_idade_dias": 2,
}

CENARIOS_AUDITOR = [
    ("fundação limpa", {}, "PASS", []),
    ("Marina viva", {"lgpd_pedidos_executados": 0, "transacoes_C0007": 3, "memorias_C0007": 2},
     "FAIL", ["transacoes_C0007", "memorias_C0007", "lgpd_pedidos_executados"]),
    ("dado velho", {"indicador_ultima_data": "2026-08-20", "indicador_idade_dias": 27},
     "FAIL", ["indicador_idade_dias"]),
    ("índice contaminado", {"docs_nao_autoritativos_vigentes": 1, "taxa_rejeicao_pct": 9.4, "quarentena_arquivos_inteiros": 2},
     "FAIL", ["docs_nao_autoritativos_vigentes", "taxa_rejeicao_pct"]),
]


MOCK_AUDITOR = {
    "fundação limpa": '{"decisao": "PASS", "violacoes": [], "justificativa": "Regras satisfeitas."}',
    "Marina viva": '{"decisao": "FAIL", "violacoes": ['
                   '{"regra": "4", "evidencia": "memorias_C0007=2", "gravidade": "alta"},'
                   '{"regra": "4", "evidencia": "transacoes_C0007=3", "gravidade": "alta"},'
                   '{"regra": "4", "evidencia": "lgpd_pedidos_executados=0", "gravidade": "alta"},'
                   '{"regra": "3", "evidencia": "chunks_sem_embedding=7", "gravidade": "media"}],'
                   '"justificativa": "Pedido LGPD nao executado."}',
    "dado velho": '{"decisao": "FAIL", "violacoes": ['
                  '{"regra": "5", "evidencia": "indicador_idade_dias=27", "gravidade": "media"}],'
                  '"justificativa": "Indicador com 27 dias."}',
    "índice contaminado": '{"decisao": "FAIL", "violacoes": ['
                          '{"regra": "2", "evidencia": "docs_nao_autoritativos_vigentes=1", "gravidade": "alta"},'
                          '{"regra": "1", "evidencia": "taxa_rejeicao_pct=9.4", "gravidade": "media"}],'
                          '"justificativa": "Indice contaminado e rejeicao alta."}',
}


def avaliar_auditor(regras: str) -> dict:
    """Quatro cenários com evidências controladas. O Auditor precisa acertar a decisão E apontar
    violações que existem de fato. Uma violação inventada não conta a favor nem contra."""
    import agentes
    checks: list = []
    score = 0.0
    por_cenario = {}

    for nome, delta, esperado, campos in CENARIOS_AUDITOR:
        if agentes._backend() == "mock":
            agentes.MOCK["auditor"] = MOCK_AUDITOR[nome]
        evidencias = {**EVIDENCIAS_BASE, **delta}
        v = agentes.julgar(regras, evidencias)
        decisao_ok = v["decisao"] == esperado
        apontados = {str(x.get("evidencia", "")).split("=")[0].strip() for x in v["violacoes"]}
        cobertura = len(set(campos) & apontados) / len(campos) if campos else (1.0 if not v["violacoes"] else 0.0)
        pontos = (15 if decisao_ok else 0) + round(10 * cobertura, 1)
        score += pontos
        por_cenario[nome] = {"decisao": v["decisao"], "esperado": esperado, "apontados": sorted(apontados),
                             "descartadas": len(v.get("violacoes_descartadas", []))}
        _check(checks, f"cenário: {nome}", decisao_ok and cobertura == 1.0, pontos, 25,
               f"decisão {v['decisao']} (esperado {esperado}), evidências {sorted(apontados)}, "
               f"alucinações descartadas {len(v.get('violacoes_descartadas', []))}")

    if agentes._backend() == "mock":
        agentes.MOCK.pop("auditor", None)   # não deixa a resposta do último cenário vazar para a próxima chamada
        print("\n  AVISO: backend mock. As respostas são canônicas e NÃO dependem das regras que você")
        print("  escreveu, então este score não mede o seu Auditor. Carregue o modelo para valer a nota.")
    resultado = {"missao": "M2-auditor", "score": round(score, 1), "checks": checks, "por_cenario": por_cenario}
    _imprimir("AGENT 2 · AUDITOR", resultado)
    return resultado


def salvar(resultado: dict, caminho: str = "resultados"):
    p = Path(caminho)
    p.mkdir(parents=True, exist_ok=True)
    arquivo = p / f"resultado_{resultado['missao'].lower()}.json"
    resultado = {**resultado, "medalha": medalha(resultado["score"]), "gerado_em": time.strftime("%Y-%m-%d %H:%M:%S")}
    arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return str(arquivo)


# --------------------------------------------------------------------------- entrega
def gerar_entrega(esquadrao: str, bloco: int, caminho_kit, resultados: dict,
                  decisoes: dict, contratos_texto: dict | None = None,
                  system_message: str | None = None, regras_auditor: str | None = None) -> str:
    """Monta o arquivo de entrega do esquadrão. O score vem do harness, não do que o time digitou."""
    from pathlib import Path

    import agentes
    from contrato import pendencias

    raiz = Path(caminho_kit)
    if contratos_texto is None:
        contratos_texto = {p.stem: p.read_text(encoding="utf-8")
                           for p in sorted((raiz / "contratos").glob("*.yaml"))}

    faltando = pendencias()
    entrega = {
        "esquadrao": esquadrao,
        "bloco": bloco,
        "gerado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scores": {k: {"score": v.get("score"), "medalha": medalha(v.get("score", 0)),
                       "total_com_caos": v.get("score_total"), "bonus_caos": v.get("bonus_caos"),
                       "checks": v.get("checks")}
                   for k, v in resultados.items()},
        "lacunas_do_contrato_ainda_abertas": faltando,
        "contratos": contratos_texto,
        "system_message": system_message,
        "regras_auditor": regras_auditor,
        "decisoes": decisoes,
        "backend_llm": agentes._backend(),
    }
    arquivo = raiz / f"entrega_{esquadrao}_bloco{bloco}.json"
    arquivo.write_text(json.dumps(entrega, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"Entrega gravada em {arquivo}")
    print(f"  esquadrão: {esquadrao} · bloco {bloco}")
    for nome, r in resultados.items():
        total = r.get("score_total", r.get("score"))
        print(f"  {nome}: {r.get('score')} pontos ({medalha(r.get('score', 0))})"
              + (f", total com Caos {total}" if r.get("score_total") is not None else ""))
    if faltando:
        print(f"  ATENÇÃO: {len(faltando)} lacuna(s) do contrato ainda em TODO")
    respondidas = sum(1 for v in decisoes.values() if str(v).strip() and "escreva aqui" not in str(v).lower())
    print(f"  perguntas respondidas: {respondidas} de {len(decisoes)}")
    if respondidas < len(decisoes):
        print("  ATENÇÃO: falta responder. Preencha e rode esta célula de novo.")
    print("\nAgora faça: Arquivo > Fazer download > Fazer download do .ipynb")
    print("e entregue os DOIS arquivos.")
    return str(arquivo)
