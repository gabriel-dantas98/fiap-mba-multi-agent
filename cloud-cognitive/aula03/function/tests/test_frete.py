"""Testes da lógica e do contrato HTTP de frete (Exercício 3.3).

Não chamam Blob/Azure. `STORAGE_ACCOUNT_CATALOGO` é necessário porque o módulo
instancia o BlobServiceClient no import; um valor fake basta, sem acesso à rede.
"""

import json
import os
import sys
from pathlib import Path

import azure.functions as func
import pytest

os.environ.setdefault("STORAGE_ACCOUNT_CATALOGO", "fakestorageaccount")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2-full"))

from function_app import calcular_frete, frete


def _http_request(params: dict[str, str]) -> func.HttpRequest:
    return func.HttpRequest(
        method="GET",
        url="http://localhost/api/frete",
        params=params,
        body=None,
    )


def test_frete_mesmo_cep_tem_piso_minimo():
    resultado = calcular_frete("01310930", "01310930", 1.0)
    assert resultado["distancia_aproximada_km"] == 5.0
    assert resultado["prazo_dias_uteis"] == 2


def test_frete_cresce_com_peso():
    curto = calcular_frete("01310930", "01311000", 1.0)
    pesado = calcular_frete("01310930", "01311000", 10.0)
    assert pesado["valor_reais"] > curto["valor_reais"]


def test_frete_cresce_com_distancia():
    perto = calcular_frete("01310930", "01311000", 1.0)
    longe = calcular_frete("01310930", "70040010", 1.0)
    assert longe["distancia_aproximada_km"] > perto["distancia_aproximada_km"]
    assert longe["valor_reais"] > perto["valor_reais"]


def test_frete_cep_invalido_levanta_erro():
    with pytest.raises(ValueError):
        calcular_frete("abc", "01311000", 1.0)


@pytest.mark.parametrize("cep", ["01310", "013109300", "01310-93", "abc01310930", "01310.930"])
def test_frete_rejeita_cep_fora_do_formato(cep):
    with pytest.raises(ValueError):
        calcular_frete(cep, "01311000", 1.0)


@pytest.mark.parametrize("peso", [0, -1, float("nan"), float("inf"), float("-inf")])
def test_frete_rejeita_peso_invalido(peso):
    with pytest.raises(ValueError):
        calcular_frete("01310930", "01311000", peso)


def test_endpoint_frete_retorna_contrato_json():
    response = frete(
        _http_request(
            {
                "cep_origem": "01310930",
                "cep_destino": "20040020",
                "peso": "2.5",
            }
        )
    )

    assert response.status_code == 200
    assert json.loads(response.get_body()) == {
        "cep_origem": "01310930",
        "cep_destino": "20040020",
        "peso_kg": 2.5,
        "distancia_aproximada_km": 842.9,
        "valor_reais": 30.86,
        "prazo_dias_uteis": 3,
    }


@pytest.mark.parametrize("peso", ["nan", "inf", "1e309"])
def test_endpoint_frete_rejeita_peso_nao_finito(peso):
    response = frete(
        _http_request(
            {
                "cep_origem": "01310930",
                "cep_destino": "20040020",
                "peso": peso,
            }
        )
    )

    assert response.status_code == 400
    assert json.loads(response.get_body()) == {"erro": "peso deve ser um número positivo e finito"}
