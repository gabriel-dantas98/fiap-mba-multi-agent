"""
Teste unitário da lógica de frete (Exercício 3.3 — pytest no pipeline CI/CD).

Só exercita `calcular_frete`, que é puro/determinístico (sem chamar Blob/Azure).
Precisa de STORAGE_ACCOUNT_CATALOGO no ambiente porque o módulo instancia o
BlobServiceClient no import — a instanciação não bate na rede, só monta a URL,
então um valor fake é suficiente para o teste rodar sem credenciais reais.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("STORAGE_ACCOUNT_CATALOGO", "fakestorageaccount")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2-full"))

from function_app import calcular_frete


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
    import pytest

    with pytest.raises(ValueError):
        calcular_frete("abc", "01311000", 1.0)
