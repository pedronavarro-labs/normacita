"""Tests del script de ingesta con XML de ejemplo con la misma forma que la API del BOE."""

import importlib.util
import json

from normacita.config import PROJECT_ROOT

_spec = importlib.util.spec_from_file_location("ingest", PROJECT_ROOT / "scripts" / "ingest_boe.py")
ingest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingest)

ARTICULO = """<?xml version="1.0" encoding="utf-8"?>
<response><status><code>200</code></status><data>
<bloque id="a3" tipo="precepto" titulo="Artículo 3">
  <version id_norma="X" fecha_publicacion="20020918">
    <p class="articulo">Artículo 3. Antiguo.</p><p class="parrafo">Texto viejo.</p>
  </version>
  <version id_norma="Y" fecha_publicacion="20210505">
    <p class="articulo">Artículo 3. Instalación eléctrica.</p>
    <p class="parrafo">1.<em> </em>Primer apartado.</p>
    <p class="parrafo_2">a) Continúa el primero.</p>
    <p class="parrafo">2. Segundo apartado.</p>
    <table class="tabla"><tr><td><p class="cuerpo_tabla_izq">Muy baja</p></td>
      <td><p class="cuerpo_tabla_centro">50 V</p></td></tr></table>
    <blockquote><p class="nota_pie">Se modifica por el Real Decreto X.</p></blockquote>
  </version>
</bloque></data></response>"""

ITC = """<response><data><bloque id="ib-9" tipo="precepto" titulo="ITC-BT-09">
<version id_norma="X">
  <p class="anexo_num">ITC-BT-09</p>
  <p class="anexo_tit">INSTALACIONES DE ALUMBRADO EXTERIOR</p>
  <p class="parrafo">0. ÍNDICE</p>
  <p class="parrafo">1. CAMPO DE APLICACIÓN</p>
  <p class="parrafo">2. REDES</p>
  <p class="parrafo">2.1 Cables</p>
  <p class="parrafo">1. CAMPO DE APLICACIÓN</p>
  <p class="parrafo">Se aplica al alumbrado exterior.</p>
  <p class="parrafo">2. REDES.</p>
  <p class="parrafo">2 m, salvo cruzamientos (no es un encabezado).</p>
  <p class="parrafo">2.1 Cables</p>
  <p class="parrafo">Los cables serán de 0,6/1 kV.</p>
  <table><tr><td>3</td><td>4,5</td></tr></table>
</version></bloque></data></response>"""

INDICE = """<response><data>
<bloque><id>pr</id><titulo>[preambulo]</titulo></bloque>
<bloque><id>a1</id><titulo>Artículo 1</titulo></bloque>
<bloque><id>a1-2</id><titulo>Artículo 10</titulo></bloque>
<bloque><id>id</id><titulo>INSTRUCCIONES TÉCNICAS COMPLEMENTARIAS</titulo></bloque>
<bloque><id>ib</id><titulo>ITC-BT-01</titulo></bloque>
<bloque><id>ib-52</id><titulo>ITC-BT-52</titulo></bloque>
</data></response>"""


def test_articulo_usa_ultima_version_divide_apartados_y_linealiza_tablas():
    frags = ingest.parse_articulo(ARTICULO, "BOE-A-TEST", "Norma test")
    assert [f["apartado"] for f in frags] == ["1", "2"]
    assert frags[0]["titulo"] == "Instalación eléctrica"
    assert frags[0]["texto"] == "1. Primer apartado. a) Continúa el primero."
    assert "Muy baja | 50 V" in frags[1]["texto"]
    assert frags[1]["url"].endswith("BOE-A-TEST#a3")
    assert all("Real Decreto X" not in f["texto"] for f in frags)  # nota editorial fuera


def test_itc_secciones_desde_indice_y_filas_de_tabla_no_son_encabezados():
    frags = ingest.parse_itc(ITC, "BOE-A-TEST", "Norma test")
    # "2. REDES" es casi solo un encabezado: se fusiona con su primera subsección 2.1
    assert [f["apartado"] for f in frags] == ["1", "2.1"]
    assert frags[0]["articulo"] == "ITC-BT-09"
    assert frags[0]["titulo"] == "Instalaciones de alumbrado exterior · Campo de aplicación"
    assert frags[1]["titulo"] == "Instalaciones de alumbrado exterior · Cables"
    assert frags[1]["texto"].startswith("2. REDES.")
    assert "2 m, salvo" in frags[1]["texto"]  # no se tomó como encabezado
    assert "3 | 4,5" in frags[1]["texto"]  # fila de tabla linealizada


def test_indice_filtra_articulos_e_itc():
    assert ingest.parse_indice(INDICE) == ["a1", "a1-2", "ib", "ib-52"]
    assert ingest.parse_indice(INDICE, incluir_itc=False) == ["a1", "a1-2"]


def test_trocear_respeta_el_maximo():
    texto = "Frase de prueba bastante larga. " * 200
    assert all(len(t) <= ingest._MAX_CHARS for t in ingest._trocear(texto))


def test_construir_desde_xml_crudo(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "indice.xml").write_text(
        "<response><data><bloque><id>a3</id></bloque><bloque><id>ib-9</id></bloque>"
        "</data></response>",
        encoding="utf-8",
    )
    (raw / "a3.xml").write_text(ARTICULO, encoding="utf-8")
    (raw / "ib-9.xml").write_text(ITC, encoding="utf-8")
    salida = tmp_path / "corpus.json"
    assert ingest.construir("BOE-A-TEST", "Norma", raw, salida, incluir_itc=True) == 4
    data = json.loads(salida.read_text(encoding="utf-8"))
    assert len({f["id"] for f in data["fragmentos"]}) == 4  # ids únicos


def test_corpus_real_es_coherente():
    """El corpus versionado en el repo tiene los 29 artículos y las 52 ITC-BT."""
    data = json.loads((PROJECT_ROOT / "data/corpus/rebt.json").read_text(encoding="utf-8"))
    frags = data["fragmentos"]
    articulos = {f["articulo"] for f in frags if f["articulo"].startswith("Artículo")}
    itcs = {f["articulo"] for f in frags if f["articulo"].startswith("ITC-BT")}
    assert len(articulos) == 29 and len(itcs) == 52
    assert len({f["id"] for f in frags}) == len(frags)
    assert all(f["url"].startswith("https://www.boe.es/") for f in frags)
