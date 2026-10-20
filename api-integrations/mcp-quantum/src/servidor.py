"""Monta o servidor MCP do desafio Quantum.

Só configuração: as capacidades ficam em arquivos dedicados
(tools.py, resources.py, prompts.py), cada um com seu `registrar(mcp)`.
Roda igual no Cloudflare Worker (src/main.py) e localmente (src/local.py).
"""

import prompts
import resources
import tools
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

tools.registrar(mcp)
resources.registrar(mcp)
prompts.registrar(mcp)
