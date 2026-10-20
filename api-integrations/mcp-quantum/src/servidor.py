"""Servidor MCP do desafio Quantum: 4 tools, 2 resources e 2 prompts.

Roda igual no Cloudflare Worker (src/main.py) e localmente (src/local.py).
"""

import json

import catalogo
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

HOSTS_PERMITIDOS = [
    "mcp-quantum.gabsdevops.workers.dev",
    "localhost:*",
    "127.0.0.1:*",
]

mcp = FastMCP(
    "quantum-catalogo",
    instructions=(
        "Catálogo de produtos do marketplace Quantum Commerce. Use as tools para listar por "
        "categoria, buscar por nome, detalhar um produto pelo ID e consultar a nota de avaliação."
    ),
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=HOSTS_PERMITIDOS,
        allowed_origins=[f"https://{h}" for h in HOSTS_PERMITIDOS[:1]]
        + ["http://localhost:*", "http://127.0.0.1:*"],
    ),
)


def _exigir(produto_id: str) -> dict:
    produto = catalogo.obter(produto_id)
    if produto is None:
        raise ValueError(f"Produto '{produto_id}' não encontrado.")
    return produto


# --- Tools -----------------------------------------------------------------


@mcp.tool()
def listar_produtos_por_categoria(categoria: str) -> dict:
    """Lista os produtos de uma categoria (ex.: 'game', 'livro', 'maquiagem').

    A comparação ignora acentos e maiúsculas. Se a categoria não existir,
    retorna a lista de categorias válidas.
    """
    produtos = catalogo.listar_por_categoria(categoria)
    if not produtos:
        raise ValueError(
            f"Categoria '{categoria}' não encontrada. "
            f"Categorias válidas: {', '.join(catalogo.categorias())}."
        )
    return {
        "categoria": produtos[0]["categoria"],
        "total": len(produtos),
        "produtos": [catalogo.resumo(p) for p in produtos],
    }


@mcp.tool()
def obter_produto(produto_id: str) -> dict:
    """Dado o ID de um produto (ex.: 'P001'), retorna nome, categoria, valor e demais dados.

    `preco` é a média das ofertas dos vendedores; `preco_min`/`preco_max` dão a faixa.
    """
    return _exigir(produto_id)


@mcp.tool()
def buscar_produto_por_nome(nome: str) -> dict:
    """Busca produtos pelo nome (todas as palavras precisam aparecer; ignora acentos)."""
    achados = catalogo.buscar_por_nome(nome)
    return {"termo": nome, "total": len(achados), "produtos": [catalogo.resumo(p) for p in achados]}


@mcp.tool()
def obter_avaliacao_produto(produto: str) -> dict:
    """Retorna a nota de avaliação (review) de um produto, informado por ID ou nome.

    Traz a média, a faixa e o total de avaliações, mais as reclamações por classe.
    """
    encontrado = catalogo.obter(produto)
    if encontrado is None:
        achados = catalogo.buscar_por_nome(produto, limite=2)
        if len(achados) != 1:
            opcoes = ", ".join(f"{p['id']} ({p['nome']})" for p in achados) or "nenhum"
            raise ValueError(
                f"Não identifiquei um único produto para '{produto}'. Opções: {opcoes}."
            )
        encontrado = achados[0]
    return catalogo.avaliacao(encontrado)


# --- Resources -------------------------------------------------------------


@mcp.resource(
    "catalogo://produtos",
    name="catalogo_completo",
    description="Catálogo completo da Quantum Commerce em JSON.",
    mime_type="application/json",
)
def catalogo_completo() -> str:
    return json.dumps(
        {"categorias": catalogo.categorias(), "produtos": catalogo.PRODUTOS},
        ensure_ascii=False,
    )


@mcp.resource(
    "produto://{produto_id}",
    name="detalhe_produto",
    description="Detalhe de um produto pelo ID (ex.: produto://P001).",
    mime_type="application/json",
)
def detalhe_produto(produto_id: str) -> str:
    return json.dumps(_exigir(produto_id), ensure_ascii=False)


# --- Prompts ---------------------------------------------------------------


@mcp.prompt(title="Recomendar produto")
def recomendar_produto(necessidade: str, orcamento: str = "", categoria: str = "") -> str:
    """Monta um pedido de recomendação usando as tools do catálogo."""
    filtros = []
    if categoria:
        filtros.append(f"categoria preferida: {categoria}")
    if orcamento:
        filtros.append(f"orçamento máximo: R$ {orcamento}")
    extra = f" ({'; '.join(filtros)})" if filtros else ""
    return (
        f"Sou cliente do marketplace Quantum Commerce e preciso de: {necessidade}{extra}.\n"
        "Use as tools listar_produtos_por_categoria, buscar_produto_por_nome e "
        "obter_avaliacao_produto para montar até 3 recomendações. Para cada uma, "
        "traga ID, nome, preço médio e nota média, e explique em uma frase por que ela atende. "
        "Não invente produtos que não estejam no catálogo."
    )


@mcp.prompt(title="Analisar produto")
def analisar_produto(produto_id: str) -> str:
    """Pede uma análise de custo-benefício de um produto frente à categoria dele."""
    return (
        f"Analise o produto {produto_id} do marketplace Quantum Commerce. Use obter_produto para os dados, "
        "obter_avaliacao_produto para a nota e listar_produtos_por_categoria para comparar "
        "com os concorrentes da mesma categoria. Responda com: pontos fortes, pontos de "
        "atenção (inclua as reclamações por classe), posição de preço e nota na categoria, e um veredito de custo-benefício."
    )
