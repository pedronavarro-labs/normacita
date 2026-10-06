"""Proveedor de IA falso (determinista, sin red ni claves).

Sirve para desarrollar, para los tests y como demo pública sin coste. Simula el
contrato del LLM real: devuelve un texto con marcadores [n] basado únicamente en
los fragmentos recibidos (respuesta extractiva: copia la frase más relevante).
"""

from __future__ import annotations

import re

from normacita.domain.models import Fragment

_SENTENCE = re.compile(r"(?<=\.)\s+")  # fin de frase = punto + espacio
_MAX_CHARS = 350


class FakeLLMProvider:
    name = "fake"

    def generate(self, question: str, fragments: list[Fragment]) -> str:
        if not fragments:
            return "No dispongo de fragmentos para responder."
        top = fragments[0]
        first_sentence = _SENTENCE.split(top.texto.strip())[0]
        if len(first_sentence) > _MAX_CHARS:
            first_sentence = first_sentence[:_MAX_CHARS].rsplit(" ", 1)[0] + "…"
        lines = [f"Según {top.referencia}: «{first_sentence}» [1]."]
        if len(fragments) > 1:
            lines.append(f"Ver también {fragments[1].referencia} [2].")
        lines.append(
            "(Respuesta generada en modo demostración, sin modelo de IA: extracto literal. "
            "Orientativa; consulta siempre la norma oficial.)"
        )
        return " ".join(lines)
