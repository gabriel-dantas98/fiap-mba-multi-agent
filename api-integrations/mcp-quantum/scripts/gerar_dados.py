"""Converte a base de chamados da Quantum Commerce em src/dados.py.

A fonte (dados/quantum-commerce-chamados.xlsx ou .csv) tem uma linha por
reclamação, com os dados do produto repetidos em cada linha. Nome, descrição e
categoria são fixos por produto; preço, vendedor e avaliação variam porque o
mesmo produto é vendido por vários vendedores (marketplace). Por isso o
catálogo agrega por id_produto:

- preço: média das ofertas + faixa mínimo/máximo
- nota: média das avaliacao_produto + mínimo/máximo/quantidade
- reclamações: contagem por classe

O Python Worker não lê arquivos soltos do disco, então o resultado vira um
módulo Python embutido no bundle. Rodar sempre que a fonte mudar:

    uv run python scripts/gerar_dados.py [caminho/da/fonte.xlsx|.csv]
"""

import csv
import pprint
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE_PADRAO = RAIZ / "dados" / "quantum-commerce-chamados.xlsx"
CSV_LIMPO = RAIZ / "dados" / "quantum-commerce-chamados.csv"
SAIDA = RAIZ / "src" / "dados.py"

COLUNAS = [
    "id_produto",
    "nome_produto",
    "descricao_produto",
    "categoria_produto",
    "preco",
    "vendedor",
    "tipo_vendedor",
    "avaliacao_produto",
    "classe",
]


def corrigir_texto(valor):
    """A planilha veio com UTF-8 lido como Latin-1 ('PreÃ§o' -> 'Preço')."""
    if not isinstance(valor, str):
        return valor
    try:
        return valor.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return valor


def ler_xlsx(caminho: Path) -> list[dict]:
    import openpyxl

    planilha = openpyxl.load_workbook(caminho, read_only=True, data_only=True).worksheets[0]
    linhas = [[corrigir_texto(c) for c in linha] for linha in planilha.iter_rows(values_only=True)]
    cabecalho = linhas[0]
    return [dict(zip(cabecalho, linha, strict=True)) for linha in linhas[1:] if any(linha)]


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return [{k: corrigir_texto(v) for k, v in linha.items()} for linha in csv.DictReader(f)]


def salvar_csv_limpo(registros: list[dict]) -> None:
    with CSV_LIMPO.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(registros[0]))
        escritor.writeheader()
        escritor.writerows(registros)


def agregar(registros: list[dict]) -> list[dict]:
    faltando = [c for c in COLUNAS if c not in registros[0]]
    if faltando:
        raise SystemExit(f"Fonte sem as colunas {faltando}.")

    por_produto = defaultdict(list)
    for r in registros:
        por_produto[str(r["id_produto"]).strip()].append(r)

    produtos = []
    for produto_id in sorted(por_produto):
        linhas = por_produto[produto_id]
        base = linhas[0]
        precos = [float(r["preco"]) for r in linhas]
        notas = [float(r["avaliacao_produto"]) for r in linhas]
        vendedores = Counter(f"{r['vendedor']} ({r['tipo_vendedor']})" for r in linhas)
        produtos.append(
            {
                "id": produto_id,
                "nome": base["nome_produto"].strip(),
                "categoria": base["categoria_produto"].strip(),
                "descricao": base["descricao_produto"].strip(),
                "preco": round(statistics.mean(precos), 2),
                "preco_min": min(precos),
                "preco_max": max(precos),
                "vendedores": sorted(vendedores),
                "nota": round(statistics.mean(notas), 2),
                "nota_min": min(notas),
                "nota_max": max(notas),
                "num_avaliacoes": len(notas),
                "reclamacoes_por_classe": dict(Counter(r["classe"] for r in linhas).most_common()),
            }
        )
    return produtos


def main() -> None:
    fonte = Path(sys.argv[1]) if len(sys.argv) > 1 else FONTE_PADRAO
    registros = ler_xlsx(fonte) if fonte.suffix.lower() == ".xlsx" else ler_csv(fonte)
    if fonte.suffix.lower() == ".xlsx":
        salvar_csv_limpo(registros)
    produtos = agregar(registros)
    corpo = pprint.pformat(produtos, width=100, sort_dicts=False)
    SAIDA.write_text(
        f'"""Gerado por scripts/gerar_dados.py a partir de {fonte.name}. Não editar."""\n\n'
        f"PRODUTOS = {corpo}\n",
        encoding="utf-8",
    )
    print(f"{len(registros)} chamados -> {len(produtos)} produtos -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
