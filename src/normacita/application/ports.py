"""Puertos (interfaces) que la aplicación necesita del exterior.

La lógica de negocio depende de estas abstracciones, no de implementaciones
concretas (principio de inversión de dependencias). Así se puede cambiar el
proveedor de IA o el motor de búsqueda sin tocar el caso de uso, y en los tests
se usan dobles (fakes) sin red ni claves.
"""

from __future__ import annotations

from typing import Protocol

from normacita.domain.models import Fragment, ScoredFragment


class Retriever(Protocol):
    """Busca los fragmentos de normativa más relevantes para una pregunta."""

    def search(self, query: str, top_k: int) -> list[ScoredFragment]: ...


class LLMProvider(Protocol):
    """Genera una respuesta en lenguaje natural a partir de fragmentos numerados."""

    name: str

    def generate(self, question: str, fragments: list[Fragment]) -> str: ...


class LLMError(RuntimeError):
    """Error al hablar con el proveedor de IA (red, cuota, respuesta inválida…)."""
