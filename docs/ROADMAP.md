# Roadmap — NormaCita (ritmo A, ~4 semanas)

> Mapeado a las fases de [`PLAN.md`](../../../PLAN.md) y a las secciones de [`CHECKLIST.md`](../../../CHECKLIST.md) de la carpeta del TFM. Las fechas son relativas (S1 = semana en que empiezas). **La fecha límite de entrega de la 3.ª edición no aparece en ninguna fuente: confírmala** (CHECKLIST A).
> Leyenda: ✅ hecho en el arranque · ⏳ pendiente · ⭐ recomendable si sobra tiempo.

## Semana 0 · Arranque (hecho el 06/10/2026)
| Tarea | Fase PLAN | Checklist |
|---|---|---|
| ✅ Elegir idea con tabla de criterios (`DECISION.md`) | 1 | B |
| ✅ Especificación, arquitectura, 4 ADRs | 2, 3 | C (+ADR) |
| ✅ Walking skeleton: pregunta → BM25 → LLM fake → respuesta con citas; UI; 30 tests | 4, 5, 6 | D |
| ✅ Seguridad base (validación, rate limit, CSP, secretos por entorno) | 7 | C, D |
| ✅ Dockerfile + workflow CI | 8 | D |

## Avance v0.2 (06/10/2026)
Repo público, corpus completo, evaluación en CI, BM25 mejorado y despliegue preparado. Detalle en las tablas (✅) y en `docs/REGISTRO-IA.md`.

## Semana 1 · Hazlo tuyo y publícalo
| Tarea | Fase | Checklist |
|---|---|---|
| ⏳ Leer el código capa a capa y ejecutar los tests en tu máquina (README §c). Anota dudas en `REGISTRO-IA.md` | 0, 4 | D («entiendes el código») |
| ⏳ Revisar `DECISION.md` y `ESPECIFICACION.md`: ajustar persona, nicho y alcance a tu experiencia real | 1, 2 | B |
| ✅ Autor de los commits a tu nombre y **repo público en GitHub** (<https://github.com/pedronavarro-labs/normacita>) | 4 | C |
| ✅ CI de GitHub Actions en verde (lint, 51 tests con umbrales de evaluación, build + smoke test Docker) | 8 | D |
| ✅ REBT completo ingerido desde el XML oficial del BOE (arts. 1-29 + ITC-BT-01…52, 832 fragmentos) vía workflow «Ingesta BOE (manual)». ⏳ Revísalo por encima (algunas ITC con tablas largas) | 5 | B (HU-05) |
| ⏳ Confirmar la fecha límite de entrega y si eres alumno Fundae | 0 | A |

## Semana 2 · IA real y calidad medible
| Tarea | Fase | Checklist |
|---|---|---|
| ⏳ Crear clave de un proveedor gratuito (Gemini/Groq/OpenRouter) y probar `LLM_PROVIDER=openai_compatible` en local (HU-06) | 5 | D |
| ✅ Conjunto de evaluación: 52 preguntas (42 con cita + 10 fuera de ámbito; subconjuntos ajuste/validación) en `eval/preguntas.json` + umbrales en CI (HU-07, `docs/EVALUACION.md`). ⏳ Ampliar con preguntas reales y negativas «cercanas» | 6 | D |
| ✅ Mejoras de BM25 medidas (stemming, campo título, exclusiones, prior, umbral de cobertura): hit@1 0.548→0.714, hit@3 0.738→0.952, negativas 0.30→1.00 | 5, 6 | D |
| ✅ ITC-BT ingeridas · ⏳ filtro por norma/ITC en la UI | 5 | B |
| ⭐ Búsqueda híbrida (embeddings + RRF) si la evaluación muestra fallos por sinónimos (ADR-0003) | 5 | D |

## Semana 3 · Seguridad, despliegue y observabilidad
| Tarea | Fase | Checklist |
|---|---|---|
| 🟡 Despliegue **preparado** (`render.yaml`, `DEPLOY.md`). ⏳ 👤 Crear cuenta en Render y aplicar el Blueprint; variables `LLM_*` en el panel (nunca en el repo) | 8 | E |
| ⏳ Añadir CD: despliegue automático desde `main` tras CI verde | 8 | D |
| ⏳ Tests adversarios de prompt injection (preguntas que intentan saltarse las reglas) | 7 | D (OWASP LLM) |
| ⏳ gitleaks + pip-audit/Dependabot en CI; CORS restringido | 7 | C, D |
| ⏳ Logs estructurados con latencia/tokens por respuesta (LLMOps) | 6 | D |
| ⭐ Feedback 👍/👎 (HU-09) e historial local (HU-10) | 5 | B |

## Semana 4 · Documentación, presentación y entrega
| Tarea | Fase | Checklist |
|---|---|---|
| ⏳ README final: 6 puntos (a–f), URLs de despliegue, slides y vídeo; capturas | 9 | F |
| ⏳ Slides públicas: problema → solución → arquitectura → demo → IA → seguridad → aprendizajes (`plantilla/docs/presentacion/guion-slides.md`) | 10 | G |
| ⏳ Vídeo con captura de pantalla (5-10 min) y enlace público | 10 | H |
| ⏳ Prueba en incógnito de todos los enlaces; alguien ajeno sigue el README | 11 | F, G, H, I |
| ⏳ Rellenar y **enviar tú** el Typeform de la lección «Proyecto Final» | 11 | I |

## Riesgos del calendario
- El REBT completo con ITC-BT es largo: si la ingesta da problemas, entrega con el articulado + 3-5 ITC clave (BT-10, BT-19, BT-25…) y documenta el alcance.
- Si la cuota gratuita de IA falla durante la corrección, el despliegue debe arrancar en modo demo (`LLM_PROVIDER=fake`) y avisarlo en el README.
