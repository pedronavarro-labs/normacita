"""Recuperador léxico BM25 en memoria (sin dependencias externas).

Mejoras sobre BM25 "de libro" (ver docs/adr/ADR-0003 y docs/EVALUACION.md):

1. **Stemming ligero en español** (``text.stem``): "aplica"/"aplicará", "zonas"/"zona".
2. **Campo título ponderado** (BM25F simplificado): el título del artículo o de la
   sección de la ITC y su identificador ("ITC-BT-25") suman con peso ``title_weight``.
3. **Prior jerárquico**: ``article_boost`` favorece el articulado del reglamento
   frente a las ITC cuando la coincidencia léxica es parecida (preguntas generales).
4. **Cláusulas negativas**: los apartados que excluyen ("Se excluyen…", "No se
   aplicarán…") se penalizan si la pregunta no busca exclusiones, y se favorecen si sí.
5. **Cobertura de la consulta**: cada resultado indica qué fracción del "peso" (IDF)
   de la pregunta aparece en el fragmento. Una pregunta ajena a la norma suele
   coincidir solo en una palabra suelta ("2010", "ciencia") → cobertura baja → el
   caso de uso puede negarse a responder.

Implementa el puerto ``Retriever``: se puede sustituir por búsqueda vectorial o
híbrida sin tocar el caso de uso.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from normacita.domain.models import Fragment, ScoredFragment
from normacita.infrastructure.text import has_negative_cue, tokenize

_NEGATIVE_CLAUSE = re.compile(
    r"^\s*(\d+\.\s*)?(se excluyen|quedan excluid|no se aplicar|no ser[áa] de aplicaci)",
    re.IGNORECASE,
)


class _Field:
    """Índice BM25 de un campo (texto o título)."""

    def __init__(self, docs: list[list[str]], k1: float, b: float) -> None:
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avg = (sum(self.len) / len(self.len)) or 1.0 if self.len else 1.0
        self.k1, self.b = k1, b

    def score(self, i: int, term: str, idf: float) -> float:
        tf = self.tf[i].get(term, 0)
        if not tf:
            return 0.0
        norm = 1 - self.b + self.b * self.len[i] / self.avg
        return idf * tf * (self.k1 + 1) / (tf + self.k1 * norm)


class BM25Retriever:
    def __init__(
        self,
        fragments: list[Fragment],
        k1: float = 1.5,
        b: float = 0.75,
        title_weight: float = 1.0,
        negative_penalty: float = 0.5,
        article_boost: float = 1.2,
    ) -> None:
        self._fragments = fragments
        self._title_weight = title_weight
        self._negative_penalty = negative_penalty
        text_docs = [tokenize(f.texto) for f in fragments]
        title_docs = [tokenize(f"{f.articulo} {f.titulo}") for f in fragments]
        self._text = _Field(text_docs, k1, b)
        self._title = _Field(title_docs, k1, b)
        self._negative = [bool(_NEGATIVE_CLAUSE.match(f.texto)) for f in fragments]
        # Prior jerárquico: el articulado del reglamento es el marco general y las ITC lo
        # desarrollan. Ante empate léxico, una pregunta general debe citar el artículo.
        self._prior = [
            article_boost if f.articulo.startswith("Artículo") else 1.0 for f in fragments
        ]
        df: Counter[str] = Counter()
        for t_doc, h_doc in zip(text_docs, title_docs, strict=True):
            df.update(set(t_doc) | set(h_doc))
        n = len(fragments)
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        # Un término que no aparece nunca en el corpus pesa como el más raro posible.
        self._idf_unknown = math.log(1 + (n + 0.5) / 0.5)

    def search(self, query: str, top_k: int) -> list[ScoredFragment]:
        terms = list(dict.fromkeys(tokenize(query)))  # sin duplicados, en orden
        if not terms:
            return []
        weights = {t: self._idf.get(t, self._idf_unknown) for t in terms}
        total_weight = sum(weights.values())
        wants_negative = has_negative_cue(query)
        scored = []
        for i, frag in enumerate(self._fragments):
            score, matched = 0.0, 0.0
            for t in terms:
                idf = self._idf.get(t)
                if idf is None:
                    continue
                s = self._text.score(i, t, idf) + self._title_weight * self._title.score(i, t, idf)
                if s:
                    score += s
                    matched += weights[t]
            if score <= 0:
                continue
            score *= self._prior[i]
            if self._negative[i]:
                score *= 1.3 if wants_negative else self._negative_penalty
            coverage = matched / total_weight
            scored.append(ScoredFragment(frag, round(score, 4), round(coverage, 3)))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]
