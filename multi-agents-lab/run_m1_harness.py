#!/usr/bin/env python3
"""Roda Missao 1 com Caos e exige OURO 100 + bonus 20."""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent / "dutos-do-q"
sys.path.insert(0, str(RAIZ / "kit"))
os.environ["LLM_BACKEND"] = "mock"
os.chdir(RAIZ)

from lake import Lake  # noqa: E402
from contrato import carregar_contratos  # noqa: E402
import avaliacao, dutos, referencia  # noqa: E402


def main() -> int:
    contratos = carregar_contratos()
    lake = Lake(str(RAIZ / "lakehouse_harness")).zerar().criar_todas()
    inbox = dutos.preparar_inbox(RAIZ)
    resultado = avaliacao.avaliar_m1(
        lake,
        inbox,
        lambda l: referencia.pipeline(l, {"fontes": contratos}),
        com_caos=True,
        pasta_caos=RAIZ / "dados" / "caos",
    )
    score = float(resultado["score"])
    bonus = float(resultado["bonus_caos"])
    print(f"score={score} bonus_caos={bonus} total={score + bonus} medalha={resultado.get('medalha')}")
    assert score == 100.0, score
    assert bonus == 20.0, bonus
    out = avaliacao.salvar(resultado, str(RAIZ / "resultados"))
    print("salvo:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
