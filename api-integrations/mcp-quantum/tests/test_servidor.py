import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from servidor import mcp


async def chamar(tool: str, **args):
    resultado = await mcp.call_tool(tool, args)
    # O SDK devolve (conteúdo, estruturado) ou só o conteúdo, conforme o tipo de retorno.
    if isinstance(resultado, tuple):
        return resultado[1]
    return json.loads(resultado[0].text)


async def test_registra_4_tools_2_resources_2_prompts():
    tools = {t.name for t in await mcp.list_tools()}
    assert tools == {
        "listar_produtos_por_categoria",
        "obter_produto",
        "buscar_produto_por_nome",
        "obter_avaliacao_produto",
    }
    assert [str(r.uri) for r in await mcp.list_resources()] == ["catalogo://produtos"]
    assert [t.uriTemplate for t in await mcp.list_resource_templates()] == [
        "produto://{produto_id}"
    ]
    assert {p.name for p in await mcp.list_prompts()} == {"recomendar_produto", "analisar_produto"}


# --- Tool 1: listar por categoria ---------------------------------------------


@pytest.mark.parametrize(
    ("categoria", "total"),
    [("game", 7), ("GAME", 7), ("livro", 6), ("maquiagem", 6), ("brinquedo", 7), ("outros", 7)],
)
async def test_listar_por_categoria(categoria, total):
    r = await chamar("listar_produtos_por_categoria", categoria=categoria)
    assert r["categoria"] == categoria.lower()
    assert r["total"] == total
    assert {"id", "nome", "categoria", "preco"} == set(r["produtos"][0])


async def test_categoria_inexistente_lista_validas():
    with pytest.raises(ToolError, match="Categorias válidas: brinquedo, game, livro"):
        await chamar("listar_produtos_por_categoria", categoria="eletrodomestico")


# --- Tool 2: produto por ID ---------------------------------------------------


async def test_obter_produto_por_id():
    r = await chamar("obter_produto", produto_id="p010")
    assert r["nome"] == "Headset gamer HX-70"
    assert r["categoria"] == "game"
    assert r["preco"] == 220.72
    assert r["preco_min"] <= r["preco"] <= r["preco_max"]


async def test_obter_produto_inexistente():
    with pytest.raises(ToolError, match="não encontrado"):
        await chamar("obter_produto", produto_id="P999")


# --- Tool 3: busca por nome ---------------------------------------------------


async def test_buscar_por_nome_ignora_acento():
    r = await chamar("buscar_produto_por_nome", nome="pelucia")
    assert [p["id"] for p in r["produtos"]] == ["P005"]


async def test_buscar_por_nome_varios_e_nenhum():
    r = await chamar("buscar_produto_por_nome", nome="gamer")
    assert [p["id"] for p in r["produtos"]] == ["P010", "P012", "P013"]
    vazio = await chamar("buscar_produto_por_nome", nome="geladeira")
    assert vazio["total"] == 0


# --- Tool 4: avaliação --------------------------------------------------------


async def test_avaliacao_por_id_e_por_nome():
    por_id = await chamar("obter_avaliacao_produto", produto="P010")
    por_nome = await chamar("obter_avaliacao_produto", produto="headset")
    assert por_id == por_nome
    assert por_id["nota_media"] == 3.54
    assert por_id["num_avaliacoes"] == 13
    assert sum(por_id["reclamacoes_por_classe"].values()) == 13


async def test_avaliacao_nome_ambiguo():
    with pytest.raises(ToolError, match="único produto"):
        await chamar("obter_avaliacao_produto", produto="gamer")


# --- Resources e prompts ------------------------------------------------------


async def test_resources():
    [catalogo] = await mcp.read_resource("catalogo://produtos")
    dados = json.loads(catalogo.content)
    assert len(dados["produtos"]) == 33
    assert dados["categorias"] == ["brinquedo", "game", "livro", "maquiagem", "outros"]
    [detalhe] = await mcp.read_resource("produto://P015")
    assert json.loads(detalhe.content)["nome"] == "Box trilogia O Reino Partido"


async def test_prompts():
    rec = await mcp.get_prompt(
        "recomendar_produto", {"necessidade": "presente para criança", "orcamento": "100"}
    )
    texto = rec.messages[0].content.text
    assert "presente para criança" in texto and "R$ 100" in texto
    ana = await mcp.get_prompt("analisar_produto", {"produto_id": "P013"})
    assert "P013" in ana.messages[0].content.text
