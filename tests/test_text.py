from normacita.infrastructure.text import normalize, tokenize


def test_normalize_quita_tildes_y_mayusculas():
    assert normalize("Tensión NOMINAL") == "tension nominal"


def test_tokenize_quita_stopwords():
    assert tokenize("¿Cuál es la tensión de la red?") == ["tension", "red"]
