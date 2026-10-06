# NormaCita

Consultas sobre el REBT con la cita exacta del BOE en cada respuesta.

Es mi Proyecto Final (TFM) del Máster en Desarrollo con IA de The Big School. Autor: Pedro Navarro Arocha.

Estado: v0.2. El corpus del REBT está completo, la evaluación corre en el CI y hay una demo pública en Render. Funciona de principio a fin en modo demo, es decir, sin un modelo de IA detrás. Lo que falta está en el [ROADMAP](docs/ROADMAP.md).

| Enlace | URL |
|---|---|
| Demo | https://normacita.onrender.com (modo demo; pasos en [DEPLOY.md](DEPLOY.md)) |
| Slides | {{URL_SLIDES}} ([guion](docs/presentacion/GUION-SLIDES.md) · [.pptx](docs/presentacion/NormaCita-slides.pptx)) |
| Vídeo | {{URL_VIDEO}} ([guion](docs/presentacion/GUION-VIDEO.md)) |
| Repositorio | https://github.com/pedronavarro-labs/normacita |
| Memoria (opcional) | [docs/MEMORIA.md](docs/MEMORIA.md) |

## a. Descripción general
Encontrar qué apartado concreto del REBT regula algo lleva su tiempo. Y si se lo preguntas a un chat de IA genérico, lo normal es que conteste muy seguro sin decir de dónde lo saca, o que cite un artículo que no existe.

NormaCita contesta preguntas escritas con tus palabras y cada respuesta lleva citas numeradas al artículo y apartado del texto consolidado del BOE, con el fragmento literal y su enlace. Si la norma no cubre la pregunta, no contesta y lo dice («Sin base en la norma»).

