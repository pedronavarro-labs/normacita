"""Punto de entrada ASGI: `uvicorn normacita.main:app`."""

from normacita.api.app import create_app

app = create_app()
