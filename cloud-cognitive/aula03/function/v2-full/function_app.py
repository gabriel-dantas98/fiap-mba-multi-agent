"""
Function HTTP da Quantum Commerce — versão L₂ + Exercício 2.1.

Duas tools no MESMO Function App (mesmo processo, mesmo plano FC1):

- /api/produtos  — lê produtos.csv do Blob Storage via Managed Identity (L₂ da aula).
- /api/frete     — calcula frete determinístico por CEP + peso (Exercício 2.1).

Justificativa de "mesmo App" está em entrega-grupo-aula03.md (2.1-e). Resumo:
tráfego parecido (dezenas de milhares/mês), sem necessidade de scaling/runtime
diferentes entre as duas, sem segredo exclusivo de uma tool só — não paga o
custo operacional de administrar dois Function Apps para separar 2 endpoints
HTTP do mesmo domínio (catálogo/logística da QC).

SEM credenciais no código — autenticação via DefaultAzureCredential que detecta
a Managed Identity SystemAssigned do Function App em runtime.

Variável de ambiente esperada (configurada pelo Terraform):
    STORAGE_ACCOUNT_CATALOGO — nome do Storage Account com o container 'catalogo'
"""

import csv
import json
import logging
import math
import os
import re

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT_CATALOGO"]
CONTAINER = "catalogo"
BLOB_NAME = "produtos.csv"

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=_credential,
)


def carregar_produtos() -> list[dict]:
    """Baixa produtos.csv do Blob e converte em lista de dicts."""
    blob_client = _blob_service.get_blob_client(container=CONTAINER, blob=BLOB_NAME)
    csv_content = blob_client.download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(csv_content.splitlines()))
    for r in rows:
        r["id"] = int(r["id"])
        r["preco"] = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


@app.route(route="produtos", methods=["GET"])
def listar_produtos(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/produtos?categoria=moveis&nome=cadeira"""
    logging.info("Endpoint /produtos chamado")

    try:
        produtos = carregar_produtos()
    except Exception:
        logging.exception("Falha ao carregar produtos do Blob")
        return func.HttpResponse(
            json.dumps({"erro": "falha ao acessar storage"}),
            mimetype="application/json",
            status_code=500,
        )

    categoria = (req.params.get("categoria") or "").lower().strip()
    nome = (req.params.get("nome") or "").lower().strip()

    resultado = produtos
    if categoria:
        resultado = [p for p in resultado if p["categoria"].lower() == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]

    return func.HttpResponse(
        json.dumps({"total": len(resultado), "produtos": resultado}, ensure_ascii=False),
        mimetype="application/json",
        status_code=200,
    )


# ---------------------------------------------------------------------------
# Exercício 2.1 — Nova tool: cálculo de frete.
#
# Determinístico e sem dependência externa de propósito: nada de API de CEP
# (Correios/ViaCEP) para não introduzir rede + custo + ponto de falha numa
# função que a spec pede "pode ser determinística". Aproxima distância pelos
# 5 primeiros dígitos do CEP (faixa de região dos Correios) e cobra por km
# aproximado + por kg. É uma tabela de tarifa simplificada, não uma cotação
# real de transportadora — documentado assim na entrega para não confundir
# leitor achando que é produção.
# ---------------------------------------------------------------------------
PRECO_BASE = 12.00  # R$ fixo por remessa
PRECO_POR_KM = 0.012  # R$ por "km" aproximado
PRECO_POR_KG = 3.50  # R$ por kg
DIAS_BASE = 2  # prazo mínimo (mesma faixa de CEP)
KM_POR_DIA_EXTRA = 800  # a cada N "km" aproximados, +1 dia útil


def _normaliza_cep(cep: str) -> int:
    if re.fullmatch(r"\d{8}|\d{5}-\d{3}", cep) is None:
        raise ValueError(f"CEP inválido: {cep!r}")
    digitos = cep.replace("-", "")
    return int(digitos[:5])


def calcular_frete(cep_origem: str, cep_destino: str, peso_kg: float) -> dict:
    if not math.isfinite(peso_kg) or peso_kg <= 0:
        raise ValueError("peso deve ser um número positivo e finito")

    origem = _normaliza_cep(cep_origem)
    destino = _normaliza_cep(cep_destino)

    distancia_aprox_km = abs(destino - origem) * 0.045  # fator empírico de calibração
    distancia_aprox_km = max(distancia_aprox_km, 5.0)  # piso: mesma cidade ainda custa algo
    distancia_aprox_km = min(
        distancia_aprox_km, 4000.0
    )  # teto: maior distância plausível no Brasil

    valor = PRECO_BASE + (distancia_aprox_km * PRECO_POR_KM) + (peso_kg * PRECO_POR_KG)
    dias = DIAS_BASE + int(distancia_aprox_km // KM_POR_DIA_EXTRA)

    return {
        "cep_origem": cep_origem,
        "cep_destino": cep_destino,
        "peso_kg": peso_kg,
        "distancia_aproximada_km": round(distancia_aprox_km, 1),
        "valor_reais": round(valor, 2),
        "prazo_dias_uteis": dias,
    }


@app.route(route="frete", methods=["GET"])
def frete(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/frete?cep_origem=01310930&cep_destino=20040020&peso=2.5"""
    logging.info("Endpoint /frete chamado")

    cep_origem = req.params.get("cep_origem")
    cep_destino = req.params.get("cep_destino")
    peso_raw = req.params.get("peso")

    if not cep_origem or not cep_destino or not peso_raw:
        return func.HttpResponse(
            json.dumps({"erro": "parâmetros obrigatórios: cep_origem, cep_destino, peso"}),
            mimetype="application/json",
            status_code=400,
        )

    try:
        peso_kg = float(peso_raw)
        resultado = calcular_frete(cep_origem, cep_destino, peso_kg)
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            mimetype="application/json",
            status_code=400,
        )

    return func.HttpResponse(
        json.dumps(resultado, ensure_ascii=False),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "service": "qc-catalogo-frete", "source": "blob"}),
        mimetype="application/json",
    )
