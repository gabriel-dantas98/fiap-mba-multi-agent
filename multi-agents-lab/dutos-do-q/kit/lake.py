"""lake.py — a plataforma de dados da aula: Delta Lake de verdade, sem Spark.

Por que sem Spark: a aula é sobre integração e ingestão, não sobre operar um cluster. O `deltalake`
(delta-rs, Rust) dá transação ACID, MERGE, time travel e Change Data Feed num `pip install`, e o DuckDB
consulta as mesmas tabelas com `delta_scan`. Os volumes da aula são pequenos; a semântica é idêntica
à do Databricks, que é o que se avalia.

O que muda em produção: o executor (Spark/Photon), o catálogo (Unity Catalog) e o Auto Loader.
O contrato, a chave de idempotência, a vigência e o CDF não mudam.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake


# --------------------------------------------------------------------------- utilidades
def hash_texto(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:24]


def agora() -> dt.datetime:
    return dt.datetime.now().replace(microsecond=0)


def hash_linha(registro: dict, colunas: list[str]) -> str:
    return hash_texto(json.dumps({c: str(registro.get(c)) for c in colunas}, sort_keys=True, ensure_ascii=False))


# --------------------------------------------------------------------------- schemas
# Schemas explícitos evitam o problema clássico de deixar o pandas adivinhar o tipo:
# uma coluna que vem como Int64 numa execução e como object na seguinte quebra o MERGE.
SCHEMAS: dict[str, pa.Schema] = {
    "bronze.arquivos": pa.schema([
        ("path", pa.string()), ("nome", pa.string()), ("tamanho", pa.int64()),
        ("conteudo", pa.binary()), ("hash_arquivo", pa.string()), ("ingerido_em", pa.timestamp("us")),
    ]),
    "silver.clientes": pa.schema([
        ("cliente_id", pa.string()), ("nome", pa.string()), ("cpf", pa.string()),
        ("segmento", pa.string()), ("cidade", pa.string()), ("cadastro_em", pa.date32()),
        ("hash", pa.string()), ("arquivo", pa.string()), ("atualizado_em", pa.timestamp("us")),
    ]),
    "silver.transacoes": pa.schema([
        ("transacao_id", pa.string()), ("cliente_id", pa.string()), ("tipo", pa.string()),
        ("valor", pa.float64()), ("data", pa.date32()),
        ("hash", pa.string()), ("arquivo", pa.string()), ("atualizado_em", pa.timestamp("us")),
    ]),
    "silver.tarifas": pa.schema([
        ("tarifa_id", pa.string()), ("tipo", pa.string()), ("valor", pa.float64()),
        ("vigencia_inicio", pa.date32()), ("vigencia_fim", pa.date32()),
        ("hash", pa.string()), ("arquivo", pa.string()), ("atualizado_em", pa.timestamp("us")),
    ]),
    "silver.documentos": pa.schema([
        ("doc_id", pa.string()), ("versao", pa.int32()), ("titulo", pa.string()), ("area", pa.string()),
        ("tipo", pa.string()), ("data", pa.date32()), ("conteudo", pa.string()),
        ("vigente", pa.bool_()), ("autoritativo", pa.bool_()),
        ("hash", pa.string()), ("arquivo", pa.string()), ("atualizado_em", pa.timestamp("us")),
    ]),
    "silver.quarentena": pa.schema([
        ("fonte", pa.string()), ("arquivo", pa.string()), ("chave", pa.string()),
        ("motivo", pa.string()), ("registro", pa.string()), ("hora", pa.timestamp("us")),
    ]),
    "silver.arquivos_processados": pa.schema([
        ("path", pa.string()), ("hash_arquivo", pa.string()), ("fonte", pa.string()),
        ("status", pa.string()), ("linhas_ok", pa.int32()), ("linhas_quarentena", pa.int32()),
        ("hora", pa.timestamp("us")),
    ]),
    "gold.chunks": pa.schema([
        ("chunk_id", pa.string()), ("doc_id", pa.string()), ("versao", pa.int32()), ("ordem", pa.int32()),
        ("texto", pa.string()), ("hash", pa.string()), ("titulo", pa.string()), ("area", pa.string()),
        ("tipo", pa.string()), ("data", pa.date32()), ("vigente", pa.bool_()), ("autoritativo", pa.bool_()),
        ("embedding", pa.list_(pa.float32())), ("atualizado_em", pa.timestamp("us")),
    ]),
    "gold.indicadores": pa.schema([
        ("serie", pa.string()), ("nome", pa.string()), ("data", pa.date32()),
        ("valor", pa.float64()), ("fonte", pa.string()), ("ingerido_em", pa.timestamp("us")),
    ]),
    "gold.execucoes": pa.schema([
        ("execucao_id", pa.string()), ("duto", pa.string()), ("modo", pa.string()),
        ("iniciado_em", pa.timestamp("us")), ("duracao_s", pa.float64()),
        ("rows_in", pa.int64()), ("rows_ok", pa.int64()), ("rows_rejected", pa.int64()),
        ("embeds_executados", pa.int64()), ("embeds_evitados", pa.int64()), ("detalhes", pa.string()),
    ]),
    "gold.eventos_agente": pa.schema([
        ("evento_id", pa.string()), ("tipo", pa.string()), ("payload", pa.string()),
        ("criado_em", pa.timestamp("us")), ("consumido", pa.bool_()),
    ]),
    "gold.cursor_sync": pa.schema([
        ("fonte", pa.string()), ("versao", pa.int64()), ("atualizado_em", pa.timestamp("us")),
    ]),
    "gold.eliminacoes_lgpd": pa.schema([
        ("pedido_id", pa.string()), ("cliente_id", pa.string()),
        ("executado_em", pa.timestamp("us")), ("transacoes_apagadas", pa.int64()),
    ]),
    "gold.liberacao": pa.schema([
        ("status", pa.string()), ("violacoes", pa.string()),
        ("justificativa", pa.string()), ("hora", pa.timestamp("us")),
    ]),
    # a fonte mutável da Quantum (o "sistema de origem"), com CDF ligado
    "fonte.comunicados": pa.schema([
        ("doc_id", pa.string()), ("titulo", pa.string()), ("area", pa.string()), ("tipo", pa.string()),
        ("data", pa.date32()), ("versao", pa.int32()), ("conteudo", pa.string()),
        ("updated_at", pa.timestamp("us")),
    ]),
    "fonte.tarifas": pa.schema([
        ("tipo", pa.string()), ("valor", pa.float64()),
        ("vigencia_inicio", pa.date32()), ("updated_at", pa.timestamp("us")),
    ]),
    "fonte.lgpd_eliminacoes": pa.schema([
        ("pedido_id", pa.string()), ("cliente_id", pa.string()),
        ("solicitado_em", pa.date32()), ("updated_at", pa.timestamp("us")),
    ]),
}

# tabelas com Change Data Feed ligado: as que alguém consome incrementalmente
COM_CDF = {"fonte.comunicados", "fonte.tarifas", "fonte.lgpd_eliminacoes", "gold.chunks"}


class Lake:
    """Um lakehouse em uma pasta. Cada tabela é um diretório Delta; o DuckDB consulta por cima."""

    def __init__(self, raiz: str = "lakehouse"):
        self.raiz = Path(raiz)
        self.raiz.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect()
        self.con.execute("INSTALL delta; LOAD delta;")
        self._views_registradas: set[str] = set()

    # ----------------------------------------------------------------- caminho e existência
    def caminho(self, nome: str) -> str:
        schema, _, tabela = nome.partition(".")
        return str(self.raiz / schema / tabela)

    def existe(self, nome: str) -> bool:
        return DeltaTable.is_deltatable(self.caminho(nome))

    def schema(self, nome: str) -> pa.Schema:
        if nome not in SCHEMAS:
            raise KeyError(f"tabela desconhecida: {nome}. Conhecidas: {sorted(SCHEMAS)}")
        return SCHEMAS[nome]

    def tabelas(self) -> list[str]:
        return sorted(n for n in SCHEMAS if self.existe(n))

    # ----------------------------------------------------------------- criação
    def criar(self, nome: str, se_nao_existir: bool = True):
        """Cria a tabela vazia com o schema declarado (e CDF quando for o caso)."""
        if se_nao_existir and self.existe(nome):
            return self
        esquema = self.schema(nome)
        conf = {"delta.enableChangeDataFeed": "true"} if nome in COM_CDF else None
        write_deltalake(self.caminho(nome), esquema.empty_table(), mode="overwrite",
                        configuration=conf, schema_mode="overwrite")
        self._views_registradas.discard(nome)
        return self

    def criar_todas(self, *nomes: str):
        for n in (nomes or SCHEMAS):
            self.criar(n)
        return self

    # ----------------------------------------------------------------- conversão
    def _arrow(self, nome: str, df: pd.DataFrame) -> pa.Table:
        """pandas → Arrow no schema declarado. É aqui que os tipos são fixados, uma vez só."""
        esquema = self.schema(nome)
        df = df.copy()
        for campo in esquema:
            if campo.name not in df.columns:
                df[campo.name] = None
            col = df[campo.name]
            if pa.types.is_date32(campo.type):
                df[campo.name] = pd.to_datetime(col, errors="coerce").dt.date
            elif pa.types.is_timestamp(campo.type):
                df[campo.name] = pd.to_datetime(col, errors="coerce")
            elif pa.types.is_integer(campo.type):
                df[campo.name] = pd.to_numeric(col, errors="coerce").astype("float64")
            elif pa.types.is_floating(campo.type):
                df[campo.name] = pd.to_numeric(col, errors="coerce")
            elif pa.types.is_boolean(campo.type):
                df[campo.name] = col.map(lambda v: None if v is None or (isinstance(v, float) and v != v) else bool(v))
        df = df[[c.name for c in esquema]]
        return pa.Table.from_pandas(df, schema=esquema, preserve_index=False, safe=False)

    # ----------------------------------------------------------------- leitura
    def ler(self, nome: str) -> pd.DataFrame:
        if not self.existe(nome):
            return self.schema(nome).empty_table().to_pandas()
        return DeltaTable(self.caminho(nome)).to_pyarrow_table().to_pandas()

    def contar(self, nome: str) -> int:
        return 0 if not self.existe(nome) else len(self.ler(nome))

    # ----------------------------------------------------------------- escrita
    def acrescentar(self, nome: str, df: pd.DataFrame):
        """APPEND puro. É o que o modo ingênuo faz, e é por isso que ele duplica ao rodar duas vezes."""
        if df is None or not len(df):
            return 0
        self.criar(nome)
        write_deltalake(self.caminho(nome), self._arrow(nome, df), mode="append")
        return len(df)

    def sobrescrever(self, nome: str, df: pd.DataFrame):
        esquema = self.schema(nome)
        tab = self._arrow(nome, df) if df is not None and len(df) else esquema.empty_table()
        conf = {"delta.enableChangeDataFeed": "true"} if nome in COM_CDF else None
        write_deltalake(self.caminho(nome), tab, mode="overwrite", configuration=conf, schema_mode="overwrite")
        return len(tab)

    def mesclar(self, nome: str, df: pd.DataFrame, chave: list[str], quando_hash_mudar: bool = True,
                apagar_ausentes: str | None = None) -> dict:
        """MERGE por chave natural. Com `hash` na tabela, só atualiza a linha que realmente mudou:
        é o que torna a segunda execução barata e idempotente.

        apagar_ausentes: predicado SQL sobre `alvo` delimitando o escopo em que uma linha que NÃO veio
        na origem deve ser apagada (o `WHEN NOT MATCHED BY SOURCE` do Databricks). Use "true" para o
        escopo inteiro. Sem ele, o MERGE nunca apaga, e um documento revogado fica vivo no índice.
        """
        if (df is None or not len(df)) and apagar_ausentes is None:
            return {"inseridas": 0, "atualizadas": 0, "apagadas": 0}
        self.criar(nome)
        origem = self._arrow(nome, df if df is not None and len(df) else pd.DataFrame(columns=[c.name for c in self.schema(nome)]))
        dt_ = DeltaTable(self.caminho(nome))
        predicado = " AND ".join(f"alvo.{k} = origem.{k}" for k in chave)
        m = dt_.merge(source=origem, predicate=predicado, source_alias="origem", target_alias="alvo")
        m = m.when_matched_update_all("alvo.hash != origem.hash") if quando_hash_mudar and "hash" in origem.column_names \
            else m.when_matched_update_all()
        m = m.when_not_matched_insert_all()
        if apagar_ausentes is not None:
            m = m.when_not_matched_by_source_delete(predicate=None if apagar_ausentes == "true" else apagar_ausentes)
        r = m.execute()
        self._views_registradas.discard(nome)
        return {"inseridas": r.get("num_target_rows_inserted", 0), "atualizadas": r.get("num_target_rows_updated", 0),
                "apagadas": r.get("num_target_rows_deleted", 0)}

    def apagar(self, nome: str, predicado: str) -> int:
        """DELETE físico. Na Missão 2 é o que a LGPD exige, e é o oposto de um tombstone."""
        if not self.existe(nome):
            return 0
        r = DeltaTable(self.caminho(nome)).delete(predicado)
        self._views_registradas.discard(nome)
        return r.get("num_deleted_rows", 0)

    def atualizar(self, nome: str, predicado: str, novos: dict[str, str]) -> int:
        if not self.existe(nome):
            return 0
        r = DeltaTable(self.caminho(nome)).update(updates=novos, predicate=predicado)
        self._views_registradas.discard(nome)
        return r.get("num_updated_rows", 0)

    # ----------------------------------------------------------------- versão e CDF
    def versao(self, nome: str) -> int:
        return -1 if not self.existe(nome) else DeltaTable(self.caminho(nome)).version()

    def historico(self, nome: str) -> pd.DataFrame:
        return pd.DataFrame(DeltaTable(self.caminho(nome)).history())

    def mudancas(self, nome: str, desde: int, ate: int | None = None) -> pd.DataFrame:
        """Change Data Feed: o que mudou entre duas versões, com _change_type e _commit_version.
        É a diferença entre reprocessar a fonte inteira e processar só o delta."""
        if not self.existe(nome):
            return pd.DataFrame()
        dt_ = DeltaTable(self.caminho(nome))
        ate = dt_.version() if ate is None else ate
        if desde > ate:
            return pd.DataFrame()
        tabela = dt_.load_cdf(starting_version=desde, ending_version=ate)
        return pa.table(tabela.read_all()).to_pandas()

    def viajar(self, nome: str, versao: int) -> pd.DataFrame:
        dt_ = DeltaTable(self.caminho(nome))
        dt_.load_as_version(versao)
        return dt_.to_pyarrow_table().to_pandas()

    # ----------------------------------------------------------------- SQL
    def _registrar(self, nome: str):
        if nome in self._views_registradas or not self.existe(nome):
            return
        schema = nome.split(".")[0]
        self.con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        self.con.execute(f"CREATE OR REPLACE VIEW {nome} AS SELECT * FROM delta_scan('{self.caminho(nome)}')")
        self._views_registradas.add(nome)

    def sql(self, consulta: str, parametros: dict | None = None) -> pd.DataFrame:
        """SQL sobre as tabelas Delta (DuckDB + delta_scan). Parâmetros vão por $nome, nunca por concatenação."""
        for nome in SCHEMAS:
            if nome in consulta:
                self._registrar(nome)
        return self.con.execute(consulta, parametros or {}).fetchdf()

    def escalar(self, consulta: str, parametros: dict | None = None):
        df = self.sql(consulta, parametros)
        return None if df.empty else df.iloc[0, 0]

    def criar_view(self, nome: str, consulta: str):
        """View de leitura do agente. Ela some quando a sessão cai: é catálogo, não dado."""
        for t in SCHEMAS:
            if t in consulta:
                self._registrar(t)
        self.con.execute("CREATE SCHEMA IF NOT EXISTS gold")
        self.con.execute(f"CREATE OR REPLACE VIEW {nome} AS {consulta}")
        return nome

    # ----------------------------------------------------------------- observabilidade
    def registrar_execucao(self, duto: str, modo: str, metricas: dict) -> dict:
        linha = {
            "execucao_id": hash_texto(duto + str(agora()) + str(metricas)),
            "duto": duto, "modo": modo, "iniciado_em": metricas.pop("iniciado_em", agora()),
            "duracao_s": float(metricas.pop("duracao_s", 0.0)),
            "rows_in": int(metricas.pop("rows_in", 0)), "rows_ok": int(metricas.pop("rows_ok", 0)),
            "rows_rejected": int(metricas.pop("rows_rejected", 0)),
            "embeds_executados": int(metricas.pop("embeds_executados", 0)),
            "embeds_evitados": int(metricas.pop("embeds_evitados", 0)),
            "detalhes": json.dumps(metricas, ensure_ascii=False, default=str),
        }
        self.acrescentar("gold.execucoes", pd.DataFrame([linha]))
        return linha

    def publicar_evento(self, tipo: str, payload: dict) -> dict:
        """Outbox: a plataforma não chama o agente, ela deixa um recado numa tabela.
        Quem vive fora do lakehouse (cache, memória) consome quando puder."""
        linha = {
            "evento_id": hash_texto(tipo + json.dumps(payload, sort_keys=True) + str(agora())),
            "tipo": tipo, "payload": json.dumps(payload, ensure_ascii=False),
            "criado_em": agora(), "consumido": False,
        }
        self.acrescentar("gold.eventos_agente", pd.DataFrame([linha]))
        return linha

    # ----------------------------------------------------------------- manutenção
    def zerar(self, *nomes: str):
        """Apaga tabelas. Sem nomes, apaga o lakehouse inteiro (é o botão de reinício da aula)."""
        if not nomes:
            shutil.rmtree(self.raiz, ignore_errors=True)
            self.raiz.mkdir(parents=True, exist_ok=True)
            self._views_registradas.clear()
            return self
        for n in nomes:
            shutil.rmtree(self.caminho(n), ignore_errors=True)
            self._views_registradas.discard(n)
        return self

    def resumo(self) -> pd.DataFrame:
        linhas = [{"tabela": n, "linhas": self.contar(n), "versao": self.versao(n),
                   "cdf": n in COM_CDF} for n in self.tabelas()]
        return pd.DataFrame(linhas)
