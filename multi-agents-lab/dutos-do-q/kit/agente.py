"""agente.py — os órgãos do Q que vivem FORA do lakehouse.

Esta é a parte que a aula passada construiu, reduzida ao mínimo. Ela está aqui por um motivo só:
a memória do cliente e o cache de respostas não são tabelas do lake, e é exatamente por isso que
um pedido de eliminação LGPD não se resolve com um DELETE na Silver. O duto precisa AVISAR, e alguém
do lado de cá precisa ouvir. É o padrão outbox, e é o ponto em que a maioria dos esquadrões vaza dado.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import embeddings


class LojaLocal:
    """Loja vetorial do agente, em JSON e numpy. Na Operação Q era Chroma; a interface é a mesma."""

    def __init__(self, caminho: str):
        self.caminho = Path(caminho)
        self.itens = json.loads(self.caminho.read_text(encoding="utf-8")) if self.caminho.exists() else []

    def _salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps(self.itens, ensure_ascii=False), encoding="utf-8")

    def adicionar(self, texto: str, meta: dict):
        self.itens.append({"texto": texto, "meta": meta, "vetor": embeddings.embed([texto])[0], "criado_em": time.time()})
        self._salvar()

    def buscar(self, texto: str, k: int = 5, filtro: dict | None = None):
        candidatos = [i for i in self.itens if not filtro or all(i["meta"].get(a) == b for a, b in filtro.items())]
        if not candidatos:
            return []
        consulta = np.array(embeddings.embed([texto])[0])
        matriz = np.array([c["vetor"] for c in candidatos])
        scores = matriz @ consulta
        return sorted(({**c, "score": float(s)} for c, s in zip(candidatos, scores)), key=lambda x: -x["score"])[:k]

    def remover(self, filtro: dict) -> int:
        antes = len(self.itens)
        self.itens = [i for i in self.itens if not all(i["meta"].get(a) == b for a, b in filtro.items())]
        self._salvar()
        return antes - len(self.itens)

    def limpar(self):
        self.itens = []
        self._salvar()


class Memoria:
    """Memória episódica por cliente. O isolamento é filtro no retrieval, nunca instrução no prompt."""

    def __init__(self, pasta: str = "estado_agente", alfa: float = 0.75, beta: float = 0.25, janela_dias: int = 240):
        self.loja = LojaLocal(f"{pasta}/memorias.json")
        self.alfa, self.beta, self.janela = alfa, beta, janela_dias

    def lembrar(self, cliente_id: str, texto: str, tipo: str = "contexto", data: str | None = None):
        self.loja.adicionar(texto, {"cliente_id": cliente_id, "tipo": tipo,
                                    "data": data or time.strftime("%Y-%m-%d")})

    def recuperar(self, cliente_id: str, pergunta: str, k: int = 3):
        candidatos = self.loja.buscar(pergunta, k=20, filtro={"cliente_id": cliente_id})
        hoje = time.time()
        for c in candidatos:
            idade = (hoje - time.mktime(time.strptime(c["meta"]["data"], "%Y-%m-%d"))) / 86400
            c["score_final"] = self.alfa * c["score"] + self.beta * max(0.0, 1 - idade / self.janela)
        return sorted(candidatos, key=lambda c: -c["score_final"])[:k]

    def esquecer_cliente(self, cliente_id: str) -> int:
        return self.loja.remover({"cliente_id": cliente_id})

    def quantas(self, cliente_id: str) -> int:
        return len([i for i in self.loja.itens if i["meta"].get("cliente_id") == cliente_id])


class CacheSemantico:
    """Cache de respostas por similaridade, com TTL por tópico. Uma tarifa que muda torna
    a resposta cacheada errada antes do TTL expirar: por isso o duto invalida em vez de esperar."""

    TTL = {"tarifa": 3600, "mercado": 3600, "conceito": 30 * 86400, "geral": 6 * 3600}

    def __init__(self, pasta: str = "estado_agente", limiar: float = 0.90):
        self.loja = LojaLocal(f"{pasta}/cache.json")
        self.limiar = limiar
        self.acertos = self.erros = 0

    @staticmethod
    def topico(pergunta: str) -> str:
        p = pergunta.lower()
        if any(w in p for w in ("tarifa", "custa", "sacar", "saque", "cobra")):
            return "tarifa"
        if any(w in p for w in ("cdi", "dólar", "dolar", "ptax", "rende")):
            return "mercado"
        if p.startswith("o que é") or "o que significa" in p:
            return "conceito"
        return "geral"

    def consultar(self, pergunta: str):
        topo = self.loja.buscar(pergunta, k=1)
        if topo and topo[0]["score"] >= self.limiar and time.time() - topo[0]["criado_em"] < self.TTL[topo[0]["meta"]["topico"]]:
            self.acertos += 1
            return topo[0]["meta"]["resposta"]
        self.erros += 1
        return None

    def guardar(self, pergunta: str, resposta: str):
        self.loja.adicionar(pergunta, {"topico": self.topico(pergunta), "resposta": resposta})

    def invalidar(self, topico: str) -> int:
        return self.loja.remover({"topico": topico})

    def itens_do_topico(self, topico: str) -> int:
        return len([i for i in self.loja.itens if i["meta"].get("topico") == topico])


def consumir_eventos(lake, memoria: Memoria, cache: CacheSemantico) -> list[dict]:
    """A ponta do duto que chega aos órgãos fora do lakehouse. Idempotente: reaplicar não muda nada."""
    if not lake.existe("gold.eventos_agente"):
        return []
    pendentes = lake.sql("SELECT evento_id, tipo, payload FROM gold.eventos_agente WHERE NOT consumido ORDER BY criado_em")
    aplicados = []
    for e in pendentes.to_dict("records"):
        payload = json.loads(e["payload"])
        if e["tipo"] == "invalidar_cache":
            removidos = cache.invalidar(payload.get("topico", "geral"))
        elif e["tipo"] == "esquecer_cliente":
            removidos = memoria.esquecer_cliente(payload["cliente_id"])
            cache.invalidar("geral")  # uma resposta cacheada pode conter dado do cliente
        else:
            removidos = 0
        aplicados.append({**e, "removidos": removidos})
        lake.atualizar("gold.eventos_agente", f"evento_id = '{e['evento_id']}'", {"consumido": "true"})
    return aplicados
