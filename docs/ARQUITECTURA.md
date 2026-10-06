# Arquitectura — NormaCita

## 1. Visión general (C4 nivel 1-2)

```mermaid
flowchart LR
    U[Usuario<br/>navegador] -->|HTTPS| W[NormaCita<br/>FastAPI + UI estática]
    W -->|lee al arrancar| C[(Corpus JSON<br/>data/corpus)]
    W -->|/chat/completions<br/>opcional| L[Proveedor LLM<br/>Gemini / Groq / OpenRouter / Ollama]
    I[scripts/ingest_boe.py] -->|API datos abiertos| B[BOE]
    I -->|genera| C
```

- **Un único servicio** (monolito modular): fácil de desplegar gratis y suficiente para el MVP.
- El LLM es **opcional**: sin él, el proveedor *fake* responde con extractos literales.

## 2. Capas (arquitectura hexagonal / Clean Architecture)

```mermaid
flowchart TB
    subgraph api["api (entrada HTTP)"]
        A1[app.py · endpoints]
        A2[schemas.py · validación]
        A3[security.py · cabeceras + rate limit]
    end
    subgraph app["application (casos de uso)"]
        P[ports.py · Retriever, LLMProvider]
        UC[ask_question.py · AskQuestion]
    end
    subgraph dom["domain"]
        D[models.py · Fragment, Citation, Answer]
    end
    subgraph infra["infrastructure (adaptadores)"]
        R[bm25_retriever.py]
        CL[corpus_loader.py]
        F[llm/fake_provider.py]
        O[llm/openai_compatible.py]
        FA[llm/factory.py]
    end
    A1 --> UC
    UC --> P
    UC --> D
    R -. implementa .-> P
    F -. implementa .-> P
    O -. implementa .-> P
    A1 --> FA
    A1 --> R
```

**Regla de dependencias:** las flechas siempre apuntan hacia dentro. `domain` no importa nada; `application` solo depende de `domain` y de sus propios puertos; la infraestructura implementa los puertos. Por eso se cambia de LLM o de buscador sin tocar el caso de uso, y los tests usan dobles sin red.

## 3. Flujo de una pregunta (secuencia)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant API as FastAPI /api/ask
    participant UC as AskQuestion
    participant R as Retriever (BM25)
    participant L as LLMProvider
    U->>API: POST {pregunta}
    API->>API: validar (3-500 chars) + rate limit por IP
    API->>UC: execute(pregunta)
    UC->>R: search(pregunta, top_k)
    R-->>UC: fragmentos con puntuación
    alt no supera la puntuación mínima o la cobertura
        Note over UC: no se llama al LLM (coste 0)
        UC-->>API: Answer(sin_base=true)
    else hay base normativa
        UC->>L: generate(pregunta, fragmentos numerados)
        L-->>UC: texto con marcadores [n]
        UC->>UC: validar marcadores, quitar inventados
        UC-->>API: Answer(texto, citas)
    end
    API-->>U: JSON {respuesta, citas[], sin_base, proveedor}
```

## 4. Modelo de datos (corpus)

```mermaid
erDiagram
    FRAGMENTO {
        string id "boe-a-2002-18099-a4-2"
        string norma "REBT (Real Decreto 842/2002)…"
        string articulo "Artículo 4"
        string titulo "Clasificación de las tensiones…"
        string apartado "2"
        string texto "literal del BOE"
        string url "https://www.boe.es/buscar/act.php?id=…#a4"
    }
```
Granularidad = **apartado** de artículo: la cita es precisa y el fragmento cabe holgado en el contexto del LLM.

## 5. Seguridad (resumen; detalle en ADR-0004)
| Amenaza | Control |
|---|---|
| Prompt injection directa (pregunta) o indirecta (texto del corpus) — OWASP LLM01 | Prompt de sistema que trata fragmentos y pregunta como datos delimitados `<<< >>>`; corpus solo de fuente oficial |
| Salida no fiable — LLM05 | La UI inserta todo con `textContent`; enlaces solo `https://`; CSP `default-src 'self'` |
| Citas inventadas / desinformación — LLM09 | Validación de marcadores [n]; umbral «sin base»; aviso de orientativo |
| Consumo ilimitado — LLM10 | Rate limit por IP, `max_tokens`, sin LLM cuando no hay base |
| Fuga de secretos | Claves solo por entorno, `repr=False`, errores genéricos (502) |
| Clickjacking / MIME sniffing | `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff` |

## 6. Despliegue

```mermaid
flowchart LR
    Dev[git push main] --> GH[GitHub Actions<br/>ruff + pytest + docker build + smoke]
    GH -->|verde| PaaS[Render / Fly.io<br/>Dockerfile, plan gratuito]
    PaaS --> URL[https://normacita…]
    Secrets[Variables de entorno<br/>LLM_* en el panel del PaaS] --> PaaS
```
- La imagen corre con usuario no root y lee `PORT` del entorno.
- Limitación conocida: el rate limit es en memoria (1 instancia). Con varias réplicas → Redis.

## 7. Estructura de carpetas
Ver README §d.
