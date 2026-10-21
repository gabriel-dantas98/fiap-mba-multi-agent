import homepage

URL = "https://mcp-quantum.gabsdevops.workers.dev/mcp"


def test_pagina_usa_o_endpoint_e_lista_as_capacidades():
    pagina = homepage.renderizar(URL)
    assert f'<code id="endpoint">{URL}</code>' in pagina
    for nome in (
        "listar_produtos_por_categoria",
        "obter_produto",
        "buscar_produto_por_nome",
        "obter_avaliacao_produto",
        "catalogo://produtos",
        "produto://{produto_id}",
        "recomendar_produto",
        "analisar_produto",
    ):
        assert nome in pagina
    assert "__MCP_URL__" not in pagina and "__CAPACIDADES__" not in pagina


def test_pagina_tem_os_clientes_pedidos():
    pagina = homepage.renderizar(URL)
    for cliente in ("Cursor", "VS Code", "Claude Code", "Codex", "Antigravity", "ChatGPT"):
        assert f"<h3>{cliente}" in pagina
    assert "cursor://anysphere.cursor-deeplink/mcp/install" in pagina
    assert "vscode:mcp/install?" in pagina


def test_pagina_escapa_o_host():
    pagina = homepage.renderizar('https://x"><script>alert(1)</script>/mcp')
    assert "<script>alert(1)</script>" not in pagina
