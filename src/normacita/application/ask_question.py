"""Caso de uso principal: responder una pregunta citando la normativa.

Flujo (RAG):
1. Recuperar fragmentos relevantes (Retriever).
2. Si nada supera el umbral → responder "sin base normativa" SIN llamar al LLM
   (evita alucinaciones y coste).
3. Si hay base → pedir al LLM una respuesta que use SOLO esos fragmentos.
4. Post-proceso: quedarse con las citas [n] que el modelo usó realmente y
   descartar marcadores inventados.
"""

from __future__ import annotations

import re

from normacita.application.ports import LLMProvider, Retriever
from normacita.domain.models import Answer, Citation, ScoredFragment

NO_BASIS_MESSAGE = (
    "No he encontrado ningún artículo del corpus cargado que responda a esta pregunta. "
    "Reformúlala o consulta la norma completa; no respondo sin una fuente que lo respalde."
)

_MARKER = re.compile(r"\[(\d{1,2})\]")


class AskQuestion:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMProvider,
        top_k: int = 4,
        min_score: float = 1.0,
        min_coverage: float = 0.0,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._top_k = top_k
        self._min_score = min_score
        self._min_coverage = min_coverage

    def relevant(self, question: str) -> list[ScoredFragment]:
        """Fragmentos que superan los umbrales de puntuación y de cobertura."""
        hits = self._retriever.search(question, self._top_k)
        if not hits or hits[0].coverage < self._min_coverage:
            return []  # el mejor resultado no cubre la pregunta: no hay base
        return [h for h in hits if h.score >= self._min_score]

    def execute(self, question: str) -> Answer:
        hits = self.relevant(question)
        if not hits:
            return Answer(texto=NO_BASIS_MESSAGE, sin_base=True, proveedor=self._llm.name)

        fragments = [h.fragment for h in hits]
        raw = self._llm.generate(question, fragments)

        # Índices citados por el modelo (1-based) que existen de verdad.
        cited = []
        for m in _MARKER.finditer(raw):
            i = int(m.group(1))
            if 1 <= i <= len(fragments) and i not in cited:
                cited.append(i)

        # Eliminar marcadores fuera de rango (citas inventadas por el modelo).
        def _clean(m: re.Match[str]) -> str:
            return m.group(0) if 1 <= int(m.group(1)) <= len(fragments) else ""

        texto = _MARKER.sub(_clean, raw).strip()

        # Si el modelo no citó nada, devolvemos todos los fragmentos usados como contexto
        # para que el usuario pueda verificar (transparencia).
        numbers = sorted(cited) if cited else range(1, len(fragments) + 1)
        citas = [Citation(numero=i, fragment=fragments[i - 1]) for i in numbers]
        return Answer(texto=texto, citas=citas, proveedor=self._llm.name)
