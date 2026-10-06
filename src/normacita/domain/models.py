"""Modelo de dominio: conceptos del negocio, sin dependencias de frameworks.

Capa más interna de la arquitectura (Clean Architecture): no importa nada de
FastAPI, httpx ni de proveedores de IA.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Fragment:
    """Un trozo citable de una norma (normalmente un apartado de un artículo)."""

    id: str
    norma: str
    articulo: str
    titulo: str
    apartado: str
    texto: str
    url: str

    @property
    def referencia(self) -> str:
        """Referencia legible, p. ej. 'Artículo 4.2 (Clasificación de las tensiones…)'."""
        ap = "" if self.apartado in ("", "único") else f".{self.apartado}"
        return f"{self.articulo}{ap} ({self.titulo})"


@dataclass(frozen=True)
class ScoredFragment:
    """Fragmento devuelto por el recuperador con su puntuación de relevancia."""

    fragment: Fragment
    score: float


@dataclass(frozen=True)
class Citation:
    """Cita de la respuesta: `numero` coincide con el marcador [n] del texto."""

    numero: int
    fragment: Fragment


@dataclass(frozen=True)
class Answer:
    """Respuesta final del asistente.

    - `texto`: respuesta en lenguaje natural con marcadores [n].
    - `citas`: fragmentos que respaldan la respuesta, numerados como los marcadores.
    - `sin_base`: True si no se encontró normativa relevante (no se llama al LLM).
    """

    texto: str
    citas: list[Citation] = field(default_factory=list)
    sin_base: bool = False
    proveedor: str = ""
