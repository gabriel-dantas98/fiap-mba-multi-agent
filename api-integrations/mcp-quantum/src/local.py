"""Roda o mesmo servidor fora da Cloudflare.

uv run python src/local.py          # stdio (MCP Inspector / Claude Code)
uv run python src/local.py http     # streamable HTTP em http://127.0.0.1:8000/mcp
"""

import sys

from servidor import mcp

if __name__ == "__main__":
    transporte = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run("streamable-http" if transporte == "http" else "stdio")
