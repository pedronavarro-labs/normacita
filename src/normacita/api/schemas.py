"""Esquemas de entrada/salida de la API (validación con Pydantic v2)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class AskRequest(BaseModel):
    pregunta: str = Field(min_length=3, max_length=500, examples=["¿Qué es baja tensión?"])

    @field_validator("pregunta")
    @classmethod
    def clean(cls, v: str) -> str:
        v = _CONTROL_CHARS.sub(" ", v).strip()
        if len(v) < 3:
            raise ValueError("La pregunta es demasiado corta")
        return v


class CitationOut(BaseModel):
    numero: int
    id: str
    norma: str
    articulo: str
    apartado: str
    titulo: str
    texto: str
    url: str


class AskResponse(BaseModel):
    respuesta: str
    citas: list[CitationOut]
    sin_base: bool
    proveedor: str
