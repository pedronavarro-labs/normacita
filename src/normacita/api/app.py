"""Aplicación FastAPI: composición de dependencias y endpoints HTTP.

Aquí se "cablea" todo (composition root): corpus → recuperador, proveedor de IA
→ caso de uso. Los endpoints solo traducen HTTP ⇄ caso de uso.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from normacita import __version__
from normacita.api.schemas import AskRequest, AskResponse, CitationOut
from normacita.api.security import RateLimiter, SecurityHeadersMiddleware
from normacita.application.ask_question import AskQuestion
from normacita.application.ports import LLMError, LLMProvider, Retriever
from normacita.config import Settings
from normacita.infrastructure.bm25_retriever import BM25Retriever
from normacita.infrastructure.corpus_loader import load_corpus
from normacita.infrastructure.llm.factory import build_llm_provider

logger = logging.getLogger("normacita")
STATIC_DIR = Path(__file__).parent / "static"


def create_app(
    settings: Settings | None = None,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
) -> FastAPI:
    """Crea la app. `retriever` y `llm` se pueden inyectar (tests)."""
    settings = settings or Settings.from_env()
    if retriever is None:
        retriever = BM25Retriever(load_corpus(settings.corpus_path))
    llm = llm or build_llm_provider(settings)
    ask = AskQuestion(retriever, llm, settings.retrieval_top_k, settings.retrieval_min_score)
    limiter = RateLimiter(settings.rate_limit_per_minute)

    app = FastAPI(title="NormaCita", version=__version__)
    app.add_middleware(SecurityHeadersMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "proveedor": llm.name}

    @app.post("/api/ask", response_model=AskResponse)
    def ask_endpoint(body: AskRequest, request: Request) -> AskResponse:
        client_ip = request.client.host if request.client else "desconocido"
        if not limiter.allow(client_ip):
            raise HTTPException(429, "Demasiadas peticiones. Espera un minuto.")
        try:
            answer = ask.execute(body.pregunta)
        except LLMError:
            logger.exception("Fallo del proveedor de IA")
            # Mensaje genérico: no filtramos detalles internos al cliente.
            raise HTTPException(
                502, "El servicio de IA no está disponible. Inténtalo más tarde."
            ) from None
        return AskResponse(
            respuesta=answer.texto,
            sin_base=answer.sin_base,
            proveedor=answer.proveedor,
            citas=[
                CitationOut(
                    numero=c.numero,
                    id=c.fragment.id,
                    norma=c.fragment.norma,
                    articulo=c.fragment.articulo,
                    apartado=c.fragment.apartado,
                    titulo=c.fragment.titulo,
                    texto=c.fragment.texto,
                    url=c.fragment.url,
                )
                for c in answer.citas
            ],
        )

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
