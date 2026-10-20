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


async def test_listar_por_categoria_ignora_acento_e_caixa():
    r = await chamar("listar_produtos_por_categoria", categoria="informatica")
    assert r["categoria"] == "Informática"
    assert r["total"] == 5
    assert {"id", "nome", "categoria", "preco"} <= set(r["produtos"][0])


async def test_categoria_inexistente_lista_validas():
    with pytest.raises(ToolError, match="Categorias válidas"):
        await chamar("listar_produtos_por_categoria", categoria="Brinquedos")


async def test_obter_produto_por_id():
    r = await chamar("obter_produto", produto_id="p006")
    assert r["nome"] == "Smartphone Quantum X"
    assert r["categoria"] == "Celulares"
    assert r["preco"] == 5299.0


async def test_obter_produto_inexistente():
    with pytest.raises(ToolError, match="não encontrado"):
        await chamar("obter_produto", produto_id="P999")


async def test_buscar_por_nome():
    r = await chamar("buscar_produto_por_nome", nome="quantum x")
    assert [p["id"] for p in r["produtos"]] == ["P006", "P009"]
    vazio = await chamar("buscar_produto_por_nome", nome="geladeira")
    assert vazio["total"] == 0


async def test_avaliacao_por_id_e_por_nome():
    por_id = await chamar("obter_avaliacao_produto", produto="P023")
    por_nome = await chamar("obter_avaliacao_produto", produto="console")
    assert por_id == por_nome
    assert por_id["nota"] == 4.9
    assert por_id["num_avaliacoes"] == 5210


async def test_avaliacao_nome_ambiguo():
    with pytest.raises(ToolError, match="único produto"):
        await chamar("obter_avaliacao_produto", produto="notebook")


async def test_resources():
    [catalogo] = await mcp.read_resource("catalogo://produtos")
    dados = json.loads(catalogo.content)
    assert len(dados["produtos"]) == 25
    [detalhe] = await mcp.read_resource("produto://P010")
    assert json.loads(detalhe.content)["nome"] == "Fone Bluetooth ANC"


async def test_prompts():
    rec = await mcp.get_prompt(
        "recomendar_produto", {"necessidade": "fone para trabalho remoto", "orcamento": "1000"}
    )
    texto = rec.messages[0].content.text
    assert "fone para trabalho remoto" in texto and "R$ 1000" in texto
    ana = await mcp.get_prompt("analisar_produto", {"produto_id": "P017"})
    assert "P017" in ana.messages[0].content.text
