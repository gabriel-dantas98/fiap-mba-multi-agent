"""agentes.py — Agent 1 (Construtor) e Agent 2 (Auditor), mais o cliente de LLM que os dois usam.

O desenho da aula: o esquadrão não escreve o pipeline. Escreve o CONTRATO e a SYSTEM MESSAGE, e o
Construtor escreve o código. Depois escreve as REGRAS, e o Auditor decide se os dutos podem conectar
ao Q. O que o harness avalia são as tabelas e a decisão, nunca o texto que o LLM produziu.

Backends, nesta ordem: hf (modelo embutido no notebook, CPU) · openai (endpoint compatível) · mock.
Sem API paga, sem serviço externo obrigatório.
"""
from __future__ import annotations

import ast
import json
import os
import re
import textwrap
import time

# =========================================================================== LLM
BACKEND = os.environ.get("LLM_BACKEND", "auto")
MODELO_HF = os.environ.get("LLM_MODELO_HF", "Qwen/Qwen2.5-Coder-1.5B-Instruct")
URL = os.environ.get("LLM_URL", "http://localhost:11434/v1").rstrip("/")
MODELO = os.environ.get("LLM_MODELO", "")
MOCK: dict[str, str] = {}
_hf = None

# Respostas canônicas do backend mock: o que um modelo que entendeu o pedido responderia.
# Servem para o professor validar o kit sem esperar geração, e para o harness não depender do LLM.
MOCK_PADRAO = {
    "lacuna:___ORDEM_DAS_FONTES___":
        'sorted(contratos, key=lambda f: {"clientes": 0, "tarifas": 1, "transacoes": 2, "documentos": 3}.get(f, 9))',
    "lacuna:___REFERENCIAS_PARA_FK___":
        '{"clientes": (ref if ref is not None else fundacao.referencia_clientes(lake))} if fonte == "transacoes" else {}',
    "lacuna:___O_QUE_FAZER_COM_O_ARQUIVO_INVALIDO___":
        'fundacao.gravar_quarentena(lake, fonte, r["nome"], None, str(e))\n'
        'fundacao.marcar_processado(lake, r["path"], fonte, "quarentena", 0, 1)\n'
        'm["drift"] += 1\nm["rows_rejected"] += 1',
    "auditor": '{"decisao": "PASS", "violacoes": [], "justificativa": "Regras satisfeitas pelas evidências."}',
}


def _backend() -> str:
    atual = os.environ.get("LLM_BACKEND", BACKEND)
    if atual != "auto":
        return atual
    try:
        import requests
        if requests.get(f"{URL}/models", timeout=2).status_code == 200:
            return "openai"
    except Exception:
        pass
    return "mock"


def carregar_modelo(nome: str | None = None, quantizar: bool = False):
    """Carrega o modelo de código no notebook. Em CPU o 1.5B ocupa ~3 GB e leva ~1 min para baixar.

    Com LLM_BACKEND=mock não carrega nada e usa as respostas canônicas: é como o professor roda
    o kit inteiro em D-1 sem esperar por geração, e como o harness roda sem depender do modelo.
    """
    global _hf, MODELO_HF, BACKEND
    if os.environ.get("LLM_BACKEND") == "mock":
        MOCK.update(MOCK_PADRAO)
        return {"modelo": "mock", "aviso": "backend mock: respostas canônicas, nenhum modelo carregado"}
    MODELO_HF = nome or MODELO_HF
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(MODELO_HF)
    # bfloat16 mesmo em CPU: o 1.5B ocupa ~3 GB em vez de ~6 GB. Em float32 a sessão do Colab
    # fica sem margem e morre no meio da prática, que é o pior momento possível.
    mdl = AutoModelForCausalLM.from_pretrained(MODELO_HF, low_cpu_mem_usage=True, dtype=torch.bfloat16)
    if torch.cuda.is_available():
        mdl = mdl.to("cuda")
    mdl.eval()
    _hf = (tok, mdl)
    BACKEND = "hf"
    os.environ["LLM_BACKEND"] = "hf"
    import gc; gc.collect()
    memoria_gb = sum(p.numel() * p.element_size() for p in mdl.parameters()) / 1e9
    return {"modelo": MODELO_HF, "dispositivo": str(mdl.device), "memoria_gb": round(memoria_gb, 2),
            "segundos_carga": round(time.time() - t0, 1)}


