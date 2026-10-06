# AGENTS.md — reglas para agentes de IA en este repo

Contexto para cualquier asistente (Cursor, Claude Code, Copilot, Codex…) que trabaje aquí.

## Proyecto
NormaCita: asistente RAG que responde sobre normativa técnica **siempre con citas** al artículo/apartado. Python 3.11+, FastAPI, arquitectura hexagonal (`src/normacita/{domain,application,infrastructure,api}`).

## Reglas
1. **Respeta las capas:** `domain` no importa nada externo; `application` solo `domain` y `ports`; los adaptadores viven en `infrastructure`. Nada de lógica de negocio en `api/app.py`.
2. **Tests primero o a la vez:** todo cambio de comportamiento con su test en `tests/`. Los tests **no usan red ni claves** (usa `FakeLLMProvider`, stubs o `httpx.MockTransport`).
3. Antes de terminar: `ruff format . && ruff check . && pytest` en verde.
4. **Seguridad:** nunca escribas claves en código, tests ni docs; usa variables de entorno y actualiza `.env.example`. En la UI, nunca `innerHTML` con datos del servidor.
5. **Citas:** no cambies el contrato de citas [n] sin actualizar `AskQuestion`, la UI y los tests.
6. El corpus solo procede de **fuentes oficiales públicas** (BOE). No inventes texto normativo.
7. Cambios de arquitectura → nuevo ADR en `docs/adr/`.
8. Registra el trabajo relevante con IA en `docs/REGISTRO-IA.md`.
9. Mensajes de commit en español, en imperativo y con prefijo convencional (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
