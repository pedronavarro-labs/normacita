def test_baja_tension_encuentra_articulo_4(retriever):
    hits = retriever.search("¿Qué tensiones se consideran baja tensión?", top_k=3)
    assert hits, "debería encontrar algo"
    assert any(h.fragment.articulo == "Artículo 4" for h in hits)


def test_resultados_ordenados_por_puntuacion(retriever):
    hits = retriever.search("instalaciones de alumbrado público", top_k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_pregunta_ajena_no_devuelve_nada(retriever):
    assert retriever.search("receta de paella valenciana", top_k=3) == []


def test_consulta_solo_stopwords(retriever):
    assert retriever.search("de la que", top_k=3) == []
