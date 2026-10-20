"""Consultas ao catálogo Quantum. Python puro, sem dependência de MCP."""

import unicodedata

from dados import PRODUTOS

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
        "nota": produto.get("nota"),
        "escala": "0 a 5",
        "num_avaliacoes": produto.get("num_avaliacoes"),
    }


def resumo(produto: dict) -> dict:
    return {k: produto[k] for k in ("id", "nome", "categoria", "preco") if k in produto}
