import importlib.util

from normacita.config import PROJECT_ROOT

_spec = importlib.util.spec_from_file_location("ingest", PROJECT_ROOT / "scripts" / "ingest_boe.py")
ingest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingest)

BLOQUE = """<?xml version="1.0" encoding="utf-8"?>
<response><status><code>200</code></status><data>
<bloque id="a3" tipo="precepto" titulo="Artículo 3">
  <version id_norma="X" fecha_publicacion="20020918">
    <p class="articulo">Artículo 3. Antiguo.</p><p class="parrafo">Texto viejo.</p>
  </version>
  <version id_norma="Y" fecha_publicacion="20210505">
    <p class="articulo">Artículo 3. Instalación eléctrica.</p>
    <p class="parrafo">1. Primer apartado.</p>
    <p class="parrafo">Continúa el primero.</p>
    <p class="parrafo">2. Segundo apartado.</p>
    <p class="nota_pie">Nota de modificación.</p>
  </version>
</bloque></data></response>"""

INDICE = """<response><data>
<bloque><id>pr</id><tipo>preambulo</tipo></bloque>
<bloque><id>a1</id><tipo>precepto</tipo></bloque>
<bloque><id>a2</id><tipo>precepto</tipo></bloque>
</data></response>"""


def test_parse_bloque_usa_ultima_version_y_divide_apartados():
    frags = ingest.parse_bloque(BLOQUE, "BOE-A-TEST", "Norma test")
    assert [f["apartado"] for f in frags] == ["1", "2"]
    assert frags[0]["titulo"] == "Instalación eléctrica"
    assert frags[0]["texto"] == "1. Primer apartado. Continúa el primero."
    assert frags[1]["url"].endswith("BOE-A-TEST#a3")
    assert all("Nota" not in f["texto"] for f in frags)


def test_parse_indice_solo_preceptos():
    assert ingest.parse_indice(INDICE) == ["a1", "a2"]
