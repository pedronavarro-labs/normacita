"""Utilidades de texto para la búsqueda: normalización, palabras vacías y stemming ligero.

El stemmer es deliberadamente sencillo (sin dependencias): agrupa plurales, género
y algunos tiempos verbales frecuentes en normativa ("aplica", "aplicará", "aplican"),
de modo que la pregunta y el texto de la norma coincidan aunque no usen la misma forma.
"""

from __future__ import annotations

import re
import unicodedata

# Palabras vacías en español + muletillas de pregunta que no aportan a la búsqueda.
STOPWORDS = frozenset(
    """a al algo como con cual cuales cuando de del desde donde e el ella ellas ellos en entre
    es esa ese esta este esto estos estas ha han hasta la las le les lo los mas me mi no o
    para pero por que se sea ser si sin sobre son su sus tiene tienen un una uno unos unas y
    ya hay debe deben puede pueden segun quien quienes cuanto cuantos cuantas cuantas existe
    dame dime hace hacen otro otra otros otras muy tan tus tu mis nos vosotros usted""".split()  # noqa: SIM905
)

# Palabras que indican que la pregunta busca exclusiones o excepciones.
_CUES = (
    "no excluye excluyen excluido excluida excluidos excluidas exclusion excepto excepcion "
    "excepciones salvo exento exenta exentos exentas"
)
NEGATIVE_CUES = frozenset(_CUES.split())

_TOKEN = re.compile(r"[a-záéíóúüñ0-9]+")
_VERBAL = ("arán", "erán", "irán", "ará", "erá", "irá", "aron", "ieron")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Minúsculas y sin tildes: 'Tensión' → 'tension'."""
    return strip_accents(text.lower())


def stem(word: str) -> str:
    """Stemming ligero en español. Recibe la palabra en minúsculas CON tildes."""
    w = word
    if len(w) <= 3 or w.isdigit():
        return strip_accents(w)
    for suf in _VERBAL:  # futuros y pasados: aplicará → aplic
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return strip_accents(w[: -len(suf)])
    w = strip_accents(w)
    if w.endswith("mente") and len(w) > 7:
        w = w[:-5]
    if w.endswith("es") and len(w) > 4 and w[-3] in "lrndzjc":  # redes → red, tensiones → tension
        w = w[:-2]
    elif w.endswith("s") and len(w) > 4 and w[-2] in "aeiou":  # zonas → zona
        w = w[:-1]
    if w.endswith("acion") and len(w) > 7:  # aplicación → aplic, instalación → instal
        return w[:-5]
    if w.endswith(("an", "en")) and len(w) > 6:  # aplican → aplic
        w = w[:-2]
    if w[-1] in "aoe" and len(w) > 4:  # eléctrica/eléctrico → electric
        w = w[:-1]
    if w.endswith(("ad", "id")) and len(w) > 6:  # instalado → instal, excluido → exclu
        w = w[:-2]
    elif w.endswith("uy"):  # excluyen/incluye → exclu/inclu (verbos en -uir)
        w = w[:-1]
    return w


def raw_tokens(text: str) -> list[str]:
    """Tokens en minúsculas sin quitar tildes (para stemming y detección de negación)."""
    return _TOKEN.findall(text.lower())


def tokenize(text: str) -> list[str]:
    """Tokens normalizados y con stemming, sin palabras vacías ni de 1 carácter."""
    out = []
    for tok in raw_tokens(text):
        if len(tok) <= 1 or normalize(tok) in STOPWORDS:
            continue
        out.append(stem(tok))
    return out


def has_negative_cue(text: str) -> bool:
    return any(normalize(t) in NEGATIVE_CUES for t in raw_tokens(text))
