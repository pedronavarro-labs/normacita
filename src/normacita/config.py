"""Configuración leída de variables de entorno (12-factor).

Toda la configuración sensible (claves de API) llega por entorno y nunca se escribe
en el código ni en el repositorio. Ver `.env.example`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Raíz del proyecto (…/normacita) cuando se ejecuta desde el código fuente (pip install -e).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve(path: Path) -> Path:
    """Rutas relativas: primero respecto al directorio actual (Docker: /app),
    después respecto a la raíz del proyecto (ejecución desde el repo)."""
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    return cwd_path if cwd_path.exists() else PROJECT_ROOT / path


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "fake"
    llm_base_url: str = ""
    llm_api_key: str = field(default="", repr=False)  # repr=False: no aparece en logs
    llm_model: str = ""
    llm_timeout_seconds: float = 30.0
    corpus_path: Path = PROJECT_ROOT / "data" / "corpus" / "rebt.json"
    retrieval_top_k: int = 4
    retrieval_min_score: float = 1.0
    rate_limit_per_minute: int = 20
    cors_origins: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> Settings:
        corpus = _resolve(Path(os.getenv("CORPUS_PATH", "data/corpus/rebt.json")))
        origins = tuple(o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip())
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "fake").strip().lower(),
            llm_base_url=os.getenv("LLM_BASE_URL", "").strip(),
            llm_api_key=os.getenv("LLM_API_KEY", "").strip(),
            llm_model=os.getenv("LLM_MODEL", "").strip(),
            llm_timeout_seconds=_float("LLM_TIMEOUT_SECONDS", 30.0),
            corpus_path=corpus,
            retrieval_top_k=_int("RETRIEVAL_TOP_K", 4),
            retrieval_min_score=_float("RETRIEVAL_MIN_SCORE", 1.0),
            rate_limit_per_minute=_int("RATE_LIMIT_PER_MINUTE", 20),
            cors_origins=origins,
        )
