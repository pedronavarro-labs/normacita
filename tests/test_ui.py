"""Comprobaciones estáticas de la interfaz: seguridad (CSP/XSS) y accesibilidad básica."""

import re

from normacita.api.app import STATIC_DIR

HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
JS = (STATIC_DIR / "app.js").read_text(encoding="utf-8")


def test_sin_scripts_ni_estilos_en_linea():
    """La CSP 'default-src self' bloquearía scripts/estilos inline: no debe haber ninguno."""
    for tag in re.findall(r"<script\b[^>]*>", HTML):
        assert "src=" in tag, f"script inline: {tag}"
    assert "<style" not in HTML
    assert not re.search(r"\sstyle=", HTML)
    assert not re.search(r"\son[a-z]+=", HTML), "manejadores de eventos inline"


def test_js_no_inserta_html_del_servidor():
    for patron in (
        r"\.innerHTML\s*=",
        r"\.outerHTML\s*=",
        r"insertAdjacentHTML",
        r"document\.write",
    ):
        assert not re.search(patron, JS), patron


def test_accesibilidad_basica():
    assert '<html lang="es">' in HTML
    assert '<label for="pregunta"' in HTML and 'id="pregunta"' in HTML
    assert 'aria-live="polite"' in HTML and 'role="alert"' in HTML
    assert "skip-link" in HTML


def test_estados_y_pie_presentes():
    for fragmento in (
        "demo-badge",
        "sin-base",
        'id="error"',
        "chip-example",
        "no es asesoramiento profesional",
        "github.com/pedronavarro-labs/normacita",
    ):
        assert fragmento in HTML, fragmento


def test_recursos_estaticos_se_sirven(client):
    for ruta in ("/static/app.js", "/static/styles.css", "/static/favicon.svg"):
        assert client.get(ruta).status_code == 200, ruta


def test_health_expone_proveedor_para_la_insignia_demo(client):
    assert client.get("/health").json()["proveedor"] == "fake"
