"""fundacao.py — a FUNDAÇÃO (dada, lacrada).

É o conjunto de peças que o Agent 1 (Construtor) pode compor para montar a Silver. O código que o LLM
escreve chama estas funções e mais nada: ele não cria tabelas, não escolhe nomes e não escreve fora da
Silver. Isso é o que mantém o harness determinístico, porque o que se avalia são as tabelas resultantes,
não o texto do código.

Interface que o código gerado precisa expor:
    def pipeline(lake, contrato: dict) -> dict     # devolve {rows_in, rows_ok, rows_rejected, arquivos, corrigidos, drift}
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json

import pandas as pd

from contrato import ler_arquivo, validar
from lake import Lake, agora, hash_linha, hash_texto

# colunas de negócio por fonte (sem as técnicas), usadas para o hash de idempotência
COLUNAS = {
    "clientes": ["cliente_id", "nome", "cpf", "segmento", "cidade", "cadastro_em"],
    "transacoes": ["transacao_id", "cliente_id", "tipo", "valor", "data"],
    "tarifas": ["tarifa_id", "tipo", "valor", "vigencia_inicio", "vigencia_fim"],
    "documentos": ["doc_id", "versao", "titulo", "area", "tipo", "data", "conteudo"],
}


def arquivos_pendentes(lake: Lake, padrao_glob: str) -> list[dict]:
    """Linhas da Bronze que ainda não foram processadas e cujo nome casa com o padrão do contrato.
    O anti-join com silver.arquivos_processados é o que faz a segunda execução não refazer nada."""
    bronze = lake.ler("bronze.arquivos")
    if not len(bronze):
        return []
    processados = set(lake.ler("silver.arquivos_processados")["path"]) if lake.existe("silver.arquivos_processados") else set()
    pendentes = bronze[~bronze["path"].isin(processados)]
    return [r for r in pendentes.to_dict("records") if fnmatch.fnmatch(r["nome"], padrao_glob)]


def ler(nome: str, conteudo: bytes, contrato: dict):
    """Decodifica e parseia um arquivo segundo o contrato (csv / parquet / markdown com front-matter).
    Lança ValueError quando o arquivo inteiro é inválido (schema drift, encoding, front-matter ausente)."""
    return ler_arquivo(nome, bytes(conteudo), contrato)


def aplicar_contrato(df: pd.DataFrame, contrato: dict, referencias: dict | None = None):
    """Correções, regras de coluna, regras de linha, FK, duplicatas e regras de conjunto.
    Devolve (ok, quarentena, n_correcoes)."""
    return validar(df, contrato, referencias)


def referencia_clientes(lake: Lake) -> set:
    """Os cliente_id que já estão na Silver, para a FK de transações."""
    return set(lake.ler("silver.clientes")["cliente_id"]) if lake.existe("silver.clientes") else set()


def gravar_silver(lake: Lake, fonte: str, ok: pd.DataFrame, chave: list[str] | None, arquivo: str = ""):
    """MERGE idempotente por chave natural, com hash da linha: reenviar o mesmo arquivo não muda nada.

    Sem chave declarada no contrato não existe MERGE possível: a gravação vira APPEND, e o mesmo
    arquivo reenviado entra de novo. É o custo exato de não ter decidido a chave de idempotência.
    """
    if ok is None or not len(ok):
        return {"inseridas": 0, "atualizadas": 0}
    cols = COLUNAS[fonte]
    linhas = ok.copy()
    linhas["hash"] = [hash_linha(r, cols) for r in linhas.to_dict("records")]
    linhas["arquivo"] = arquivo
    linhas["atualizado_em"] = agora()
    if not chave:
        return {"inseridas": lake.acrescentar(f"silver.{fonte}", linhas), "atualizadas": 0, "sem_chave": True}
    linhas = linhas.drop_duplicates(subset=chave, keep="last")
    return lake.mesclar(f"silver.{fonte}", linhas, chave)


def gravar_quarentena(lake: Lake, fonte: str, arquivo: str, quarentena: pd.DataFrame | None,
                      motivo_arquivo: str | None = None):
    """Quarentena com motivo legível. Reprocessar o mesmo arquivo substitui as linhas dele, não acumula."""
    lake.criar("silver.quarentena")
    lake.apagar("silver.quarentena", f"arquivo = '{arquivo}'")
    linhas = []
    if motivo_arquivo:
        linhas.append({"fonte": fonte, "arquivo": arquivo, "chave": "*arquivo*",
                       "motivo": f"arquivo rejeitado: {motivo_arquivo}", "registro": "{}"})
    if quarentena is not None and len(quarentena):
        linhas += [{"fonte": fonte, "arquivo": arquivo, **q} for q in quarentena.to_dict("records")]
    if linhas:
        df = pd.DataFrame(linhas)
        df["hora"] = agora()
        lake.acrescentar("silver.quarentena", df)
    return len(linhas)


def marcar_processado(lake: Lake, path: str, fonte: str, status: str, ok: int, q: int):
    lake.acrescentar("silver.arquivos_processados", pd.DataFrame([{
        "path": path, "hash_arquivo": hash_texto(path), "fonte": fonte,
        "status": status, "linhas_ok": ok, "linhas_quarentena": q, "hora": agora(),
    }]))


def finalizar_documentos(lake: Lake, contrato_docs: dict):
    """vigente = a maior versão de cada doc_id; autoritativo = tipo fora da lista de ruído.
    Sem isso, a v1 da tabela de tarifas continua no índice ao lado da v2, e o agente escolhe a errada."""
    docs = lake.ler("silver.documentos")
    if not len(docs):
        return {"vigentes": 0}
    nao_autoritativos = set(contrato_docs.get("tipos_nao_autoritativos") or [])
    vmax = docs.groupby("doc_id")["versao"].transform("max")
    novo = docs.copy()
    novo["vigente"] = docs["versao"] == vmax
    novo["autoritativo"] = ~docs["tipo"].isin(nao_autoritativos)
    mudou = novo[(novo["vigente"] != docs["vigente"].fillna(False)) |
                 (novo["autoritativo"] != docs["autoritativo"].fillna(False))]
    if len(mudou):
        lake.mesclar("silver.documentos", mudou, ["doc_id", "versao"], quando_hash_mudar=False)
    return {"vigentes": int(novo["vigente"].sum()), "linhas_ajustadas": len(mudou)}