def _chat_hf(mensagens, max_tokens, temperatura):
    import torch
    if _hf is None:
        carregar_modelo()
    tok, mdl = _hf
    texto = tok.apply_chat_template(mensagens, add_generation_prompt=True, tokenize=False)
    entrada = tok(texto, return_tensors="pt").to(mdl.device)
    with torch.no_grad():
        saida = mdl.generate(**entrada, max_new_tokens=max_tokens, do_sample=temperatura > 0,
                             temperature=temperatura or None, pad_token_id=tok.eos_token_id)
    return tok.decode(saida[0][entrada["input_ids"].shape[-1]:], skip_special_tokens=True)


def chat(mensagens, max_tokens: int = 400, temperatura: float = 0.0, tag: str | None = None) -> str:
    b = _backend()
    if b == "mock":
        return MOCK.get(tag) or MOCK_PADRAO.get(tag) or MOCK.get("*", "")
    if b == "hf":
        return _chat_hf(mensagens, max_tokens, temperatura)
    import requests
    corpo = {"model": MODELO or "local", "messages": mensagens,
             "temperature": temperatura, "max_tokens": max_tokens, "stream": False}
    r = requests.post(f"{URL}/chat/completions", json=corpo, timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def completar(prompt: str, sistema: str | None = None, **kw) -> str:
    msgs = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": prompt}]
    return chat(msgs, **kw)


def _so_codigo(texto: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", texto, re.S)
    return (m.group(1) if m else texto).strip()


def _so_json(texto: str) -> dict:
    t = re.sub(r"```(?:json)?", "", texto.strip())
    i, j = t.find("{"), t.rfind("}")
    return json.loads(t[i:j + 1]) if i >= 0 else {}


# =========================================================================== Agent 1 · CONSTRUTOR
FUNDACAO_DOC = """
Funções disponíveis (módulo `fundacao`, já importado):
  fundacao.arquivos_pendentes(lake, padrao_glob) -> lista de dicts {path, nome, conteudo}
  fundacao.ler(nome, conteudo, contrato) -> (DataFrame pandas, correcoes)      # ValueError = arquivo inválido
  fundacao.aplicar_contrato(df, contrato, referencias) -> (ok, quarentena, n_correcoes)
  fundacao.referencia_clientes(lake) -> set de cliente_id já na Silver
  fundacao.gravar_silver(lake, fonte, ok, chave, arquivo)
  fundacao.gravar_quarentena(lake, fonte, arquivo, quarentena, motivo_arquivo=None)
  fundacao.marcar_processado(lake, path, fonte, status, ok, q)
  fundacao.finalizar_documentos(lake, contrato_documentos)
Regras: use só estas funções e pandas. Nunca crie ou apague tabelas. Nunca escreva fora da Silver.
"""

ESQUELETO = '''
import fundacao

def pipeline(lake, contrato: dict) -> dict:
    contratos = contrato["fontes"]
    m = {"rows_in": 0, "rows_ok": 0, "rows_rejected": 0, "arquivos": 0, "corrigidos": 0, "drift": 0}
    ref = None
    for fonte in ___ORDEM_DAS_FONTES___:
        c = contratos[fonte]
        for r in fundacao.arquivos_pendentes(lake, c["padrao_arquivo"]):
            m["arquivos"] += 1
            try:
                df, correcoes = fundacao.ler(r["nome"], r["conteudo"], c)
                refs = ___REFERENCIAS_PARA_FK___
                ok, q, n_corr = fundacao.aplicar_contrato(df, c, refs)
                fundacao.gravar_silver(lake, fonte, ok, c["chave"], r["nome"])
                fundacao.gravar_quarentena(lake, fonte, r["nome"], q)
                fundacao.marcar_processado(lake, r["path"], fonte, "ok", len(ok), len(q))
                if fonte == "clientes" and ref is not None:
                    ref |= set(ok["cliente_id"])
                m["rows_in"] += len(df); m["rows_ok"] += len(ok)
                m["rows_rejected"] += len(q); m["corrigidos"] += n_corr + len(correcoes)
            except (ValueError, UnicodeDecodeError, KeyError) as e:
                ___O_QUE_FAZER_COM_O_ARQUIVO_INVALIDO___
    if "documentos" in contratos:
        fundacao.finalizar_documentos(lake, contratos["documentos"])
    return m
'''

LACUNAS = {
    "___ORDEM_DAS_FONTES___": (
        "UMA expressão Python (sem `=`, sem `for`) que devolve a lista das quatro fontes na ordem de "
        "processamento. As quatro fontes são exatamente: clientes, tarifas, transacoes, documentos. "
        "TODAS as quatro precisam aparecer no dicionário de ordem. A fonte transacoes tem chave estrangeira "
        "para clientes, então clientes precisa receber o MENOR número e ser processada primeiro; transacoes "
        "precisa vir depois de clientes.\n"
        "Formato da resposta (preencha os números): "
        "sorted(contratos, key=lambda f: {\"clientes\": ?, \"tarifas\": ?, \"transacoes\": ?, \"documentos\": ?}.get(f, 9))"
    ),
    "___REFERENCIAS_PARA_FK___": (
        "UMA expressão Python que avalia para um DICIONÁRIO. Não use `=`, não use atribuição, não crie variável. "
        "Quando a fonte for transacoes, o dicionário precisa ser {\"clientes\": <conjunto de ids>}, onde o conjunto "
        "vem de fundacao.referencia_clientes(lake) (ou de `ref`, se já estiver preenchido). Para qualquer outra "
        "fonte, o dicionário precisa ser vazio: {}.\n"
        "Formato da resposta: {\"clientes\": (ref if ref is not None else fundacao.referencia_clientes(lake))} "
        "if fonte == \"transacoes\" else {}"
    ),
    "___O_QUE_FAZER_COM_O_ARQUIVO_INVALIDO___": (
        "Linhas Python para o bloco except. ATENÇÃO: as variáveis `ok`, `q` e `df` NÃO existem aqui, porque a "
        "leitura falhou antes de criá-las. Use apenas `e`, `r`, `fonte`, `lake` e `m`. São exatamente quatro linhas: "
        "manda o arquivo inteiro para a quarentena com o motivo str(e); marca o arquivo como processado com status "
        "\"quarentena\" e zero linhas em ambos os contadores; soma 1 em m[\"drift\"]; soma 1 em m[\"rows_rejected\"].\n"
        "Formato da resposta:\n"
        "fundacao.gravar_quarentena(lake, fonte, r[\"nome\"], None, str(e))\n"
        "fundacao.marcar_processado(lake, r[\"path\"], fonte, \"quarentena\", 0, 0)\n"
        "m[\"drift\"] += 1\n"
        "m[\"rows_rejected\"] += 1"
    ),
}

SISTEMA_LACUNA = (
    "Você completa uma lacuna de um esqueleto Python. Responda SOMENTE com o código que substitui a lacuna. "
    "Sem explicação, sem ```, sem repetir o esqueleto, sem def, sem import."
)

IMPORTS_PERMITIDOS = {"pandas", "json", "re", "datetime", "math", "fundacao"}
PROIBIDOS = ("os.system", "subprocess", "exec(", "eval(", "__import__", "shutil", "open(", "DROP ", "TRUNCATE")


def gerar(contrato_yaml: str, system_message: str, modelo=None, verboso: bool = True) -> dict:
    """Geração por lacunas: esqueleto fixo, uma pergunta estreita por lacuna.

    Pedir o módulo inteiro a um modelo de 1.5B produz código que quase compila. Pedir três decisões
    específicas produz três decisões. O esqueleto é o guardrail mais barato que existe.
    """
    t0 = time.time()
    codigo = ESQUELETO
    respostas, tempos = {}, {}
    contexto = (f"CONTRATO (resumo):\n{contrato_yaml[:2000]}\n\n{FUNDACAO_DOC}\n"
                f"\nINSTRUÇÕES DO ESQUADRÃO:\n{system_message}\n\nESQUELETO:\n{ESQUELETO}")

    for lacuna, pedido in LACUNAS.items():
        t1 = time.time()
        msgs = [{"role": "system", "content": SISTEMA_LACUNA},
                {"role": "user", "content": f"{contexto}\n\nLacuna: {lacuna}\nO que vai nela: {pedido}\n\nResponda só o código."}]
        bruto = chat(msgs, max_tokens=220, tag=f"lacuna:{lacuna}").strip()
        resposta = _so_codigo(bruto) if "```" in bruto else bruto
        resposta = resposta.strip().strip("`").strip()
        respostas[lacuna] = resposta
        tempos[lacuna] = round(time.time() - t1, 1)
        linha = next(l for l in codigo.splitlines() if lacuna in l)
        indent = linha[: len(linha) - len(linha.lstrip())]
        bloco = ("\n".join((indent + l.strip()) if i else l.strip()
                           for i, l in enumerate(resposta.splitlines()))) if "\n" in resposta else resposta
        codigo = codigo.replace(lacuna, bloco, 1)
        if verboso:
            print(f"  {lacuna:<40} {tempos[lacuna]:>6.1f}s  {resposta.splitlines()[0][:70] if resposta else '(vazio)'}")

    return {"codigo": codigo, "respostas": respostas, "tempos": tempos,
            "segundos": round(time.time() - t0, 1), "backend": _backend()}


def validar(codigo: str) -> list[str]:
    """Guardrails estáticos: lacuna não preenchida, sintaxe, import fora da lista, comando destrutivo,
    e a função `pipeline` existir. Nenhum deles olha se o código está CERTO: isso é com o harness."""
    problemas = []
    if "___" in codigo:
        problemas.append("lacunas do esqueleto não preenchidas")
    for p in PROIBIDOS:
        if p in codigo:
            problemas.append(f"trecho proibido: {p.strip()}")
    try:
        arvore = ast.parse(codigo)
    except SyntaxError as e:
        return problemas + [f"erro de sintaxe na linha {e.lineno}: {e.msg}"]
    for n in ast.walk(arvore):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name.split(".")[0] for a in n.names] if isinstance(n, ast.Import) else [(n.module or "").split(".")[0]]
            problemas += [f"import não permitido: {m}" for m in mods if m not in IMPORTS_PERMITIDOS]
    if not any(isinstance(n, ast.FunctionDef) and n.name == "pipeline" for n in arvore.body):
        problemas.append("função pipeline(lake, contrato) ausente")
    return problemas


def executar(codigo: str, lake, contrato: dict) -> dict:
    """Executa o módulo gerado num namespace controlado."""
    import fundacao
    ns = {"fundacao": fundacao}
    exec(compile(codigo, "<construtor>", "exec"), ns)
    t0 = time.time()
    m = ns["pipeline"](lake, contrato) or {}
    m["duracao_s"] = round(time.time() - t0, 1)
    return m


def codigo_de_referencia() -> str:
    """Plano B do esquadrão travado: o módulo que o Construtor deveria ter produzido."""
    from pathlib import Path
    return (Path(__file__).resolve().parent / "referencia.py").read_text(encoding="utf-8")


# =========================================================================== Agent 2 · AUDITOR
SISTEMA_AUDITOR = """Você é o Auditor de dados de uma fintech. Recebe REGRAS escritas pelo time e EVIDÊNCIAS numéricas
coletadas do lakehouse. Decida PASS ou FAIL aplicando as regras às evidências. Responda SOMENTE JSON:
{"decisao": "PASS"|"FAIL", "violacoes": [{"regra": "...", "evidencia": "<campo>=<valor>", "gravidade": "alta"|"media"}], "justificativa": "1-3 frases"}
Nunca invente números: só cite valores presentes nas evidências. Regras satisfeitas: violacoes = [] e PASS."""

# As regras que o esquadrão RECEBE. Elas aprovam uma fundação com a Marina viva no sistema e com o
# indicador de mercado parado há 27 dias. Estão frouxas de propósito: endurecê-las é a missão.
REGRAS_INICIAIS = """1. A taxa de rejeição não pode passar de 50% (taxa_rejeicao_pct).
2. O índice precisa ter pelo menos um documento vigente (docs_vigentes).
3. Os dutos precisam ter rodado pelo menos uma vez."""

# O gabarito do professor. Não aparece no notebook do aluno.
REGRAS_EXEMPLO = """1. Taxa de rejeição total abaixo de 5% (taxa_rejeicao_pct).
2. Nenhum documento não autoritativo vigente no índice (docs_nao_autoritativos_vigentes = 0).
3. Nenhum chunk sem embedding (chunks_sem_embedding = 0).
4. Todo pedido LGPD executado: lgpd_pedidos_executados >= lgpd_pedidos_recebidos, e a cliente C0007 sem transações nem memórias.
5. Indicador de mercado com no máximo 4 dias de idade (indicador_idade_dias).
6. Outbox sem eventos pendentes (outbox_pendentes = 0)."""


def coletar_evidencias(lake, memoria=None, cliente_lgpd: str = "C0007") -> dict:
    """Evidências determinísticas. O LLM julga; ele não mede. Esta separação é o que torna
    o Auditor auditável: as mesmas evidências produzem a mesma decisão."""
    import datetime as dt

    def n(consulta, padrao=0):
        try:
            v = lake.escalar(consulta)
            return padrao if v is None else int(v)
        except Exception:
            return padrao

    ev = {"coletado_em": dt.datetime.now().isoformat(timespec="seconds")}
    execucoes = lake.sql("""SELECT duto, COUNT(*) n, SUM(rows_in) rows_in, SUM(rows_rejected) rej,
                                   SUM(embeds_executados) embeds, MAX(iniciado_em) ultima
                            FROM gold.execucoes GROUP BY duto""") if lake.existe("gold.execucoes") else None
    total_in = total_rej = 0
    if execucoes is not None:
        for r in execucoes.to_dict("records"):
            d = r["duto"]
            ev[f"exec_{d}_n"] = int(r["n"])
            ev[f"exec_{d}_embeds"] = int(r["embeds"] or 0)
            total_in += int(r["rows_in"] or 0)
            total_rej += int(r["rej"] or 0)
    ev["linhas_lidas"] = total_in
    ev["linhas_rejeitadas"] = total_rej
    ev["taxa_rejeicao_pct"] = round(100 * total_rej / total_in, 2) if total_in else 0.0
    ev["quarentena_linhas"] = n("SELECT COUNT(*) FROM silver.quarentena")
    ev["quarentena_arquivos_inteiros"] = n("SELECT COUNT(*) FROM silver.quarentena WHERE chave = '*arquivo*'")
    ev["docs_vigentes"] = n("SELECT COUNT(DISTINCT doc_id) FROM silver.documentos WHERE vigente")
    ev["docs_nao_autoritativos_vigentes"] = n(
        "SELECT COUNT(*) FROM gold.chunks WHERE vigente AND autoritativo AND tipo IN ('marketing','rascunho','faq-antigo')")
    ev["chunks_sem_embedding"] = n("SELECT COUNT(*) FROM gold.chunks WHERE embedding IS NULL")
    ev["lgpd_pedidos_recebidos"] = n("SELECT COUNT(*) FROM fonte.lgpd_eliminacoes")
    ev["lgpd_pedidos_executados"] = n("SELECT COUNT(*) FROM gold.eliminacoes_lgpd")
    ev[f"transacoes_{cliente_lgpd}"] = n(f"SELECT COUNT(*) FROM silver.transacoes WHERE cliente_id = '{cliente_lgpd}'")
    ev[f"memorias_{cliente_lgpd}"] = int(memoria.quantas(cliente_lgpd)) if memoria is not None else -1
    ev["outbox_pendentes"] = n("SELECT COUNT(*) FROM gold.eventos_agente WHERE NOT consumido")
    ultima = None
    try:
        import pandas as pd
        bruto = lake.escalar("SELECT MAX(data) FROM gold.indicadores")
        ultima = pd.to_datetime(bruto).date() if bruto is not None else None
    except Exception:
        pass
    ev["indicador_ultima_data"] = str(ultima) if ultima is not None else None
    ev["indicador_idade_dias"] = (dt.date.today() - ultima).days if ultima is not None else None
    return ev


def julgar(regras: str, evidencias: dict, modelo=None) -> dict:
    """LLM-as-a-judge com filtro anti-alucinação: uma violação só vale se apontar um campo que existe
    nas evidências, com o valor que está lá. Violação inventada é descartada, não vira FAIL."""
    prompt = f"REGRAS DO TIME:\n{regras}\n\nEVIDÊNCIAS:\n{json.dumps(evidencias, ensure_ascii=False, indent=1)}"
    bruto = completar(prompt, SISTEMA_AUDITOR, max_tokens=600, tag="auditor")
    try:
        v = _so_json(bruto)
    except Exception:
        v = {"decisao": "FAIL", "violacoes": [], "justificativa": f"o auditor não devolveu JSON: {bruto[:200]}"}

    validas, descartadas = [], []
    for viol in v.get("violacoes", []):
        e = str(viol.get("evidencia", ""))
        campo = e.split("=")[0].strip()
        if campo in evidencias and str(evidencias[campo]) in e.replace(" ", ""):
            validas.append(viol)
        else:
            descartadas.append(viol)
    v["violacoes"], v["violacoes_descartadas"] = validas, descartadas
    v["decisao"] = "FAIL" if validas else v.get("decisao", "FAIL")
    v["bruto"] = bruto[:1200]
    return v


def liberar(lake, veredito: dict) -> str:
    """A catraca. O Q só responde quando o último status é PASS."""
    import pandas as pd
    from lake import agora
    lake.criar("gold.liberacao")
    lake.acrescentar("gold.liberacao", pd.DataFrame([{
        "status": veredito.get("decisao", "FAIL"),
        "violacoes": json.dumps(veredito.get("violacoes", []), ensure_ascii=False),
        "justificativa": str(veredito.get("justificativa", ""))[:900],
        "hora": agora(),
    }]))
    return veredito.get("decisao", "FAIL")


def status_liberacao(lake) -> str:
    try:
        v = lake.escalar("SELECT status FROM gold.liberacao ORDER BY hora DESC LIMIT 1")
        return v or "SEM_AUDITORIA"
    except Exception:
        return "SEM_AUDITORIA"


# =========================================================================== teste de fumaça
SINTOMAS = {
    "ordem": ("A ordem das fontes está errada: clientes precisa ser processada ANTES de transacoes, "
              "senão toda transação vira órfã na validação da chave estrangeira."),
    "fk": ("As referências da chave estrangeira não chegaram como dicionário {\"clientes\": conjunto} "
           "na fonte transacoes."),
    "except": ("O bloco except usa variáveis que não existem quando a leitura falha (ok, q ou df)."),
}


def testar(codigo: str, contratos: dict, pasta_kit) -> dict:
    """Roda o código gerado contra um lakehouse descartável e diz, em português, o que saiu errado.

    Existe porque os guardrails estáticos não pegam erro de lógica: o código do 1.5B compila, executa
    e rejeita 2.017 linhas em vez de 14. Este teste é o que transforma esse silêncio em feedback.
    """
    import shutil
    import tempfile
    from pathlib import Path

    import dutos
    from lake import Lake

    temporario = Path(tempfile.mkdtemp(prefix="fumaca_"))
    try:
        inbox = temporario / "inbox"
        shutil.copytree(Path(pasta_kit) / "dados" / "inbox", inbox)
        lake = Lake(str(temporario / "lake")).criar_todas()
        dutos.bronze(lake, inbox)
        try:
            m = executar(codigo, lake, {"fontes": contratos})
        except Exception as e:
            return {"ok": False, "erro": f"{type(e).__name__}: {str(e)[:200]}",
                    "sintomas": [SINTOMAS["except"]] if "not defined" in str(e) else []}

        problemas = []
        if m.get("rows_rejected", 0) > 200:
            problemas.append(SINTOMAS["ordem"])
        if lake.contar("silver.transacoes") == 0 and m.get("rows_in", 0) > 0:
            problemas.append(SINTOMAS["fk"])
        esperado = {"rows_in": 2243, "rows_rejected": 14}
        bate = all(m.get(k) == v for k, v in esperado.items())
        return {"ok": bate and not problemas, "metricas": m, "sintomas": problemas,
                "esperado": esperado,
                "contagens": {"clientes": lake.contar("silver.clientes"),
                              "transacoes": lake.contar("silver.transacoes")}}
    finally:
        shutil.rmtree(temporario, ignore_errors=True)


def construir(contrato_yaml: str, system_message: str, contratos: dict, pasta_kit,
              tentativas: int = 2, verboso: bool = True) -> dict:
    """gerar → guardrails → teste de fumaça → e, se falhar, gera de novo com o diagnóstico em mãos.

    Uma tentativa sem feedback é um sorteio. Uma tentativa com o erro concreto na entrada é engenharia.
    """
    historico = []
    instrucao = system_message
    for n in range(1, tentativas + 1):
        if verboso:
            print(f"\n--- tentativa {n} de {tentativas} ---")
        g = gerar(contrato_yaml, instrucao, verboso=verboso)
        problemas = validar(g["codigo"])
        if problemas:
            historico.append({"tentativa": n, "etapa": "guardrails", "problemas": problemas})
            if verboso:
                print("  guardrails reprovaram:", problemas)
            instrucao = system_message + "\n\nA tentativa anterior falhou nos guardrails: " + "; ".join(problemas)
            continue
        fumaca = testar(g["codigo"], contratos, pasta_kit)
        if fumaca["ok"]:
            if verboso:
                print("  teste de fumaça: passou", fumaca.get("metricas"))
            return {"ok": True, "codigo": g["codigo"], "tentativas": n, "historico": historico,
                    "fumaca": fumaca, "segundos": g["segundos"]}
        historico.append({"tentativa": n, "etapa": "fumaça", "diagnostico": fumaca})
        if verboso:
            print("  teste de fumaça: reprovou.", fumaca.get("erro") or fumaca.get("metricas"))
            for s in fumaca["sintomas"]:
                print("   ·", s)
        diagnostico = fumaca.get("erro") or (
            f"o pipeline rejeitou {fumaca['metricas'].get('rows_rejected')} linhas "
            f"em vez de 14, e gravou {fumaca['contagens']['transacoes']} transações")
        instrucao = (system_message + f"\n\nA tentativa anterior rodou mas deu errado: {diagnostico}. "
                     + " ".join(fumaca["sintomas"]))
    return {"ok": False, "codigo": g["codigo"], "tentativas": tentativas, "historico": historico,
            "fumaca": fumaca}
