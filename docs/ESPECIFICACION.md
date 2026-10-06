# Especificación funcional — NormaCita

> Versión 0.1 (06/10/2026). Documento vivo: actualízalo cuando cambie el alcance.

## 1. Problema
Quienes trabajan con normativa técnica (instaladores, ingenieros, técnicos de prevención, estudiantes) pierden tiempo buscando **qué artículo exacto** dice algo en normas largas, con muchas modificaciones. Los chats de IA genéricos responden con seguridad pero **sin citar** o citando artículos inventados, y en un dominio regulado eso no sirve.

## 2. Propuesta de valor
Preguntas en lenguaje natural → respuesta breve **siempre respaldada por citas** al artículo/apartado del texto **consolidado y oficial** (BOE), con enlace a la fuente. Si no hay base en el corpus, **lo dice y no responde**.

## 3. Usuarios (personas)
| Persona | Necesidad | Contexto |
|---|---|---|
| **Instalador/a electricista** | Comprobar rápido un requisito en obra | Móvil, poco tiempo, necesita el artículo para justificar |
| **Ingeniero/a proyectista** | Localizar la referencia exacta para una memoria técnica | Escritorio, quiere copiar la cita |
| **Estudiante de FP/grado** | Entender la norma mientras estudia | Quiere la explicación y el texto literal |
| **Administrador/a del corpus** (fase posterior) | Actualizar la norma cuando el BOE publica cambios | Ejecuta la ingesta y revisa la evaluación |

## 4. Historias de usuario

### MVP (imprescindible para entregar)
**HU-01 · Preguntar y obtener respuesta con citas** ✅ *(walking skeleton)*
Como profesional, quiero escribir una pregunta y recibir una respuesta con citas numeradas para verificarla en la norma.
- Dado un corpus cargado, cuando pregunto «¿Qué tensiones se consideran baja tensión?», entonces recibo una respuesta con al menos una cita [n] que apunta al Artículo 4 del REBT con enlace `https://www.boe.es/...`.
- Cada marcador [n] del texto corresponde a una cita devuelta; los marcadores inventados por el modelo se eliminan.
- La respuesta incluye el aviso de que es orientativa.

**HU-02 · No responder sin base** ✅
Como profesional, quiero que el sistema me diga que no sabe cuando la norma no cubre la pregunta, para no fiarme de una invención.
- Dada una pregunta ajena al corpus («receta de paella»), entonces `sin_base = true`, no hay citas y **no se llama al LLM** (coste 0).

**HU-03 · Ver el texto literal de la fuente** ✅
Como ingeniero/a, quiero ver el fragmento literal citado y un enlace al BOE para copiarlo en mi memoria.
- Cada cita muestra artículo, apartado, título, texto literal y enlace oficial (solo `https://`).

**HU-04 · Entradas validadas y uso limitado** ✅
Como responsable del servicio, quiero validar las preguntas y limitar peticiones para evitar abuso y gasto.
- Preguntas de 3 a 500 caracteres; caracteres de control eliminados; si no → HTTP 422.
- Más de N peticiones/minuto por IP → HTTP 429 (N configurable).
- Fallo del proveedor de IA → HTTP 502 con mensaje genérico (sin detalles internos).

**HU-05 · Corpus REBT completo desde el BOE** ✅ (v0.2: arts. 1-29 + ITC-BT-01…52, 832 fragmentos)
Como administrador/a, quiero ingerir el REBT completo (articulado + ITC-BT) desde la API del BOE para que el asistente cubra la norma entera.
- `scripts/ingest_boe.py` genera un JSON con todos los artículos divididos por apartado y la fecha de consulta.
- El corpus indica la versión consolidada usada.

**HU-06 · Respuesta generada por un LLM real** ⏳
Como usuario/a, quiero respuestas redactadas (no solo extractos) cuando hay un proveedor configurado.
- Con `LLM_PROVIDER=openai_compatible` y credenciales válidas, la respuesta se genera con el prompt versionado y conserva las citas.
- Sin credenciales, la app sigue funcionando en modo demo (*fake*).

**HU-07 · Evaluación automática de calidad** ✅ (v0.2: 52 preguntas, umbrales en CI; ver `docs/EVALUACION.md`)
Como desarrollador, quiero un conjunto de ≥ 20 preguntas de referencia con su artículo esperado y medir la *precisión de cita* en CI.
- `pytest -m eval` (o script) calcula *hit@k* del recuperador; el CI falla si baja de un umbral acordado (p. ej. 0,8).

**HU-08 · Despliegue público** ⏳ (preparado: `render.yaml` + `DEPLOY.md`; falta crear la cuenta y desplegar)
Como evaluador/a del TFM, quiero una URL pública para probar la app sin instalar nada.
- URL en el README; `/health` responde 200; modo demo si no hay cuota de IA.

### Después del MVP (si da tiempo)
- HU-09 Feedback 👍/👎 por respuesta (persistido) para mejorar la evaluación.
- HU-10 Historial de consultas (local en el navegador, sin cuentas).
- HU-11 Búsqueda híbrida BM25 + embeddings (pgvector) — ver ADR-0003.
- HU-12 Varias normas (ITC-BT, CTE, RITE) con filtro por norma.
- HU-13 Trazas LLMOps: latencia, tokens y coste por respuesta.
- HU-14 Login de administrador para lanzar la ingesta desde la web (implicaría usuario/contraseña de prueba en el README).

## 5. Requisitos no funcionales
| Id | Requisito | Cómo se comprueba |
|---|---|---|
| RNF-01 | Sin secretos en el repo; configuración por entorno | `.env` en `.gitignore`, `.env.example`, revisión en CI (añadir gitleaks, roadmap) |
| RNF-02 | Seguridad web: CSP, nosniff, anti-clickjacking, render seguro (sin `innerHTML`) | Test `test_cabeceras_de_seguridad` |
| RNF-03 | OWASP LLM: prompt injection (LLM01), salida no fiable (LLM05), consumo ilimitado (LLM10) | Prompt de sistema + citas validadas + `max_tokens` + rate limit |
| RNF-04 | Tests sin red ni claves; cobertura del core ≥ 80 % | `pytest` en CI con proveedor fake |
| RNF-05 | Latencia p95 < 5 s con LLM real | Medición en el despliegue (roadmap) |
| RNF-06 | Arranca con un comando (local y Docker) | README §c |

## 6. Fuera de alcance
Asesoramiento legal o profesional vinculante; normas autonómicas o privadas (UNE) con derechos de autor; apps móviles nativas; pagos.
