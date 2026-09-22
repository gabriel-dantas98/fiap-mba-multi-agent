"""aula.py — utilidades de sala: mostrar o enunciado dentro do notebook e conferir o estado do time."""
from __future__ import annotations

import re
from pathlib import Path


def _secao(texto: str, titulo: str) -> str:
    """Recorta uma seção de nível 2 do markdown, do '## <titulo>' até o próximo '## '."""
    linhas = texto.splitlines()
    inicio = next((i for i, l in enumerate(linhas)
                   if l.startswith("## ") and titulo.lower() in l.lower()), None)
    if inicio is None:
        return texto
    fim = next((j for j in range(inicio + 1, len(linhas)) if linhas[j].startswith("## ")), len(linhas))
    return "\n".join(linhas[inicio:fim]).strip()


def briefing(caminho_kit, secao: str | None = None, arquivo: str = "ENUNCIADO.md"):
    """Mostra o enunciado (ou uma seção dele) formatado dentro do notebook."""
    texto = (Path(caminho_kit) / arquivo).read_text(encoding="utf-8")
    if secao:
        texto = _secao(texto, secao)
    try:
        from IPython.display import Markdown, display
        display(Markdown(texto))
    except Exception:
        print(texto)


def ficha(caminho_kit, bloco: int):
    """Mostra as perguntas da ficha de decisão do bloco."""
    briefing(caminho_kit, f"Bloco {bloco}", arquivo="FICHA.md")


def situacao(lake, contratos_dir=None):
    """Um retrato rápido do estado do trabalho: lacunas abertas e o que já está nas tabelas."""
    from contrato import pendencias
    faltando = pendencias()
    print(f"lacunas do contrato ainda abertas: {len(faltando)}")
    for f in faltando:
        print(f"   {f['fonte']:<12} {f['campo']}")
    print()
    print(lake.resumo().to_string(index=False))
    return faltando
