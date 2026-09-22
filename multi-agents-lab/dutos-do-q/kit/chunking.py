"""Chunking por parágrafo com título — a estratégia vencedora da Operação Q (decisão já tomada lá).
Aqui ela importa por OUTRO motivo: granularidade do chunk = granularidade do re-embedding."""
import re
from lake import hash_texto

def chunks_do_documento(doc_id: str, versao: int, titulo: str, conteudo: str, minimo=40):
    blocos = [b.strip() for b in re.split(r"\n\s*\n", conteudo) if b.strip()]
    secao = ""
    out, ordem = [], 0
    for b in blocos:
        if b.startswith("#"):                      # "## Título\ntexto..." no mesmo bloco: título vira seção, resto é o texto
            primeira, _, resto = b.partition("\n")
            secao = primeira.lstrip("#").strip()
            b = resto.strip()
            if not b:
                continue
        texto = f"{titulo} — {secao}\n{b}" if secao else f"{titulo}\n{b}"
        if len(texto) < minimo and out:          # junta fragmento curto ao anterior
            out[-1]["texto"] += "\n" + b
            out[-1]["hash"] = hash_texto(out[-1]["texto"])
            continue
        out.append({"chunk_id": f"{doc_id}#v{versao}#{ordem}", "doc_id": doc_id, "versao": versao, "ordem": ordem,
                    "texto": texto, "hash": hash_texto(texto)})
        ordem += 1
    return out
