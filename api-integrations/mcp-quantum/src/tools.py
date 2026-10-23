"""Tools do MCP Quantum: as 4 ações que o agente pode executar no catálogo."""

import catalogo


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


def obter_produto(produto_id: str) -> dict:
    """Dado o ID de um produto (ex.: 'P001'), retorna nome, categoria, valor e demais dados.

    `preco` é a média das ofertas dos vendedores; `preco_min`/`preco_max` dão a faixa.
    """
    return catalogo.exigir(produto_id)


def buscar_produto_por_nome(nome: str) -> dict:
    """Busca produtos pelo nome (todas as palavras precisam aparecer; ignora acentos)."""
    achados = catalogo.buscar_por_nome(nome)
    return {"termo": nome, "total": len(achados), "produtos": [catalogo.resumo(p) for p in achados]}


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


def registrar(mcp) -> None:
    for tool in (
        listar_produtos_por_categoria,
        obter_produto,
        buscar_produto_por_nome,
        obter_avaliacao_produto,
    ):
        mcp.tool()(tool)
