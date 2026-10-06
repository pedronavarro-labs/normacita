import pytest

from normacita.infrastructure.text import has_negative_cue, normalize, stem, tokenize


def test_normalize_quita_tildes_y_mayusculas():
    assert normalize("Tensión NOMINAL") == "tension nominal"


def test_tokenize_quita_stopwords():
    assert tokenize("¿Cuál es la tensión de la red?") == ["tension", "red"]


@pytest.mark.parametrize(
    ("variantes", "raiz"),
    [
        (["instalación", "instalaciones", "instalado"], "instal"),
        (["eléctrica", "eléctrico", "eléctricas"], "electric"),
        (["excluyen", "excluidas", "excluido"], "exclu"),
        (["conductor", "conductores"], "conductor"),
    ],
)
def test_stem_agrupa_variantes(variantes, raiz):
    assert {stem(normalize(v)) for v in variantes} == {raiz}


def test_stem_no_toca_numeros_ni_palabras_cortas():
    assert stem("230") == "230"
    assert stem("red") == "red"


def test_detecta_preguntas_negativas():
    assert has_negative_cue("¿Qué instalaciones quedan excluidas?")
    assert has_negative_cue("¿Cuándo no se aplica el reglamento?")
    assert not has_negative_cue("¿A qué instalaciones se aplica?")
