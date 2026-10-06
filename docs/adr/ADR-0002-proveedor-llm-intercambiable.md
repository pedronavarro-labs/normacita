# ADR-0002 · Proveedor de LLM intercambiable (OpenAI-compatible + fake)

- **Estado:** aceptada · **Fecha:** 2026-10-06

## Contexto
Se quiere desplegar gratis y no depender de un proveedor concreto ni de una cuota. Los tests y el CI no deben usar claves ni red.

## Decisión
- Puerto `LLMProvider` con un método `generate(question, fragments) -> str`.
- Adaptador **`OpenAICompatibleProvider`** (httpx → `POST {LLM_BASE_URL}/chat/completions`), compatible con Gemini (endpoint OpenAI), Groq, OpenRouter, OpenAI y Ollama local, configurado solo con `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL`.
- Adaptador **`FakeLLMProvider`** determinista (extractivo) para desarrollo, tests y modo demo.
- Selección por `LLM_PROVIDER` en una *factory*.

## Alternativas
- SDK oficial de cada proveedor: más dependencias y acoplamiento.
- LiteLLM: muy completo, pero añade dependencia pesada para un único endpoint.

## Consecuencias
- ✅ Cambiar de proveedor = cambiar variables de entorno.
- ✅ CI sin secretos.
- ⚠️ Funciones específicas (p. ej. salida JSON estricta de un proveedor) requieren ampliar el adaptador.
- ⚠️ Revisar términos de uso y privacidad de la capa gratuita elegida (algunas usan los datos para entrenar). No enviar datos personales.
