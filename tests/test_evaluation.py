"""Evaluación de calidad en CI (proveedor fake, determinista).

Los umbrales son un "trinquete": se fijan algo por debajo del resultado actual para
detectar regresiones. Si mejoras la recuperación, súbelos (ver docs/EVALUACION.md).
"""

import pytest

from normacita.evaluation import apartado_base, cargar_preguntas, evaluar

UMBRALES = {"hit@1": 0.60, "hit@3": 0.70, "cobertura": 0.95, "acierto_negativas": 0.25}


@pytest.fixture(scope="module")
def informe(retriever):
    return evaluar(retriever, cargar_preguntas())


def test_las_citas_esperadas_existen_en_el_corpus(fragments):
    """Protege el conjunto de evaluación: cada cita esperada debe existir de verdad."""
    disponibles = {(f.articulo, apartado_base(f.apartado)) for f in fragments}
    for q in cargar_preguntas():
        if q["esperado"] != "fuera":
            for art, ap in q["esperado"]:
                assert (art, ap) in disponibles, f"{q['id']}: {art} {ap} no está en el corpus"


def test_tamano_del_conjunto():
    preguntas = cargar_preguntas()
    assert sum(q["esperado"] != "fuera" for q in preguntas) >= 25
    assert sum(q["esperado"] == "fuera" for q in preguntas) >= 5


@pytest.mark.parametrize("metrica", sorted(UMBRALES))
def test_metricas_superan_umbral(informe, metrica):
    valor = informe.metricas[metrica]
    assert valor >= UMBRALES[metrica], f"{metrica}={valor} < {UMBRALES[metrica]}"
