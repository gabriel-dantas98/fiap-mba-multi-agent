"""Leitor mínimo de .xlsx só com a biblioteca padrão.

Um .xlsx é um ZIP com XML dentro. Ler direto com zipfile + ElementTree evita
o openpyxl no bundle do Worker (o plano free limita o bundle a 3 MB).
Lê apenas a primeira aba; números vêm como float, textos como str.
"""

import io
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _coluna(ref: str) -> int:
    """'A1' -> 0, 'Q201' -> 16."""
    letras = re.match(r"[A-Z]+", ref).group()
    indice = 0
    for letra in letras:
        indice = indice * 26 + (ord(letra) - 64)
    return indice - 1


def _texto(no) -> str:
    # Rich text quebra a string em vários <t>; junta tudo.
    return "".join(t.text or "" for t in no.iter(f"{{{NS['m']}}}t"))


def corrigir_texto(valor: str) -> str:
    """A planilha veio com UTF-8 lido como Latin-1 ('PreÃ§o' -> 'Preço')."""
    try:
        return valor.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return valor


def _valor(celula, compartilhadas: list[str]):
    tipo = celula.get("t")
    if tipo == "inlineStr":
        return corrigir_texto(_texto(celula))
    bruto = celula.findtext("m:v", default=None, namespaces=NS)
    if bruto is None:
        return None
    if tipo == "s":
        return compartilhadas[int(bruto)]
    if tipo in ("str", "e"):
        return corrigir_texto(bruto)
    if tipo == "b":
        return bruto == "1"
    return float(bruto)


def ler_linhas(conteudo: bytes) -> list[dict]:
    """Primeira aba como lista de dicts, usando a linha 1 como cabeçalho."""
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        compartilhadas = []
        if "xl/sharedStrings.xml" in z.namelist():
            raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
            compartilhadas = [corrigir_texto(_texto(si)) for si in raiz.findall("m:si", NS)]
        aba = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    linhas = []
    for linha in aba.iterfind("m:sheetData/m:row", NS):
        valores = {}
        for celula in linha.iterfind("m:c", NS):
            valores[_coluna(celula.get("r"))] = _valor(celula, compartilhadas)
        if valores:
            largura = max(valores) + 1
            linhas.append([valores.get(i) for i in range(largura)])

    cabecalho = [str(c).strip() for c in linhas[0]]
    return [dict(zip(cabecalho, linha, strict=False)) for linha in linhas[1:] if any(linha)]
