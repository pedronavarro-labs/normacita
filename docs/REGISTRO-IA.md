# Registro de uso de IA en el desarrollo

> Valorado en el máster: transparencia sobre cómo se ha usado la IA (V-DPF2 0:47:43, 0:50:05). Añade una entrada por sesión relevante. **Debes entender y saber explicar todo el código**, lo haya escrito quien lo haya escrito.

| Fecha | Herramienta / agente | Qué se pidió | Qué se generó | Revisión humana / cambios |
|---|---|---|---|---|
| 2026-10-06 | Grok Bot (asistente de Pedro) | Elegir una idea entre 5 con criterios y arrancar el proyecto | `DECISION.md`, especificación, arquitectura, ADR-0001…0004, roadmap, walking skeleton (FastAPI, BM25, proveedores LLM fake y OpenAI-compatible, UI, 30 tests, Dockerfile, CI) y muestra del corpus REBT (18 apartados copiados del BOE) | ⏳ Pendiente de que Pedro revise y ajuste. Commits iniciales generados con asistente IA y reasignados al autor (Pedro) antes de publicar |
| 2026-10-06 | Grok Bot (asistente de Pedro) | Avanzar el proyecto tras publicar el repo: corpus completo, evaluación, mejora de la recuperación y preparar despliegue | Ingesta BOE en dos pasos (XML → JSON) ejecutada en GitHub Actions porque la red del asistente no llegaba a boe.es; corpus completo (82 XML oficiales, 832 fragmentos); 52 preguntas de evaluación con cita esperada **extraída del texto real**; `normacita.evaluation` + umbrales en CI; BM25 con stemming, campo título, penalización de exclusiones, prior y umbral de cobertura; `render.yaml`, `DEPLOY.md`, `docs/EVALUACION.md` | El asistente detectó **sobreajuste** (con prior ×1,5 el subconjunto de validación bajaba a hit@1 0.333) y eligió ×1,2; se documenta que esa elección miró la validación. ⏳ Pedro: revisar preguntas/citas de `eval/preguntas.json`, el corpus y los parámetros; crear las cuentas (Render, LLM) él mismo |
| 2026-10-06 | Grok Bot (asistente de Pedro) | Pulir la UI para la demo y preparar slides y vídeo | UI renovada (chips de ejemplo y de citas, estados de carga/sin base/error, insignia demo, responsive, accesible, sin `innerHTML`), tests de UI, capturas con Chrome headless (`docs/img/`), borradores de `GUION-SLIDES.md`, `GUION-VIDEO.md` y `.pptx` generado con `scripts/generar_slides.py` | La captura de error simula la respuesta 502 real de la API. ⏳ Pedro: reescribir con sus palabras los textos en primera persona y completar los `[PENDIENTE]` |

## Cómo usar este registro
- Anota los prompts importantes (o el enlace a la conversación), las decisiones que tomaste **tú** y lo que corregiste.
- Si un agente usa `AGENTS.md`, anota cuándo cambiaste sus reglas y por qué.
- En la presentación, resume: qué aceleró la IA, dónde se equivocó y cómo lo detectaste (tests, evaluación, revisión).
