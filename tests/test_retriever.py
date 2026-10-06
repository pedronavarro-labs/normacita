def test_clasificacion_tensiones_encuentra_articulo_4(retriever):
    hits = retriever.search("¿Cómo se clasifican las tensiones?", top_k=3)
    assert hits, "debería encontrar algo"
    assert hits[0].fragment.articulo == "Artículo 4"


def test_resultados_ordenados_por_puntuacion(retriever):
    hits = retriever.search("instalaciones de alumbrado público", top_k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_pregunta_ajena_no_devuelve_nada(retriever):
    assert retriever.search("receta de paella valenciana", top_k=3) == []


def test_consulta_solo_stopwords(retriever):
    assert retriever.search("de la que", top_k=3) == []


def _pos(hits, articulo, apartado):
    for i, h in enumerate(hits):
        if h.fragment.articulo == articulo and h.fragment.apartado == apartado:
            return i
    return None


def test_ambito_positivo_no_prioriza_exclusiones(retriever):
    """Regresión: '¿A qué instalaciones se aplica?' devolvía el art. 2.4 (exclusiones) primero."""
    hits = retriever.search("¿A qué instalaciones se aplica?", top_k=3)
    assert _pos(hits, "Artículo 2", "1") is not None
    assert _pos(hits, "Artículo 2", "4") is None


def test_pregunta_negativa_si_encuentra_exclusiones(retriever):
    hits = retriever.search("¿Qué instalaciones quedan excluidas del reglamento?", top_k=3)
    assert _pos(hits, "Artículo 2", "4") == 0


def test_cobertura_entre_0_y_1(retriever):
    hits = retriever.search("tensión nominal receta paella", top_k=3)
    assert hits and all(0 < h.coverage < 1 for h in hits)
    completo = retriever.search("tensión nominal", top_k=1)
    assert completo[0].coverage == 1.0
