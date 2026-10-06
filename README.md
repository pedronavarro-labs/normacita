# NormaCita · Normativa técnica con citas verificables

> Proyecto Final (TFM) del **Máster en Desarrollo con IA** (The Big School) · Autor: **Pedro Navarro Arocha**
> Estado: 🚧 *walking skeleton* (v0.1). Funciona de extremo a extremo en modo demo; ver [ROADMAP](docs/ROADMAP.md).

| Enlace | URL |
|---|---|
| 🌐 Demo desplegada | `PENDIENTE — https://…` |
| 📊 Slides (públicas) | `PENDIENTE — https://…` |
| 🎬 Vídeo de presentación | `PENDIENTE — https://…` |
| 💻 Repositorio | `PENDIENTE — https://github.com/…/normacita` |

## a. Descripción general
Quienes trabajan con normativa técnica pierden tiempo buscando **qué artículo exacto** regula algo, y los chats de IA genéricos responden sin citar o inventan artículos. **NormaCita** responde preguntas en lenguaje natural **siempre con citas numeradas** al artículo y apartado del texto consolidado del BOE, con el fragmento literal y su enlace. Si el corpus no cubre la pregunta, **lo dice y no responde**.

Corpus inicial: **Reglamento Electrotécnico para Baja Tensión (REBT)**, Real Decreto 842/2002 ([BOE-A-2002-18099](https://www.boe.es/buscar/act.php?id=BOE-A-2002-18099)). La v0.1 incluye una **muestra de 18 apartados** (arts. 1, 2, 3, 4 y 16); el script de ingesta permite cargar la norma completa.

> ⚠️ Herramienta orientativa: no sustituye al texto oficial ni al criterio profesional.

## b. Stack tecnológico
| Capa | Tecnología | Por qué |
|---|---|---|
| Backend / API | Python 3.11+, **FastAPI**, Pydantic v2, Uvicorn | Ecosistema IA en Python, validación tipada, OpenAPI automático |
| Recuperación (RAG) | BM25 propio en Python puro | Determinista, gratis y testeable ([ADR-0003](docs/adr/ADR-0003-recuperacion-bm25-primero.md)) |
| IA generativa | Cualquier API **OpenAI-compatible** (Gemini, Groq, OpenRouter, Ollama) vía httpx · proveedor **fake** sin claves | Proveedor intercambiable por entorno ([ADR-0002](docs/adr/ADR-0002-proveedor-llm-intercambiable.md)) |
| Frontend | HTML + CSS + JavaScript sin framework | Mínimo y seguro (CSP estricta, sin `innerHTML`) |
| Calidad | pytest + pytest-cov, ruff (lint + formato + reglas de seguridad) | |
| Infra | Docker (usuario no root), GitHub Actions (CI), despliegue previsto en Render/Fly.io | |
| Datos | API de datos abiertos del BOE → JSON | Fuente oficial y pública |

Arquitectura hexagonal; diagramas en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## c. Instalación y ejecución

**Requisitos:** Python ≥ 3.11 (o Docker). Recomendado: [uv](https://docs.astral.sh/uv/).

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

**Con un LLM real** (edita `.env`; nunca subas ese archivo):
```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai   # ejemplo: Gemini
LLM_API_KEY=tu_clave
LLM_MODEL=nombre-del-modelo
```

**Con Docker:**
```bash
docker build -t normacita .
docker run --rm -p 8000:8000 --env-file .env normacita
```

**Ampliar el corpus desde el BOE:**
```bash
python scripts/ingest_boe.py --id BOE-A-2002-18099 \
  --norma "REBT (Real Decreto 842/2002), Reglamento electrotécnico para baja tensión" \
  --salida data/corpus/rebt.json            # sin --bloques: todos los artículos
# y después: CORPUS_PATH=data/corpus/rebt.json
```

**Despliegue:** `PENDIENTE` (previsto: Render/Fly.io desde el Dockerfile, variables `LLM_*` configuradas en el panel del proveedor).

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
├── data/corpus/           # Corpus normativo en JSON (muestra REBT)
├── scripts/ingest_boe.py  # Ingesta desde la API de datos abiertos del BOE
├── tests/                 # 30 tests (unitarios + API), sin red ni claves
├── docs/                  # Especificación, arquitectura, ADRs, roadmap, registro de IA
├── .github/workflows/     # CI: lint, tests, build y smoke test de Docker
├── Dockerfile · .env.example · AGENTS.md · pyproject.toml
```

## e. Funcionalidades principales
- ✅ Pregunta en lenguaje natural → respuesta con **citas numeradas** [n] al artículo y apartado.
- ✅ Visor de la fuente: texto literal + enlace al BOE por cada cita.
- ✅ **«Sin base normativa»**: si nada relevante supera el umbral, no responde ni llama al LLM.
- ✅ Validación de citas: se eliminan los marcadores que el modelo invente.
- ✅ Proveedor de IA intercambiable (modo demo sin claves).
- ✅ Seguridad: validación de entradas, rate limit por IP, CSP y cabeceras, errores genéricos.
- ⏳ Corpus REBT completo + ITC-BT · evaluación automática de la precisión de cita · despliegue público · feedback 👍/👎.

API:
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado y proveedor activo |
| POST | `/api/ask` | `{"pregunta": "..."}` → `{respuesta, citas[], sin_base, proveedor}` |
| GET | `/` | Interfaz web |

## f. Usuario y contraseña de prueba
No aplica en la v0.1: la app es pública y **no tiene login**. Si se añade el panel de administración (HU-14), aquí irán las credenciales de prueba.

---
Licencia: `PENDIENTE de elegir` · Uso de IA en el desarrollo: [docs/REGISTRO-IA.md](docs/REGISTRO-IA.md) · Reglas para agentes: [AGENTS.md](AGENTS.md)
