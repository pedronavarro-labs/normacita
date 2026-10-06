import json

import httpx
import pytest

from normacita.application.ports import LLMError
from normacita.config import Settings
from normacita.infrastructure.llm.factory import build_llm_provider
from normacita.infrastructure.llm.fake_provider import FakeLLMProvider
from normacita.infrastructure.llm.openai_compatible import OpenAICompatibleProvider
from normacita.infrastructure.llm.prompts import build_user_prompt


def test_fake_cita_el_primer_fragmento(fragments):
    out = FakeLLMProvider().generate("¿objeto?", fragments[:2])
    assert "[1]" in out and "[2]" in out


def test_prompt_numera_y_delimita(fragments):
    prompt = build_user_prompt("¿Qué es?", fragments[:2])
    assert prompt.startswith("FRAGMENTOS:") and "[2]" in prompt and "<<<" in prompt


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_compatible_envia_payload_y_lee_respuesta(fragments):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Hola [1]"}}]})

    provider = OpenAICompatibleProvider(
        "https://llm.example/v1/", "clave-de-prueba", "modelo-x", client=_client(handler)
    )
    assert provider.generate("¿?", fragments[:1]) == "Hola [1]"
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["auth"] == "Bearer clave-de-prueba"
    assert seen["body"]["model"] == "modelo-x"
    assert seen["body"]["messages"][0]["role"] == "system"


def test_openai_compatible_error_http_se_traduce(fragments):
    provider = OpenAICompatibleProvider(
        "https://llm.example/v1", "", "m", client=_client(lambda r: httpx.Response(500))
    )
    with pytest.raises(LLMError):
        provider.generate("¿?", fragments[:1])


def test_openai_compatible_respuesta_malformada(fragments):
    provider = OpenAICompatibleProvider(
        "https://llm.example/v1", "", "m", client=_client(lambda r: httpx.Response(200, json={}))
    )
    with pytest.raises(LLMError):
        provider.generate("¿?", fragments[:1])


def test_factory():
    assert build_llm_provider(Settings(llm_provider="fake")).name == "fake"
    with pytest.raises(ValueError):
        build_llm_provider(Settings(llm_provider="desconocido"))
    with pytest.raises(ValueError):  # falta base_url/model
        build_llm_provider(Settings(llm_provider="openai_compatible"))


def test_settings_no_muestra_la_clave():
    assert "secreta" not in repr(Settings(llm_api_key="secreta"))
