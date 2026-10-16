"""embeddings.py — MiniLM multilíngue 384d, o mesmo modelo da Operação Q.

O modelo carrega uma vez por sessão (~10 s) e depois embeda ~300 textos por segundo em CPU.
O que importa na aula não é a velocidade: é QUANTAS vezes você chama isso sem precisar.
"""
import os

_MODELO = None
NOME = os.environ.get("MODELO_EMBEDDING", "paraphrase-multilingual-MiniLM-L12-v2")
DIM = 384
_contador = {"textos": 0, "chamadas": 0}


def modelo():
    global _MODELO
    if _MODELO is None:
        from sentence_transformers import SentenceTransformer
        _MODELO = SentenceTransformer(NOME, device="cpu")
    return _MODELO


def embed(textos) -> list[list[float]]:
    textos = list(textos)
    if not textos:
        return []
    _contador["textos"] += len(textos)
    _contador["chamadas"] += 1
    v = modelo().encode(textos, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return [[float(x) for x in linha] for linha in v]


def contador() -> dict:
    return dict(_contador)


def zerar_contador():
    _contador.update(textos=0, chamadas=0)
