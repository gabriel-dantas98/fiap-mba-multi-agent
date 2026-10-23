"""E2E: cliente MCP de verdade contra o servidor publicado.

    MCP_URL=https://mcp-quantum.gabsdevops.workers.dev/mcp MCP_TOKEN=$(cat .token) \\
        uv run pytest tests/test_e2e.py -v
"""

import json
import os

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = os.environ.get("MCP_URL")
TOKEN = os.environ.get("MCP_TOKEN", "")

pytestmark = pytest.mark.skipif(not URL, reason="defina MCP_URL (e MCP_TOKEN) para rodar o E2E")


async def sessao_e(fn):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with (
        streamablehttp_client(URL, headers=headers) as (leitura, escrita, _),
        ClientSession(leitura, escrita) as sessao,
    ):
        info = await sessao.initialize()
        assert info.serverInfo.name == "quantum-catalogo"
        return await fn(sessao)


def texto_json(resultado):
    assert not resultado.isError, resultado.content
    return json.loads(resultado.content[0].text)


@pytest.mark.parametrize(
    ("headers", "status"),
    [({}, 401), ({"Authorization": "Bearer token-errado"}, 401)],
)
def test_sem_token_valido_recebe_401(headers, status):
    r = httpx.post(URL, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=headers)
    assert r.status_code == status
    assert r.headers["www-authenticate"].startswith("Bearer")


def test_homepage_publica_sem_token():
    r = httpx.get(URL.rsplit("/mcp", 1)[0] + "/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert f'<code id="endpoint">{URL}</code>' in r.text


def test_rota_fora_de_mcp_recebe_404():
    assert httpx.get(URL.rsplit("/mcp", 1)[0] + "/admin").status_code == 404


async def test_lista_capacidades():
    async def fn(s):
        tools = {t.name for t in (await s.list_tools()).tools}
        resources = [str(r.uri) for r in (await s.list_resources()).resources]
        templates = [t.uriTemplate for t in (await s.list_resource_templates()).resourceTemplates]
        prompts = {p.name for p in (await s.list_prompts()).prompts}
        return tools, resources, templates, prompts

    tools, resources, templates, prompts = await sessao_e(fn)
    assert len(tools) == 4
    assert resources == ["catalogo://produtos"]
    assert templates == ["produto://{produto_id}"]
    assert prompts == {"recomendar_produto", "analisar_produto"}


async def test_tool_1_listar_por_categoria():
    r = await sessao_e(
        lambda s: s.call_tool("listar_produtos_por_categoria", {"categoria": "livro"})
    )
    dados = texto_json(r)
    assert dados["total"] == 6


async def test_tool_2_obter_produto():
    dados = texto_json(
        await sessao_e(lambda s: s.call_tool("obter_produto", {"produto_id": "P013"}))
    )
    assert dados["nome"] == "Cadeira gamer ErgoMax"
    assert dados["preco"] == 900.39


async def test_tool_3_buscar_por_nome():
    dados = texto_json(
        await sessao_e(lambda s: s.call_tool("buscar_produto_por_nome", {"nome": "batom"}))
    )
    assert [p["id"] for p in dados["produtos"]] == ["P023"]


async def test_tool_4_avaliacao():
    dados = texto_json(
        await sessao_e(lambda s: s.call_tool("obter_avaliacao_produto", {"produto": "headset"}))
    )
    assert dados["nota_media"] == 3.54
    assert dados["num_avaliacoes"] == 13


async def test_tool_com_erro_volta_iserror():
    r = await sessao_e(lambda s: s.call_tool("obter_produto", {"produto_id": "P999"}))
    assert r.isError
    assert "não encontrado" in r.content[0].text


async def test_resources():
    async def fn(s):
        return (
            await s.read_resource("catalogo://produtos"),
            await s.read_resource("produto://P001"),
        )

    catalogo, detalhe = await sessao_e(fn)
    assert len(json.loads(catalogo.contents[0].text)["produtos"]) == 33
    assert json.loads(detalhe.contents[0].text)["nome"] == "Boneca de pano Amélia"


async def test_prompt():
    r = await sessao_e(lambda s: s.get_prompt("analisar_produto", arguments={"produto_id": "P027"}))
    assert "P027" in r.messages[0].content.text