El corpus es el Reglamento Electrotécnico para Baja Tensión (REBT), Real Decreto 842/2002 ([BOE-A-2002-18099](https://www.boe.es/buscar/act.php?id=BOE-A-2002-18099)), y en la v0.2 está entero: los artículos 1 a 29 del Real Decreto y las 52 ITC-BT. Lo he troceado por apartados en 832 fragmentos (`data/corpus/rebt.json`) a partir del XML oficial de la API de datos abiertos del BOE (`data/raw/rebt/`).

> Es una herramienta orientativa. No sustituye al texto oficial ni al criterio de un profesional.

### Capturas (modo demo, sin LLM)
| Inicio | Respuesta con citas desplegadas |
|---|---|
| ![Pantalla de inicio con ejemplos de preguntas](docs/img/01-inicio.png) | ![Respuesta con citas numeradas y el texto literal del BOE desplegado](docs/img/02-respuesta-con-citas.png) |
| **Sin base en la norma** | **Móvil** |
| ![Pregunta ajena al REBT rechazada](docs/img/03-sin-base.png) | ![Vista móvil con una respuesta y su cita](docs/img/04-movil-respuesta.png) |

Hay más capturas: [error del servicio de IA](docs/img/05-error.png), [validación de la pregunta](docs/img/06-validacion.png) e [inicio en móvil](docs/img/04a-movil-inicio.png).

## b. Stack tecnológico
| Capa | Tecnología | Motivo |
|---|---|---|
| Backend / API | Python 3.11+, FastAPI, Pydantic v2, Uvicorn | Casi todo lo de IA está en Python, y FastAPI da validación tipada y OpenAPI sin esfuerzo |
| Recuperación (RAG) | BM25 propio en Python puro (stemming ligero, campo título, umbral de cobertura) | Es determinista, no cuesta nada y se puede testear ([ADR-0003](docs/adr/ADR-0003-recuperacion-bm25-primero.md)) |
| IA generativa | Cualquier API compatible con OpenAI (Gemini, Groq, OpenRouter, Ollama) vía httpx, y un proveedor *fake* que no necesita claves | El proveedor se cambia con variables de entorno ([ADR-0002](docs/adr/ADR-0002-proveedor-llm-intercambiable.md)) |
| Frontend | HTML, CSS y JavaScript sin framework, responsive y accesible (teclado, foco visible, ARIA) | Poco código y fácil de asegurar: CSP estricta, sin `innerHTML` y sin scripts ni estilos en línea |
| Calidad | pytest + pytest-cov, ruff (lint, formato y reglas de seguridad) | |
| Infra | Docker (usuario no root), GitHub Actions (CI), despliegue en Render (plan free; alternativa Fly.io) | |
| Datos | API de datos abiertos del BOE → JSON | Es la fuente oficial y es pública |

La arquitectura es hexagonal. Los diagramas están en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## c. Instalación y ejecución

Necesitas Python 3.11 o superior (o Docker). Recomiendo [uv](https://docs.astral.sh/uv/), aunque no es obligatorio.

```bash
# 1. Entorno e instalación (con uv)
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
#    (alternativa sin uv: python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]")

# 2. Configuración (por defecto modo demo, sin claves)
cp .env.example .env
set -a && source .env && set +a      # carga las variables en la sesión

# 3. Arrancar
uvicorn normacita.main:app --reload
# → http://localhost:8000  (UI)  ·  http://localhost:8000/docs  (OpenAPI)

# 4. Calidad
ruff format --check . && ruff check .
pytest
```

Para usar un LLM real, edita `.env` (y no lo subas nunca al repositorio):
```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai   # ejemplo: Gemini
LLM_API_KEY=tu_clave
LLM_MODEL=nombre-del-modelo
```

Con Docker:
```bash
docker build -t normacita .
docker run --rm -p 8000:8000 --env-file .env normacita
```

Para regenerar el corpus desde el BOE hay dos pasos, primero el XML crudo y luego el JSON:
```bash
python scripts/ingest_boe.py descargar      # guarda el XML oficial en data/raw/rebt/
python scripts/ingest_boe.py construir      # genera data/corpus/rebt.json (añade --sin-itc para solo el articulado)
```
Si desde tu red no se llega a `boe.es`, lanza el workflow manual «Ingesta BOE (manual)» en GitHub Actions y descarga el artefacto `corpus-boe` (`gh run download`).

La evaluación de calidad usa 52 preguntas y el proveedor fake, y también se ejecuta en el CI:
```bash
python -m normacita.evaluation       # hit@1, hit@3, cobertura y acierto en negativas
```
Resultados actuales: hit@1 0.714, hit@3 0.952 y negativas 1.00. En el subconjunto de validación baja a 0.50 / 0.917 / 1.00. La metodología y el detalle están en [docs/EVALUACION.md](docs/EVALUACION.md).

Despliegue: la app está publicada en Render, en <https://normacita.onrender.com> (`render.yaml`, plan free, modo demo con el proveedor *fake*). Al ser el plan gratuito, la instancia se duerme tras unos 15 min sin tráfico y la primera petición tarda un rato mientras despierta. También se puede desplegar en Fly.io. El paso a paso, y cómo sacar claves gratuitas de LLM, está en [DEPLOY.md](DEPLOY.md).

## d. Estructura del proyecto
```
normacita/
├── src/normacita/
│   ├── domain/            # Modelos de negocio (Fragment, Citation, Answer). Sin dependencias.
│   ├── application/       # Puertos (Retriever, LLMProvider) y caso de uso AskQuestion
│   ├── infrastructure/    # Adaptadores: corpus JSON, BM25, proveedores LLM (fake / OpenAI-compatible)
│   ├── api/               # FastAPI: endpoints, validación, seguridad, UI estática
│   ├── config.py          # Configuración desde variables de entorno
│   └── main.py            # Punto de entrada ASGI
├── data/raw/rebt/         # XML oficial del BOE (82 ficheros: índice + 29 artículos + 52 ITC)
├── data/corpus/rebt.json  # Corpus REBT completo troceado por apartado
├── eval/preguntas.json    # 52 preguntas de evaluación con la cita esperada
├── scripts/               # ingest_boe.py (BOE), generar_slides.py y generar_memoria.py (documentación)
├── tests/                 # 57 tests (unitarios, API, UI, ingesta y evaluación), sin red ni claves
├── docs/                  # Especificación, arquitectura, ADRs, evaluación, capturas (img/), presentación, registro de IA
├── .github/workflows/     # CI (lint, tests, Docker) + ingesta BOE manual
├── Dockerfile · render.yaml · DEPLOY.md · .env.example · AGENTS.md · pyproject.toml
```

## e. Funcionalidades principales
Lo que ya funciona:
- Preguntas en lenguaje natural con respuesta y citas numeradas [n] al artículo y apartado.
- Las citas salen como *chips* clicables (y como marcadores [n] en el texto). Al pulsarlas se ve el texto literal del BOE y su enlace.
- Preguntas de ejemplo, indicador de carga, mensajes claros cuando no hay base o hay un error, e insignia de «Modo demo».
- «Sin base normativa»: si ningún fragmento supera los umbrales de puntuación y cobertura, no responde y tampoco llama al LLM.
- El REBT completo (arts. 1-29 e ITC-BT-01 a 52) sacado del XML oficial del BOE.
- Evaluación automática en el CI (hit@1 y hit@3 de la cita, acierto en negativas).
- Si el modelo se inventa un marcador de cita, se elimina antes de responder.
- Proveedor de IA intercambiable, con un modo demo que no necesita claves.
- Seguridad básica: validación de entradas, rate limit por IP, CSP y cabeceras, errores genéricos.
- Despliegue público en Render: https://normacita.onrender.com (modo demo; plan free, se duerme tras ~15 min sin tráfico).

Pendiente: LLM real en producción, búsqueda híbrida y botones de feedback (útil / no útil).

API:
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado y proveedor activo |
| POST | `/api/ask` | `{"pregunta": "..."}` → `{respuesta, citas[], sin_base, proveedor}` |
| GET | `/` | Interfaz web |

## f. Usuario y contraseña de prueba
No aplica en la v0.2. La app es pública y no tiene login. Si más adelante añado el panel de administración (HU-14), las credenciales de prueba irán aquí.

---
Licencia: [MIT](LICENSE) · Uso de IA en el desarrollo: [docs/REGISTRO-IA.md](docs/REGISTRO-IA.md) · Reglas para agentes: [AGENTS.md](AGENTS.md)
