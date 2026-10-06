# ADR-0004 · Controles de seguridad base (OWASP Web/API + OWASP LLM Top 10)

- **Estado:** aceptada · **Fecha:** 2026-10-06

## Contexto
La app es pública, sin login en el MVP, y llama a un LLM de pago o con cuota. Riesgos principales: abuso/coste, prompt injection, XSS por salida del modelo, fuga de secretos y desinformación (citas falsas).

## Decisión
1. **Validación de entrada** con Pydantic (longitud 3-500, sin caracteres de control).
2. **Rate limit** por IP en memoria (configurable) → 429.
3. **Cabeceras:** CSP `default-src 'self'; frame-ancestors 'none'`, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`.
4. **Render seguro** en la UI: solo `textContent`; enlaces solo `https://` con `rel="noopener noreferrer"`.
5. **Prompt de sistema** con reglas y delimitadores; fragmentos tratados como datos (LLM01).
6. **Validación de la salida:** solo se aceptan citas [n] existentes (LLM05/LLM09).
7. **Límites de coste:** `max_tokens`, sin LLM si no hay base (LLM10).
8. **Secretos** solo por entorno; `repr=False`; errores 502 genéricos; contenedor no root; token de CI con `contents: read`.

## Pendiente (roadmap)
gitleaks/secret scanning en CI, `pip-audit`/Dependabot, tests de inyección con preguntas adversarias, CORS restringido en producción, rate limit compartido si hay varias réplicas.

## Consecuencias
- ✅ Cubre los riesgos más probables con poco código y tests que lo demuestran.
- ⚠️ El rate limit en memoria se reinicia con cada despliegue y no se comparte entre instancias.
