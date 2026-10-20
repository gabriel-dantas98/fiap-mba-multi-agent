"""Converte dados/produtos.csv em src/dados.py.

O Python Worker não lê arquivos soltos do disco, então o catálogo vira um
módulo Python embutido no bundle. Rodar sempre que o CSV mudar:

    uv run python scripts/gerar_dados.py [caminho/do.csv]
"""

import csv
import pprint
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_PADRAO = RAIZ / "dados" / "produtos.csv"
SAIDA = RAIZ / "src" / "dados.py"

# Nome canônico -> cabeçalhos aceitos no CSV (comparados sem acento/caixa).
ALIASES = {
    "id": ["id", "produto_id", "id_produto", "product_id", "sku", "codigo"],
    "nome": ["nome", "produto", "nome_produto", "name", "title", "titulo"],
    "categoria": ["categoria", "category", "departamento"],
    "preco": ["preco", "valor", "price", "preco_unitario"],
    "nota": ["nota", "avaliacao", "rating", "review", "nota_media", "score"],
    "num_avaliacoes": ["num_avaliacoes", "qtd_avaliacoes", "reviews", "rating_count", "votos"],
    "descricao": ["descricao", "description", "detalhes"],
}
OBRIGATORIAS = ["id", "nome", "categoria", "preco"]


def _chave(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.strip().lower().replace(" ", "_")


def _numero(valor: str) -> float | None:
    valor = (valor or "").strip().replace("R$", "").strip()
    if not valor:
        return None
    if "," in valor and "." in valor:
        valor = valor.replace(".", "").replace(",", ".")
    elif "," in valor:
        valor = valor.replace(",", ".")
    return float(valor)


def mapear_colunas(cabecalho: list[str]) -> dict[str, str]:
    por_chave = {_chave(c): c for c in cabecalho}
    mapa = {}
    for canonico, aceitos in ALIASES.items():
        for alias in aceitos:
            if alias in por_chave:
                mapa[canonico] = por_chave[alias]
                break
    faltando = [c for c in OBRIGATORIAS if c not in mapa]
    if faltando:
        raise SystemExit(f"CSV sem colunas obrigatórias {faltando}. Cabeçalho: {cabecalho}")
    return mapa


def carregar(caminho: Path) -> list[dict]:
    amostra = caminho.read_text(encoding="utf-8-sig")
    dialeto = csv.Sniffer().sniff(amostra.splitlines()[0], delimiters=",;\t")
    leitor = csv.DictReader(amostra.splitlines(), delimiter=dialeto.delimiter)
    mapa = mapear_colunas(leitor.fieldnames or [])
    produtos = []
    for linha in leitor:
        produto = {
            "id": linha[mapa["id"]].strip(),
            "nome": linha[mapa["nome"]].strip(),
            "categoria": linha[mapa["categoria"]].strip(),
            "preco": _numero(linha[mapa["preco"]]),
        }
        for opcional in ("nota", "num_avaliacoes", "descricao"):
            if opcional in mapa:
                bruto = linha[mapa[opcional]]
                produto[opcional] = bruto.strip() if opcional == "descricao" else _numero(bruto)
        if produto.get("num_avaliacoes") is not None:
            produto["num_avaliacoes"] = int(produto["num_avaliacoes"])
        produtos.append(produto)
    return produtos


def main() -> None:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PADRAO
    produtos = carregar(caminho)
    corpo = pprint.pformat(produtos, width=100, sort_dicts=False)
    SAIDA.write_text(
        f'"""Gerado por scripts/gerar_dados.py a partir de {caminho.name}. Não editar."""\n\n'
        f"PRODUTOS = {corpo}\n",
        encoding="utf-8",
    )
    print(f"{len(produtos)} produtos -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
