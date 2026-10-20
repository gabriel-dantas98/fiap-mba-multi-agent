"""Catálogo Quantum lido direto da planilha de chamados. Python puro, sem MCP.

A planilha tem uma linha por reclamação, com o produto repetido em cada linha.
Nome, descrição e categoria são fixos por produto; preço, vendedor e avaliação
variam porque o mesmo produto é vendido por vários vendedores (marketplace).
Por isso o catálogo agrega por id_produto:

- preço: média das ofertas + faixa mínimo/máximo
- nota: média das avaliacao_produto + mínimo/máximo/quantidade
- reclamações: contagem por classe

A leitura acontece no import. No Worker isso entra no snapshot de memória do
deploy, então nenhum request paga o parse.
"""

import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from planilha import ler_linhas

PLANILHA = Path(__file__).resolve().parent / "quantum-commerce-chamados.xlsx"

COLUNAS = [
    "id_produto",
    "nome_produto",
    "descricao_produto",
    "categoria_produto",
    "preco",
    "vendedor",
    "tipo_vendedor",
    "avaliacao_produto",
    "classe",
]


def carregar_chamados(caminho: Path = PLANILHA) -> list[dict]:
    chamados = ler_linhas(caminho.read_bytes())
    faltando = [c for c in COLUNAS if c not in chamados[0]]
    if faltando:
        raise ValueError(f"Planilha sem as colunas {faltando}.")
    return chamados


def agregar(chamados: list[dict]) -> list[dict]:
    por_produto = defaultdict(list)
    for c in chamados:
        por_produto[str(c["id_produto"]).strip()].append(c)

    produtos = []
    for produto_id in sorted(por_produto):
        linhas = por_produto[produto_id]
        base = linhas[0]
        precos = [float(r["preco"]) for r in linhas]
        notas = [float(r["avaliacao_produto"]) for r in linhas]
        produtos.append(
            {
                "id": produto_id,
                "nome": base["nome_produto"].strip(),
                "categoria": base["categoria_produto"].strip(),
                "descricao": base["descricao_produto"].strip(),
                "preco": round(statistics.mean(precos), 2),
                "preco_min": min(precos),
                "preco_max": max(precos),
                "vendedores": sorted({f"{r['vendedor']} ({r['tipo_vendedor']})" for r in linhas}),
                "nota": round(statistics.mean(notas), 2),
                "nota_min": min(notas),
                "nota_max": max(notas),
                "num_avaliacoes": len(notas),
                "reclamacoes_por_classe": dict(Counter(r["classe"] for r in linhas).most_common()),
            }
        )
    return produtos


PRODUTOS = agregar(carregar_chamados())
_POR_ID = {p["id"].upper(): p for p in PRODUTOS}


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def categorias() -> list[str]:
    return sorted({p["categoria"] for p in PRODUTOS}, key=_normalizar)


def listar_por_categoria(categoria: str) -> list[dict]:
    alvo = _normalizar(categoria)
    return [p for p in PRODUTOS if _normalizar(p["categoria"]) == alvo]


def obter(produto_id: str) -> dict | None:
    return _POR_ID.get(produto_id.strip().upper())


def exigir(produto_id: str) -> dict:
    """Como obter(), mas levanta ValueError (vira isError no MCP) se não existir."""
    produto = obter(produto_id)
    if produto is None:
        raise ValueError(f"Produto '{produto_id}' não encontrado.")
    return produto


def buscar_por_nome(termo: str, limite: int = 10) -> list[dict]:
    palavras = _normalizar(termo).split()
    if not palavras:
        return []
    achados = [p for p in PRODUTOS if all(w in _normalizar(p["nome"]) for w in palavras)]
    return achados[:limite]


def avaliacao(produto: dict) -> dict:
    return {
        "id": produto["id"],
        "nome": produto["nome"],
        "nota_media": produto["nota"],
        "escala": "0 a 5",
        "nota_min": produto["nota_min"],
        "nota_max": produto["nota_max"],
        "num_avaliacoes": produto["num_avaliacoes"],
        "reclamacoes_por_classe": produto["reclamacoes_por_classe"],
    }


def resumo(produto: dict) -> dict:
    return {k: produto[k] for k in ("id", "nome", "categoria", "preco") if k in produto}
