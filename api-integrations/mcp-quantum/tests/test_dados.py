"""Confere o catálogo gerado contra a planilha original (fonte de verdade)."""

import statistics
import sys
from collections import defaultdict
from pathlib import Path

import pytest
from dados import PRODUTOS

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from gerar_dados import ler_xlsx  # noqa: E402

XLSX = RAIZ / "dados" / "quantum-commerce-chamados.xlsx"


@pytest.fixture(scope="module")
def chamados():
    return ler_xlsx(XLSX)


def test_planilha_tem_200_chamados_e_33_produtos(chamados):
    assert len(chamados) == 200
    assert len({c["id_produto"] for c in chamados}) == 33 == len(PRODUTOS)


def test_acentos_corrigidos(chamados):
    nomes = {c["nome_produto"] for c in chamados}
    assert "Quebra-cabeça 1000 peças Paisagem Alpina" in nomes
    assert not any("Ã" in n for n in nomes)


def test_agregados_batem_com_a_planilha(chamados):
    por_produto = defaultdict(list)
    for c in chamados:
        por_produto[c["id_produto"]].append(c)
    for p in PRODUTOS:
        linhas = por_produto[p["id"]]
        assert p["nome"] == linhas[0]["nome_produto"]
        assert p["num_avaliacoes"] == len(linhas)
        assert p["nota"] == round(statistics.mean(r["avaliacao_produto"] for r in linhas), 2)
        assert p["preco"] == round(statistics.mean(r["preco"] for r in linhas), 2)
        assert sum(p["reclamacoes_por_classe"].values()) == len(linhas)
