"""Resources do MCP Quantum: dados que o cliente pode ler como contexto."""

import json

import catalogo

URI_CATALOGO = "catalogo://produtos"
URI_PRODUTO = "produto://{produto_id}"
DESCRICOES = {
    URI_CATALOGO: "Catálogo completo da Quantum Commerce em JSON.",
    URI_PRODUTO: "Detalhe de um produto pelo ID (ex.: produto://P001).",
}


def catalogo_completo() -> str:
    return json.dumps(
        {"categorias": catalogo.categorias(), "produtos": catalogo.PRODUTOS},
        ensure_ascii=False,
    )


def detalhe_produto(produto_id: str) -> str:
    return json.dumps(catalogo.exigir(produto_id), ensure_ascii=False)


def registrar(mcp) -> None:
    mcp.resource(
        URI_CATALOGO,
        name="catalogo_completo",
        description=DESCRICOES[URI_CATALOGO],
        mime_type="application/json",
    )(catalogo_completo)
    mcp.resource(
        URI_PRODUTO,
        name="detalhe_produto",
        description=DESCRICOES[URI_PRODUTO],
        mime_type="application/json",
    )(detalhe_produto)
