"""Resources do MCP Quantum: dados que o cliente pode ler como contexto."""

import json

import catalogo


def catalogo_completo() -> str:
    return json.dumps(
        {"categorias": catalogo.categorias(), "produtos": catalogo.PRODUTOS},
        ensure_ascii=False,
    )


def detalhe_produto(produto_id: str) -> str:
    return json.dumps(catalogo.exigir(produto_id), ensure_ascii=False)


def registrar(mcp) -> None:
    mcp.resource(
        "catalogo://produtos",
        name="catalogo_completo",
        description="Catálogo completo da Quantum Commerce em JSON.",
        mime_type="application/json",
    )(catalogo_completo)
    mcp.resource(
        "produto://{produto_id}",
        name="detalhe_produto",
        description="Detalhe de um produto pelo ID (ex.: produto://P001).",
        mime_type="application/json",
    )(detalhe_produto)
