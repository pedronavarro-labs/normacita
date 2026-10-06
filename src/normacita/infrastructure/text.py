"""Utilidades de texto para la búsqueda: normalización y tokenización en español."""

from __future__ import annotations

import re
import unicodedata

# Lista corta de palabras vacías en español: no aportan significado a la búsqueda.
STOPWORDS = frozenset(
    """a al algo como con cual cuando de del desde donde e el ella en entre es esa ese esta
    este esto ha han hasta la las le les lo los mas me mi no o para pero por que qué se
    sea ser si sin sobre son su sus tiene un una uno unos unas y ya hay cuál cuáles debe
    deben puede pueden según""".split()  # noqa: SIM905 (más legible que una lista larga)
)

_TOKEN = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> str:
    """Minúsculas y sin tildes: 'Tensión' → 'tension'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    """Tokens normalizados sin palabras vacías ni tokens de 1 carácter."""
    stop = {normalize(w) for w in STOPWORDS}
    return [t for t in _TOKEN.findall(normalize(text)) if len(t) > 1 and t not in stop]
