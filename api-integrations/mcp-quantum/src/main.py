"""Entrypoint do Cloudflare Python Worker.

Os imports ficam no topo de propósito: o deploy tira um snapshot de memória
com o MCP já carregado. Importar dentro do fetch custava ~2 s de CPU por cold
start e estourava o limite do plano free (erro 1102).
"""

import hmac

from servidor import mcp
from workers import Response, WorkerEntrypoint, asgi


def _autorizado(request, token: str) -> bool:
    enviado = request.headers.get("authorization") or ""
    return bool(token) and hmac.compare_digest(enviado.encode(), f"Bearer {token}".encode())


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        caminho = request.url.split("?", 1)[0].split("/", 3)[-1]
        if caminho != "mcp":
            return Response("not found", status=404)
        if not _autorizado(request, getattr(self.env, "MCP_TOKEN", "")):
            return Response(
                "unauthorized",
                status=401,
                headers={"WWW-Authenticate": 'Bearer realm="mcp-quantum"'},
            )
        # Stateless: o adaptador ASGI roda o lifespan a cada request e o session
        # manager do SDK só aceita run() uma vez, então cada request ganha um novo.
        mcp._session_manager = None
        return await asgi.fetch(mcp.streamable_http_app(), request, self.env)
