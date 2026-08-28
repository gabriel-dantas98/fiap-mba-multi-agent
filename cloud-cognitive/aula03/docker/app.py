"""
Versão FastAPI da API de produtos QC — mesmo comportamento da Function v2-blob.

Empacotada num container Docker para rodar no Azure Container Instances (ACI),
autenticando no Blob via Managed Identity user-assigned do ACI.
"""
import csv
import os

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Quantum Commerce — Catálogo API", version="1.0")

STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT_CATALOGO"]
CONTAINER       = "catalogo"
BLOB_NAME       = "produtos.csv"

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=_credential,
)


def carregar_produtos() -> list[dict]:
    blob_client = _blob_service.get_blob_client(container=CONTAINER, blob=BLOB_NAME)
    csv_content = blob_client.download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(csv_content.splitlines()))
    for r in rows:
        r["id"]      = int(r["id"])
        r["preco"]   = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "qc-catalogo",
        "source": "blob",
        "runtime": "container",
    }


@app.get("/produtos")
def listar_produtos(categoria: str | None = None, nome: str | None = None):
    try:
        produtos = carregar_produtos()
    except Exception as e:
        raise HTTPException(500, detail=f"falha ao acessar storage: {e!s}")

    cat = (categoria or "").lower().strip()
    nm  = (nome or "").lower().strip()

    resultado = produtos
    if cat:
        resultado = [p for p in resultado if p["categoria"].lower() == cat]
    if nm:
        resultado = [p for p in resultado if nm in p["nome"].lower()]

    return {"total": len(resultado), "produtos": resultado}
