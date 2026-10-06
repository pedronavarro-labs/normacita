# Despliegue de NormaCita

> Objetivo: una **URL pública** para que el tribunal del TFM pruebe la app sin instalar nada (HU-08).
> La app arranca siempre en **modo demo** (`LLM_PROVIDER=fake`, sin claves): responde con extractos literales y citas. Con una clave de un LLM gratuito pasa a redactar respuestas.
> **Ninguna cuenta se ha creado por ti**: los pasos marcados con 👤 los tienes que hacer tú.
> **Estado actual:** desplegado en Render (plan free, modo demo) en <https://normacita.onrender.com>.

## 0. Requisitos
- Repositorio público: <https://github.com/pedronavarro-labs/normacita> (CI en verde en `main`).
- Endpoint de salud: `GET /health` → `200 {"status":"ok", ...}` (lo usan Render y el smoke test del CI).
- El contenedor escucha en `$PORT` (Render/Fly lo inyectan; por defecto 8000) con usuario no root.

## 1. Render (recomendado, plan gratuito)
El repo incluye [`render.yaml`](render.yaml) (Blueprint): servicio web Docker, plan `free`, health check `/health`, modo demo por defecto.

1. 👤 Crea una cuenta en <https://render.com> entrando con **GitHub** (no pide tarjeta para el plan free).
2. 👤 Autoriza a Render a leer el repositorio `pedronavarro-labs/normacita` (puedes limitarlo a ese repo).
3. En el panel: **New → Blueprint** → elige el repo → rama `main`. Render detecta `render.yaml`.
4. Te pedirá los valores de las variables marcadas `sync: false` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`):
   - **Modo demo:** déjalas vacías.
   - **Con LLM:** rellénalas según la §3 y cambia `LLM_PROVIDER` a `openai_compatible` (Environment del servicio).
5. **Apply**. El primer build tarda unos minutos. Cuando el health check pase, tendrás una URL tipo `https://normacita.onrender.com` (el subdominio puede variar si el nombre está cogido).
6. Comprueba:
   ```bash
   curl https://TU-URL/health
   curl -s -X POST https://TU-URL/api/ask -H 'Content-Type: application/json' \
        -d '{"pregunta":"¿Qué tensiones nominales se usan en las redes trifásicas?"}'
   ```
7. Copia la URL en el README (tabla de enlaces, «Demo desplegada») y en el documento de entrega.

Notas del plan free de Render:
- La instancia **se duerme tras ~15 min sin tráfico**; la primera petición tarda ~30-60 s en despertar. Ábrela un minuto antes de la corrección o de grabar el vídeo.
- `autoDeploy: true`: cada push a `main` redespliega. Si prefieres desplegar solo con CI verde, desactívalo y usa un *deploy hook* desde GitHub Actions (tarea de la semana 3 del ROADMAP).
- Cambiar variables en el panel provoca un redeploy automático.

## 2. Alternativa: Fly.io
⚠️ Fly.io **ya no tiene plan gratuito** para cuentas nuevas: ofrece una prueba (2 h de máquina o 7 días) y después exige tarjeta. Úsalo solo si Render no te sirve.

```bash
# 👤 instala flyctl y crea la cuenta: https://fly.io/docs/flyctl/install/
fly auth login
fly launch --no-deploy --name normacita-TUNOMBRE --region mad   # detecta el Dockerfile; genera fly.toml
# En fly.toml: internal_port = 8000, y añade un health check:
#   [[http_service.checks]]
#     path = "/health"
#     interval = "30s"
#     timeout = "5s"
fly secrets set LLM_PROVIDER=fake                     # modo demo
# Con LLM (ver §3):
# fly secrets set LLM_PROVIDER=openai_compatible LLM_BASE_URL=... LLM_API_KEY=... LLM_MODEL=...
fly deploy
fly open
```
Para ahorrar: `auto_stop_machines = "stop"` y `min_machines_running = 0` en `fly.toml` (la máquina se para sin tráfico).

## 3. Clave gratuita de un LLM (opcional)
NormaCita habla con cualquier API compatible con OpenAI `/chat/completions` (ADR-0002). Elige **una**:

| Proveedor | 👤 Dónde crear la clave | `LLM_BASE_URL` | `LLM_MODEL` (ejemplo; comprueba el vigente) |
|---|---|---|---|
| Google Gemini | <https://aistudio.google.com/apikey> (cuenta Google) | `https://generativelanguage.googleapis.com/v1beta/openai` | un modelo *flash* del plan gratuito listado en AI Studio (p. ej. `gemini-3.8-flash` según la doc a 10/2026) |
| Groq | <https://console.groq.com/keys> | `https://api.groq.com/openai/v1` | uno de <https://console.groq.com/docs/models> |
| OpenRouter | <https://openrouter.ai/keys> | `https://openrouter.ai/api/v1` | un modelo con sufijo `:free` de <https://openrouter.ai/models?max_price=0> |

Variables a definir (en el panel de Render / `fly secrets` / tu `.env` local; **nunca en el repo**):
```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=<de la tabla>
LLM_API_KEY=<tu clave>
LLM_MODEL=<de la tabla>
LLM_TIMEOUT_SECONDS=30
```
Recomendaciones:
- Prueba primero en local (`cp .env.example .env`, rellena, `uvicorn normacita.main:app`).
- Los planes gratuitos tienen **límites por minuto/día** y algunos usan tus peticiones para mejorar sus modelos: no envíes datos personales (NormaCita solo envía la pregunta y fragmentos del BOE).
- Si se agota la cuota, la API responde 502 con un mensaje genérico; vuelve a `LLM_PROVIDER=fake` para mantener la demo operativa.
- `RATE_LIMIT_PER_MINUTE` (20 por defecto) limita el gasto por IP.

## 4. Variables de entorno (referencia)
| Variable | Por defecto | Para qué |
|---|---|---|
| `LLM_PROVIDER` | `fake` | `fake` (demo, sin claves) u `openai_compatible` |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | vacías | Solo con `openai_compatible` |
| `LLM_TIMEOUT_SECONDS` | `30` | Tiempo máximo de la llamada al LLM |
| `CORPUS_PATH` | `data/corpus/rebt.json` | Corpus REBT completo (arts. 1-29 + ITC-BT-01…52) |
| `RETRIEVAL_TOP_K` | `4` | Fragmentos que se pasan al LLM |
| `RETRIEVAL_MIN_SCORE` | `1.0` | Puntuación BM25 mínima |
| `RETRIEVAL_MIN_COVERAGE` | `0.3` | Fracción mínima de la pregunta cubierta por el mejor fragmento; por debajo, «sin base normativa» (ver docs/EVALUACION.md) |
| `RATE_LIMIT_PER_MINUTE` | `20` | Peticiones por IP y minuto |
| `CORS_ORIGINS` | vacío | Orígenes permitidos (vacío = mismo origen) |
| `PORT` | `8000` | Lo inyecta la plataforma |

## 5. Checklist tras desplegar
- [ ] `/health` responde 200 desde una ventana de incógnito.
- [ ] Una pregunta del REBT devuelve citas con enlace al BOE; una ajena («receta de paella») devuelve «sin base normativa».
- [ ] La URL está en el README y en el documento de entrega.
- [ ] Ninguna clave en el repositorio (`git grep -i api_key` solo muestra nombres de variables).
