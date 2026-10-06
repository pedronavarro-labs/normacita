"""Carga del corpus de normativa desde JSON (generado por scripts/ingest_boe.py)."""

from __future__ import annotations

import json
from pathlib import Path

from normacita.domain.models import Fragment

_REQUIRED = ("id", "norma", "articulo", "titulo", "apartado", "texto", "url")


def load_corpus(path: Path) -> list[Fragment]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fragments = []
    for raw in data["fragmentos"]:
        missing = [k for k in _REQUIRED if k not in raw]
        if missing:
            raise ValueError(f"Fragmento {raw.get('id', '?')} sin campos: {missing}")
        fragments.append(Fragment(**{k: str(raw[k]) for k in _REQUIRED}))
    if not fragments:
        raise ValueError(f"El corpus {path} está vacío")
    return fragments
