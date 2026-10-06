"""Recuperador léxico BM25 en memoria (sin dependencias externas).

Es el primer paso del walking skeleton: suficiente para un corpus pequeño y
100 % determinista (ideal para tests). Implementa el puerto `Retriever`, así que
más adelante se puede sustituir por búsqueda vectorial (embeddings + pgvector)
o híbrida sin tocar el caso de uso. Ver docs/adr/ADR-0003.
"""

from __future__ import annotations

import math
from collections import Counter

from normacita.domain.models import Fragment, ScoredFragment
from normacita.infrastructure.text import tokenize


class BM25Retriever:
    def __init__(self, fragments: list[Fragment], k1: float = 1.5, b: float = 0.75) -> None:
        self._fragments = fragments
        self._k1 = k1
        self._b = b
        # Indexamos título + texto: el título del artículo aporta mucho contexto.
        self._docs = [Counter(tokenize(f"{f.titulo} {f.texto}")) for f in fragments]
        self._lengths = [sum(d.values()) for d in self._docs]
        self._avg_len = sum(self._lengths) / len(self._lengths) if self._lengths else 0.0
        df: Counter[str] = Counter()
        for doc in self._docs:
            df.update(doc.keys())
        n = len(self._docs)
        # IDF con suavizado (variante BM25+ no negativa).
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query: str, top_k: int) -> list[ScoredFragment]:
        terms = tokenize(query)
        if not terms:
            return []
        scored = []
        for i, doc in enumerate(self._docs):
            score = 0.0
            for t in terms:
                tf = doc.get(t, 0)
                if tf == 0:
                    continue
                norm = 1 - self._b + self._b * self._lengths[i] / self._avg_len
                score += self._idf[t] * tf * (self._k1 + 1) / (tf + self._k1 * norm)
            if score > 0:
                scored.append(ScoredFragment(self._fragments[i], round(score, 4)))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]
