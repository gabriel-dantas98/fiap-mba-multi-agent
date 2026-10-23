"""Confere o leitor da planilha e o catálogo contra o openpyxl (referência independente)."""

import statistics
from collections import defaultdict

import openpyxl
import pytest
from catalogo import PLANILHA, PRODUTOS, carregar_chamados
from planilha import corrigir_texto


@pytest.fixture(scope="module")
def referencia():
    """Mesma planilha lida pelo openpyxl, com a mesma correção de acentos."""
    aba = openpyxl.load_workbook(PLANILHA, read_only=True, data_only=True).worksheets[0]
    linhas = [
        [corrigir_texto(c) if isinstance(c, str) else c for c in linha]
        for linha in aba.iter_rows(values_only=True)
    ]
    return [dict(zip(linhas[0], linha, strict=True)) for linha in linhas[1:]]


def test_planilha_tem_200_chamados_e_33_produtos(referencia):
    assert len(referencia) == 200
    assert len({c["id_produto"] for c in referencia}) == 33 == len(PRODUTOS)


def test_leitor_stdlib_bate_com_openpyxl(referencia):
    nossos = carregar_chamados()
    assert len(nossos) == len(referencia)
    for nosso, ref in zip(nossos, referencia, strict=True):
        for coluna in ("id_produto", "nome_produto", "categoria_produto", "vendedor", "classe"):
            assert nosso[coluna] == ref[coluna]
        assert nosso["preco"] == pytest.approx(ref["preco"])
        assert nosso["avaliacao_produto"] == pytest.approx(ref["avaliacao_produto"])


def test_acentos_corrigidos():
    nomes = {p["nome"] for p in PRODUTOS}
    assert "Quebra-cabeça 1000 peças Paisagem Alpina" in nomes
    assert not any("Ã" in n for n in nomes)


def test_agregados_batem_com_a_planilha(referencia):
    por_produto = defaultdict(list)
    for c in referencia:
        por_produto[c["id_produto"]].append(c)
    for p in PRODUTOS:
        linhas = por_produto[p["id"]]
        assert p["nome"] == linhas[0]["nome_produto"]
        assert p["num_avaliacoes"] == len(linhas)
        assert p["nota"] == round(statistics.mean(r["avaliacao_produto"] for r in linhas), 2)
        assert p["preco"] == round(statistics.mean(r["preco"] for r in linhas), 2)
        assert sum(p["reclamacoes_por_classe"].values()) == len(linhas)
