from fastapi.testclient import TestClient

from normacita.api.app import create_app
from normacita.api.security import RateLimiter
from normacita.application.ports import LLMError


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_flujo_completo_con_citas(client):
    r = client.post("/api/ask", json={"pregunta": "¿Qué tensiones se consideran baja tensión?"})
    assert r.status_code == 200
    data = r.json()
    assert data["sin_base"] is False and data["proveedor"] == "fake"
    assert data["citas"] and all(c["url"].startswith("https://www.boe.es/") for c in data["citas"])
    assert "[1]" in data["respuesta"]


def test_pregunta_fuera_de_corpus(client):
    r = client.post("/api/ask", json={"pregunta": "receta de paella valenciana"})
    assert r.status_code == 200 and r.json()["sin_base"] is True and r.json()["citas"] == []


def test_validacion_pregunta(client):
    assert client.post("/api/ask", json={"pregunta": "a"}).status_code == 422
    assert client.post("/api/ask", json={"pregunta": "x" * 501}).status_code == 422
    assert client.post("/api/ask", json={}).status_code == 422
    assert client.post("/api/ask", json={"pregunta": "\x00\x01  \x02"}).status_code == 422


def test_cabeceras_de_seguridad(client):
    r = client.get("/")
    assert r.status_code == 200 and "NormaCita" in r.text
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"


def test_rate_limit(settings, retriever):
    from dataclasses import replace

    c = TestClient(create_app(replace(settings, rate_limit_per_minute=2), retriever=retriever))
    body = {"pregunta": "campo de aplicación"}
    assert [c.post("/api/ask", json=body).status_code for _ in range(3)] == [200, 200, 429]


def test_rate_limiter_ventana():
    t = [0.0]
    rl = RateLimiter(1, clock=lambda: t[0])
    assert rl.allow("ip") and not rl.allow("ip")
    t[0] = 61
    assert rl.allow("ip")


def test_error_del_llm_da_502_generico(settings, retriever):
    class Broken:
        name = "roto"

        def generate(self, q, f):
            raise LLMError("detalle interno con secreto")

    c = TestClient(create_app(settings, retriever=retriever, llm=Broken()))
    r = c.post("/api/ask", json={"pregunta": "baja tensión"})
    assert r.status_code == 502 and "secreto" not in r.text
