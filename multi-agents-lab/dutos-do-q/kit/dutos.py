"""dutos.py — os dutos da Quantum: Bronze, Gold, incremental (CDF), externo (BCB) e a fonte mutável.

Cada função é um duto e devolve métricas. Todas aceitam modo="referencia" (o jeito que sobrevive ao Caos)
ou modo="ingenuo" (o jeito que parece funcionar até a segunda execução). A Silver não está aqui de
propósito: quem escreve a Silver é o Agent 1 Construtor, compondo `fundacao`.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pandas as pd

import embeddings
import fundacao
from chunking import chunks_do_documento
from contrato import carregar_contratos
from lake import Lake, agora, hash_texto


# =========================================================================== 10 · BRONZE
def bronze(lake: Lake, pasta_inbox: str, modo: str = "referencia") -> dict:
    """Cada arquivo que chega vira UMA linha em bronze.arquivos, com o conteúdo bruto preservado.

    Referência: MERGE por path + hash do conteúdo, então reprocessar a pasta não duplica nada.
    Ingênuo:    APPEND de tudo o que está na pasta, toda vez.
    No Databricks este duto é o Auto Loader (`cloudFiles`) com checkpoint; a garantia é a mesma
    (cada arquivo entra uma vez), o mecanismo é que muda.
    """
    t0 = time.time()
    lake.criar("bronze.arquivos")
    raiz = Path(pasta_inbox)
    linhas = []
    for p in sorted(raiz.rglob("*")):
        if not p.is_file() or p.suffix not in (".md", ".csv", ".parquet", ".json"):
            continue
        conteudo = p.read_bytes()
        linhas.append({
            "path": str(p), "nome": str(p.relative_to(raiz)), "tamanho": len(conteudo),
            "conteudo": conteudo, "hash_arquivo": hash_texto(str(len(conteudo)) + p.name),
            "ingerido_em": agora(),
        })
    antes = lake.contar("bronze.arquivos")
    df = pd.DataFrame(linhas)
    if modo == "ingenuo":
        lake.acrescentar("bronze.arquivos", df)
    elif len(df):
        lake.mesclar("bronze.arquivos", df, ["path"], quando_hash_mudar=False)
    depois = lake.contar("bronze.arquivos")
    m = {"novos_arquivos": depois - antes, "total": depois, "arquivos_na_pasta": len(linhas)}
    lake.registrar_execucao("bronze", modo, {"duracao_s": time.time() - t0,
                                             "rows_in": len(linhas), "rows_ok": depois - antes, **m})
    return m


# =========================================================================== 12 · GOLD
def _chunks_desejados(lake: Lake, filtro_doc_ids=None) -> pd.DataFrame:
    docs = lake.ler("silver.documentos")
    if filtro_doc_ids is not None:
        docs = docs[docs["doc_id"].isin(list(filtro_doc_ids))]
    linhas = []
    for d in docs.to_dict("records"):
        for c in chunks_do_documento(d["doc_id"], int(d["versao"]), d["titulo"], d["conteudo"]):
            linhas.append({**c, "titulo": d["titulo"], "area": d["area"], "tipo": d["tipo"], "data": d["data"],
                           "vigente": bool(d["vigente"]) if d["vigente"] is not None else True,
                           "autoritativo": bool(d["autoritativo"]) if d["autoritativo"] is not None else True})
    return pd.DataFrame(linhas)


def gold(lake: Lake, modo: str = "referencia", filtro_doc_ids=None) -> dict:
    """gold.chunks: o que o agente lê. Texto, embedding e os metadados de vigência e autoridade.

    Referência: embeda só o chunk novo ou cujo TEXTO mudou. Mudança de metadado (área, vigência)
                atualiza a linha sem tocar no vetor, porque o vetor não depende do metadado.
    Ingênuo:    recria a tabela e re-embeda tudo, toda vez. Funciona, e a conta chega no fim do mês.
    """
    t0 = time.time()
    lake.criar("gold.chunks")
    desejados = _chunks_desejados(lake, filtro_doc_ids)

    if modo == "ingenuo":
        vetores = embeddings.embed(desejados["texto"].tolist()) if len(desejados) else []
        if len(desejados):
            desejados = desejados.copy()
            desejados["embedding"] = vetores
            desejados["atualizado_em"] = agora()
        lake.sobrescrever("gold.chunks", desejados)
        m = {"embeds_executados": len(desejados), "embeds_evitados": 0, "chunks": len(desejados)}
        lake.registrar_execucao("gold", modo, {"duracao_s": time.time() - t0, "rows_in": len(desejados), **m})
        return m

    existentes = lake.ler("gold.chunks")
    hash_atual = dict(zip(existentes["chunk_id"], existentes["hash"])) if len(existentes) else {}
    vetor_atual = dict(zip(existentes["chunk_id"], existentes["embedding"])) if len(existentes) else {}

    precisam = [i for i, r in desejados.iterrows() if hash_atual.get(r["chunk_id"]) != r["hash"]] if len(desejados) else []
    novos_vetores = embeddings.embed([desejados.loc[i, "texto"] for i in precisam])
    mapa = dict(zip(precisam, novos_vetores))

    if len(desejados):
        desejados = desejados.copy()
        desejados["embedding"] = [mapa.get(i, vetor_atual.get(desejados.loc[i, "chunk_id"])) for i in desejados.index]
        desejados["atualizado_em"] = agora()

    escopo = "true" if filtro_doc_ids is None else \
        "alvo.doc_id IN ({})".format(", ".join(f"'{d}'" for d in filtro_doc_ids)) if filtro_doc_ids else None
    r = lake.mesclar("gold.chunks", desejados, ["chunk_id"], quando_hash_mudar=False,
                     apagar_ausentes=escopo) if escopo else {"apagadas": 0}
    m = {"embeds_executados": len(precisam), "embeds_evitados": len(desejados) - len(precisam),
         "chunks": len(desejados), "chunks_apagados": r.get("apagadas", 0)}
    lake.registrar_execucao("gold", modo, {"duracao_s": time.time() - t0, "rows_in": len(desejados), **m})
    return m


# =========================================================================== 21 · FONTE MUTÁVEL
def semear_fonte(lake: Lake, caminho_linha_do_tempo: str | None = None) -> dict:
    """Cria o "sistema de origem" da Quantum com CDF ligado, a partir do que já está na Silver."""
    lake.zerar("fonte.comunicados", "fonte.tarifas", "fonte.lgpd_eliminacoes",
               "gold.cursor_sync", "gold.eventos_agente", "gold.eliminacoes_lgpd")
    lake.criar_todas("fonte.comunicados", "fonte.tarifas", "fonte.lgpd_eliminacoes")

    docs = lake.ler("silver.documentos")
    comunicados = docs[(docs["tipo"] == "comunicado") & (docs["vigente"] == True)]  # noqa: E712
    if len(comunicados):
        c = comunicados[["doc_id", "titulo", "area", "tipo", "data", "versao", "conteudo"]].copy()
        c["updated_at"] = agora()
        lake.acrescentar("fonte.comunicados", c)

    lake.acrescentar("fonte.tarifas", pd.DataFrame([
        {"tipo": "saque", "valor": 7.50, "vigencia_inicio": "2026-01-10", "updated_at": agora()},
        {"tipo": "ted", "valor": 9.90, "vigencia_inicio": "2025-01-15", "updated_at": agora()},
        {"tipo": "manutencao", "valor": 0.00, "vigencia_inicio": "2025-01-15", "updated_at": agora()},
    ]))
    return {"comunicados": lake.contar("fonte.comunicados"), "tarifas": lake.contar("fonte.tarifas")}


def _sql_literal(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return repr(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"


def avancar_fonte(lake: Lake, evento: int, linha_do_tempo: list[dict]) -> dict:
    """Aplica um evento da linha do tempo na fonte. Cada evento existe para provocar uma decisão
    diferente no duto incremental: texto novo, só metadado, reenvio idêntico, revogação, LGPD."""
    ev = next(e for e in linha_do_tempo if e["evento"] == evento)
    tabela = f"fonte.{ev['tabela']}"
    op = ev["op"]

    if op == "insert":
        linha = {**ev["linha"], "updated_at": agora()}
        lake.acrescentar(tabela, pd.DataFrame([linha]))

    elif op == "update":
        where = " AND ".join(f"{k} = {_sql_literal(v)}" for k, v in ev["chave"].items())
        novos = {k: _sql_literal(v) for k, v in ev["set"].items()}
        novos["updated_at"] = f"TIMESTAMP '{agora()}'"
        lake.atualizar(tabela, where, novos)

    elif op == "delete":
        where = " AND ".join(f"{k} = {_sql_literal(v)}" for k, v in ev["chave"].items())
        lake.apagar(tabela, where)

    elif op == "reenvio_identico":
        # at-least-once: a fonte reenvia a mesma linha. A tabela ganha uma versão nova
        # sem que nenhum dado tenha mudado. Um duto por updated_at cai nessa; um por efeito líquido, não.
        where = " AND ".join(f"{k} = {_sql_literal(v)}" for k, v in ev["chave"].items())
        lake.atualizar(tabela, where, {"updated_at": f"TIMESTAMP '{agora()}'"})

    elif op == "regravacao_total":
        # a fonte regrava a tabela inteira com o mesmo conteúdo. O CDF mostra tudo como delete + insert.
        atual = lake.ler(tabela)
        lake.sobrescrever(tabela, atual)

    else:
        raise ValueError(f"operação desconhecida: {op}")

    return {"evento": evento, "nome": ev["nome"], "op": op, "versao_fonte": lake.versao(tabela)}


# =========================================================================== 20 · DUTO INCREMENTAL
def _cursor(lake: Lake, fonte: str) -> int:
    lake.criar("gold.cursor_sync")
    c = lake.ler("gold.cursor_sync")
    linha = c[c["fonte"] == fonte]
    return int(linha.iloc[0]["versao"]) if len(linha) else -1


def _salvar_cursor(lake: Lake, fonte: str, versao: int):
    lake.mesclar("gold.cursor_sync", pd.DataFrame([{"fonte": fonte, "versao": versao, "atualizado_em": agora()}]),
                 ["fonte"], quando_hash_mudar=False)


def sync(lake: Lake, modo: str = "referencia") -> dict:
    """O duto incremental: lê o Change Data Feed da fonte e leva só o delta até o índice do agente.

    As decisões que valem ponto:
      cursor        = a VERSÃO da tabela Delta, não o updated_at (relógio de origem mente)
      efeito líquido= compara o estado final da chave com o hash na Silver (sobrevive a reenvio e regravação)
      re-embed      = só o chunk cujo texto mudou
      deleção       = apaga de verdade na Silver e no índice, não marca como inativo
      tarifa nova   = fecha a vigência anterior, abre a nova, e avisa o agente pelo outbox
      LGPD          = apaga transações, pseudonimiza o cliente e manda esquecer_cliente pelo outbox
    """
    t0 = time.time()
    estatisticas = {"embeds_executados": 0, "embeds_evitados": 0}

    if modo == "ingenuo":
        # sem CDF: relê a fonte inteira, regrava e re-embeda tudo. Tarifas e LGPD ficam para trás.
        comunicados = lake.ler("fonte.comunicados")
        if len(comunicados):
            docs = comunicados[["doc_id", "versao", "titulo", "area", "tipo", "data", "conteudo"]].copy()
            docs["vigente"] = True
            docs["autoritativo"] = True
            docs["hash"] = ""
            docs["arquivo"] = "fonte.comunicados"
            docs["atualizado_em"] = agora()
            lake.apagar("silver.documentos", "arquivo = 'fonte.comunicados'")
            lake.acrescentar("silver.documentos", docs)
            estatisticas["docs_tocados"] = len(docs)
        m = gold(lake, "ingenuo")
        estatisticas["embeds_executados"] += m["embeds_executados"]
        lake.registrar_execucao("sync", modo, {"duracao_s": time.time() - t0, **estatisticas})
        return estatisticas

    _sync_comunicados(lake, estatisticas)
    _sync_tarifas(lake, estatisticas)
    _sync_lgpd(lake, estatisticas)
    lake.registrar_execucao("sync", modo, {"duracao_s": time.time() - t0, **estatisticas})
    return estatisticas


def _sync_comunicados(lake: Lake, estatisticas: dict):
    atual = lake.versao("fonte.comunicados")
    cursor = _cursor(lake, "comunicados")
    if atual <= cursor:
        return
    mudancas = lake.mudancas("fonte.comunicados", cursor + 1, atual)
    if not len(mudancas):
        _salvar_cursor(lake, "comunicados", atual)
        return

    tocados = set(mudancas["doc_id"])
    estatisticas["docs_tocados"] = len(tocados)

    estado = lake.ler("fonte.comunicados")
    presentes = estado[estado["doc_id"].isin(tocados)]
    apagados = tocados - set(presentes["doc_id"])

    if len(presentes):
        docs = presentes[["doc_id", "versao", "titulo", "area", "tipo", "data", "conteudo"]].copy()
        fundacao.gravar_silver(lake, "documentos", docs, ["doc_id", "versao"], "fonte.comunicados")
    if apagados:
        lista = ", ".join(f"'{d}'" for d in apagados)
        lake.apagar("silver.documentos", f"doc_id IN ({lista})")
        estatisticas["docs_apagados"] = len(apagados)

    fundacao.finalizar_documentos(lake, carregar_contratos()["documentos"])
    m = gold(lake, "referencia", filtro_doc_ids=tocados)
    estatisticas["embeds_executados"] += m["embeds_executados"]
    estatisticas["embeds_evitados"] += m["embeds_evitados"]
    _salvar_cursor(lake, "comunicados", atual)


def _sync_tarifas(lake: Lake, estatisticas: dict):
    atual = lake.versao("fonte.tarifas")
    cursor = _cursor(lake, "tarifas")
    if atual <= cursor:
        return
    mudancas = lake.mudancas("fonte.tarifas", cursor + 1, atual)
    tipos = set(mudancas["tipo"]) if len(mudancas) else set()
    fonte = lake.ler("fonte.tarifas")
    silver = lake.ler("silver.tarifas")
    alteradas = []

    for r in fonte[fonte["tipo"].isin(tipos)].to_dict("records"):
        vigente = silver[(silver["tipo"] == r["tipo"]) & (silver["vigencia_fim"].isna())]
        if len(vigente) and abs(float(vigente.iloc[0]["valor"]) - float(r["valor"])) < 1e-9:
            continue  # reenvio com o mesmo valor: nada a fazer
        inicio = pd.to_datetime(r["vigencia_inicio"]).date()
        if len(vigente):
            fim = inicio - dt.timedelta(days=1)
            lake.atualizar("silver.tarifas", f"tarifa_id = '{vigente.iloc[0]['tarifa_id']}'",
                           {"vigencia_fim": f"DATE '{fim}'"})
        nova = pd.DataFrame([{
            "tarifa_id": f"TF-{r['tipo']}-{inicio}", "tipo": r["tipo"], "valor": float(r["valor"]),
            "vigencia_inicio": inicio, "vigencia_fim": None, "hash": hash_texto(f"{r['tipo']}{r['valor']}{inicio}"),
            "arquivo": "fonte.tarifas", "atualizado_em": agora(),
        }])
        lake.mesclar("silver.tarifas", nova, ["tarifa_id"])
        alteradas.append(r["tipo"])

    if alteradas:
        lake.publicar_evento("invalidar_cache", {"topico": "tarifa", "tipos": alteradas})
        estatisticas["tarifas_alteradas"] = alteradas
    _salvar_cursor(lake, "tarifas", atual)


def _sync_lgpd(lake: Lake, estatisticas: dict):
    atual = lake.versao("fonte.lgpd_eliminacoes")
    cursor = _cursor(lake, "lgpd")
    if atual <= cursor:
        return
    mudancas = lake.mudancas("fonte.lgpd_eliminacoes", cursor + 1, atual)
    if not len(mudancas):
        _salvar_cursor(lake, "lgpd", atual)
        return
    pedidos = mudancas[mudancas["_change_type"] == "insert"][["pedido_id", "cliente_id"]].drop_duplicates()
    lake.criar("gold.eliminacoes_lgpd")

    for p in pedidos.to_dict("records"):
        cliente = p["cliente_id"]
        n = int(lake.escalar("SELECT COUNT(*) FROM silver.transacoes WHERE cliente_id = $c", {"c": cliente}) or 0)
        lake.apagar("silver.transacoes", f"cliente_id = '{cliente}'")
        lake.atualizar("silver.clientes", f"cliente_id = '{cliente}'",
                       {"nome": "'[eliminado LGPD]'", "cpf": "'***********'", "cidade": "NULL"})
        lake.acrescentar("gold.eliminacoes_lgpd", pd.DataFrame([{
            "pedido_id": p["pedido_id"], "cliente_id": cliente,
            "executado_em": agora(), "transacoes_apagadas": n,
        }]))
        # o cache e a memória do agente vivem FORA do lakehouse: o duto avisa, não alcança
        lake.publicar_evento("esquecer_cliente", {"cliente_id": cliente, "pedido_id": p["pedido_id"]})
        estatisticas.setdefault("lgpd", []).append(cliente)
    _salvar_cursor(lake, "lgpd", atual)


# =========================================================================== 30 · DUTO EXTERNO
def bcb(lake: Lake, caminho_snapshot: str, modo: str = "referencia") -> dict:
    """Séries do Banco Central → gold.indicadores.

    Decisões: chave natural (serie, data) com MERGE, então reprocessar não duplica; dia sem pregão
    NÃO é preenchido na tabela, o carry-forward acontece na CONSULTA; a idade do dado vai para a
    observabilidade, porque "o pipeline rodou" e "o dado está fresco" são coisas diferentes.
    """
    t0 = time.time()
    lake.criar("gold.indicadores")
    snap = json.loads(Path(caminho_snapshot).read_text(encoding="utf-8"))
    linhas = []
    for serie, s in snap["series"].items():
        for d in s["dados"]:
            dia, mes, ano = d["data"].split("/")
            linhas.append({"serie": serie, "nome": s["nome"], "data": dt.date(int(ano), int(mes), int(dia)),
                           "valor": float(d["valor"]), "fonte": snap.get("fonte", "bcb"), "ingerido_em": agora()})
    df = pd.DataFrame(linhas)
    antes = lake.contar("gold.indicadores")
    if modo == "ingenuo":
        lake.acrescentar("gold.indicadores", df)
    else:
        lake.mesclar("gold.indicadores", df, ["serie", "data"], quando_hash_mudar=False)
    depois = lake.contar("gold.indicadores")

    ultima = lake.escalar("SELECT MAX(data) FROM gold.indicadores")
    ultima = pd.to_datetime(ultima).date() if ultima is not None else None
    idade = (dt.date.today() - ultima).days if ultima is not None else None
    m = {"linhas_snapshot": len(linhas), "novas": depois - antes, "total": depois, "idade_dado_dias": idade}
    lake.registrar_execucao("bcb", modo, {"duracao_s": time.time() - t0, "rows_in": len(linhas),
                                          "rows_ok": depois - antes, **m})
    return m


# =========================================================================== 31 · SUPERFÍCIE DE LEITURA
def views(lake: Lake) -> dict:
    """As views que o Q enxerga. A regra de negócio mora aqui, não no prompt do agente:
    se o comitê mudar o percentual do CDB, muda a view, não o LLM."""
    lake.criar_view("gold.v_documentos_vigentes", """
        SELECT doc_id, versao, titulo, area, tipo, data
        FROM silver.documentos WHERE vigente AND autoritativo""")
    lake.criar_view("gold.v_tarifas", """
        SELECT tipo, valor, vigencia_inicio, vigencia_fim FROM silver.tarifas""")
    lake.criar_view("gold.v_saldos", """
        SELECT cliente_id, ROUND(SUM(valor), 2) AS saldo, COUNT(*) AS n_transacoes, MAX(data) AS ultima_transacao
        FROM silver.transacoes GROUP BY cliente_id""")
    lake.criar_view("gold.v_indicadores", """
        SELECT serie, nome, data, valor FROM gold.indicadores""")
    lake.criar_view("gold.v_regra_cdb", """
        SELECT DATE '2026-04-01' AS vigencia_inicio, 1.05 AS pct_cdi
        UNION ALL SELECT DATE '1900-01-01', 1.02""")
    return {"views": ["v_documentos_vigentes", "v_tarifas", "v_saldos", "v_indicadores", "v_regra_cdb"]}


# =========================================================================== retrieval
def buscar(lake: Lake, pergunta: str, k: int = 3, so_vigente: bool = True) -> pd.DataFrame:
    """Busca vetorial sobre gold.chunks. Com 60 chunks o produto escalar em numpy resolve;
    no Databricks isso seria um índice Vector Search, com a mesma semântica de filtro."""
    import numpy as np
    chunks = lake.ler("gold.chunks")
    if so_vigente:
        chunks = chunks[(chunks["vigente"] == True) & (chunks["autoritativo"] == True)]  # noqa: E712
    chunks = chunks[chunks["embedding"].notna()]
    if not len(chunks):
        return pd.DataFrame(columns=["doc_id", "versao", "texto", "score"])
    consulta = np.array(embeddings.embed([pergunta])[0], dtype=np.float32)
    matriz = np.vstack([np.array(v, dtype=np.float32) for v in chunks["embedding"]])
    scores = matriz @ consulta
    saida = chunks.assign(score=scores).sort_values("score", ascending=False).head(k)
    return saida[["chunk_id", "doc_id", "versao", "titulo", "tipo", "texto", "score"]].reset_index(drop=True)


# =========================================================================== sessão
def preparar_inbox(raiz_kit) -> "Path":
    """Cria uma cópia de trabalho do inbox. O Caos suja a cópia, nunca o original:
    assim dá para reiniciar a prática sem baixar o kit de novo."""
    import shutil
    raiz = Path(raiz_kit)
    origem, destino = raiz / "dados" / "inbox", raiz / "trabalho" / "inbox"
    shutil.rmtree(destino, ignore_errors=True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(origem, destino)
    return destino


def soltar_caos(raiz_kit, inbox) -> list[str]:
    """Os seis arquivos do Caos caem no inbox de trabalho."""
    import shutil
    raiz, inbox = Path(raiz_kit), Path(inbox)
    nomes = []
    for f in sorted((raiz / "dados" / "caos").iterdir()):
        destino = inbox / "docs" / f.name if f.suffix == ".md" else inbox / f.name
        shutil.copy(f, destino)
        nomes.append(f.name)
    return nomes
