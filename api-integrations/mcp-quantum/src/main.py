"""Entrypoint do Cloudflare Python Worker.

Os imports ficam no topo de propósito: o deploy tira um snapshot de memória
com o MCP já carregado. Importar dentro do fetch custava ~2 s de CPU por cold
start e estourava o limite do plano free (erro 1102).
"""

import hmac
from urllib.parse import urlsplit

from servidor import mcp
from workers import Response, WorkerEntrypoint, asgi

import homepage

# A homepage não carrega nada externo: CSP fechada, só o CSS/JS inline dela.
HEADERS_HOMEPAGE = {
    "content-type": "text/html; charset=utf-8",
    "content-security-policy": (
        "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "cache-control": "public, max-age=300",
}


def _autorizado(request, token: str) -> bool:
    enviado = request.headers.get("authorization") or ""
    return bool(token) and hmac.compare_digest(enviado.encode(), f"Bearer {token}".encode())


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlsplit(request.url)
        caminho = url.path.strip("/")
        if caminho == "" and request.method == "GET":
            pagina = homepage.renderizar(f"{url.scheme}://{url.netloc}/mcp")
            return Response(pagina, headers=HEADERS_HOMEPAGE)
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
