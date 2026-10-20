"""Prompts do MCP Quantum: roteiros prontos que o cliente oferece ao usuário."""


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


def analisar_produto(produto_id: str) -> str:
    """Pede uma análise de custo-benefício de um produto frente à categoria dele."""
    return (
        f"Analise o produto {produto_id} do marketplace Quantum Commerce. "
        "Use obter_produto para os dados, obter_avaliacao_produto para a nota e "
        "listar_produtos_por_categoria para comparar com os concorrentes da mesma categoria. "
        "Responda com: pontos fortes, pontos de atenção (inclua as reclamações por classe), "
        "posição de preço e nota na categoria, e um veredito de custo-benefício."
    )


def registrar(mcp) -> None:
    mcp.prompt(title="Recomendar produto")(recomendar_produto)
    mcp.prompt(title="Analisar produto")(analisar_produto)
