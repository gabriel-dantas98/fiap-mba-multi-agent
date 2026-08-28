"""
Function HTTP da Quantum Commerce — versão L₁ (mock data).
Sem dependências externas, sem credenciais. Bom para validar que o deploy funciona.

No L₂ vamos plugar no Blob do catálogo (criado nesta aula) via Managed Identity (versão em ../v2-blob/).
"""
import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Mock inicial — depois substituído pelo Blob na v2-blob/
PRODUTOS_MOCK = [
    {"id": 1, "nome": "Cadeira Ergonômica DXRacer", "categoria": "moveis",          "preco": 1499.90},
    {"id": 2, "nome": "Notebook Dell Inspiron 15",  "categoria": "eletronicos",     "preco": 4299.00},
    {"id": 3, "nome": "Cafeteira Nespresso Mini",   "categoria": "eletrodomesticos","preco": 499.00},
    {"id": 4, "nome": "Tênis Nike Air Zoom Pegasus","categoria": "calcados",        "preco": 799.90},
    {"id": 5, "nome": "Smartphone Galaxy S24",      "categoria": "eletronicos",     "preco": 3999.00},
]


@app.route(route="produtos", methods=["GET"])
def listar_produtos(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/produtos?categoria=eletronicos&nome=galaxy"""
    logging.info("Endpoint /produtos chamado (mock)")

    categoria = (req.params.get("categoria") or "").lower().strip()
    nome      = (req.params.get("nome")      or "").lower().strip()

    resultado = PRODUTOS_MOCK
    if categoria:
        resultado = [p for p in resultado if p["categoria"] == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]

    return func.HttpResponse(
        json.dumps({"total": len(resultado), "produtos": resultado}, ensure_ascii=False),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "service": "qc-catalogo", "source": "mock"}),
        mimetype="application/json",
    )
