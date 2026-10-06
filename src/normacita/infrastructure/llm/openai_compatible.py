"""Proveedor para cualquier API compatible con OpenAI `/chat/completions`.

Con un único adaptador se puede usar Gemini, Groq, OpenRouter, OpenAI u Ollama
(local) cambiando solo variables de entorno. Ver docs/adr/ADR-0002.
"""

from __future__ import annotations

import httpx

from normacita.application.ports import LLMError
from normacita.domain.models import Fragment
from normacita.infrastructure.llm.prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url or not model:
            raise ValueError("LLM_BASE_URL y LLM_MODEL son obligatorios para openai_compatible")
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._model = model
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        # `client` inyectable: en los tests se pasa un httpx.MockTransport (sin red).
        self._client = client or httpx.Client(timeout=timeout, headers=headers)
        if client is not None and headers:
            self._client.headers.update(headers)

    def generate(self, question: str, fragments: list[Fragment]) -> str:
        payload = {
            "model": self._model,
            "temperature": 0,  # respuestas lo más deterministas posible
            "max_tokens": 400,  # tope de coste por respuesta
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, fragments)},
            ],
        }
        try:
            resp = self._client.post(self._url, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            # No propagamos detalles (podrían incluir cabeceras o la clave).
            raise LLMError(f"Fallo del proveedor de IA ({type(exc).__name__})") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMError("Respuesta vacía del proveedor de IA")
        return content.strip()
