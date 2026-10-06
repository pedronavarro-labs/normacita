"""Elige el proveedor de IA según la configuración (patrón factory)."""

from __future__ import annotations

from normacita.application.ports import LLMProvider
from normacita.config import Settings
from normacita.infrastructure.llm.fake_provider import FakeLLMProvider
from normacita.infrastructure.llm.openai_compatible import OpenAICompatibleProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "fake":
        return FakeLLMProvider()
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
        )
    raise ValueError(f"LLM_PROVIDER desconocido: {settings.llm_provider!r}")
