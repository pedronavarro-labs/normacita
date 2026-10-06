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
        """Referencia legible: 'Artículo 4.2 (…)' o 'ITC-BT-25, apdo. 2.3.1 (…)'."""
        if self.apartado in ("", "único"):
            return f"{self.articulo} ({self.titulo})"
        if self.articulo.startswith("Artículo"):
            return f"{self.articulo}.{self.apartado} ({self.titulo})"
        return f"{self.articulo}, apdo. {self.apartado} ({self.titulo})"  # ITC-BT-25, apdo. 2.3.1


@dataclass(frozen=True)
class ScoredFragment:
    """Fragmento devuelto por el recuperador.

    - `score`: relevancia (mayor = mejor; escala propia del recuperador).
    - `coverage`: fracción (0-1) del peso de la pregunta presente en el fragmento.
      Sirve para detectar preguntas ajenas al corpus que solo coinciden por azar.
    """

    fragment: Fragment
    score: float
    coverage: float = 1.0


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
