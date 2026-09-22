#!/usr/bin/env python3
"""Executa o notebook Bloco 1 E2E e grava outputs no .ipynb.

Uso (a partir da raiz do repo ou de multi-agents-lab/):

  LLM_BACKEND=mock python multi-agents-lab/run_notebook_e2e.py
  LLM_BACKEND=hf   python multi-agents-lab/run_notebook_e2e.py

Saida: multi-agents-lab/entregas/01_bloco1_batch_EXECUTADO_<backend>.ipynb
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import papermill as pm

LAB = Path(__file__).resolve().parent
BACKEND = os.environ.get("LLM_BACKEND", "mock")
os.environ["LLM_BACKEND"] = BACKEND

IN_NB = LAB / "01_bloco1_batch_LOCAL.ipynb"
OUT_DIR = LAB / "entregas"
OUT_NB = OUT_DIR / f"01_bloco1_batch_EXECUTADO_{BACKEND}.ipynb"


def main() -> int:
    if not IN_NB.exists():
        print("missing", IN_NB, file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # limpa artefatos de runs anteriores do kit
    for name in ("lakehouse_harness", "lakehouse", "trabalho", "resultados", "_validacao"):
        p = LAB / "dutos-do-q" / name
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)

    print("input :", IN_NB)
    print("output:", OUT_NB)
    print("backend:", BACKEND)
    print("cwd   :", LAB)

    pm.execute_notebook(
        input_path=str(IN_NB),
        output_path=str(OUT_NB),
        kernel_name="fiap-mba",
        cwd=str(LAB),
        progress_bar=True,
        log_output=True,
        stdout_file=sys.stdout,
        stderr_file=sys.stderr,
    )

    # sanity: harness score no stdout ja saiu; confere JSON se existir
    res = LAB / "dutos-do-q" / "resultados" / "resultado_m1.json"
    if res.exists():
        data = json.loads(res.read_text())
        score = data.get("score") or data.get("score_total")
        print("resultado_m1.json keys:", sorted(data.keys())[:12])
        print("resultado_m1.json score field:", score)
    print("DONE", OUT_NB, "size", OUT_NB.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
