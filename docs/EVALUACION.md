# Evaluación de la recuperación y de las negativas (HU-07)

> Qué se mide, cómo reproducirlo y qué resultados hay. Todo con el proveedor **fake** (determinista, sin red ni claves), así que corre en el CI.

## 1. Qué se mide
La parte crítica de NormaCita es **citar el artículo/apartado correcto** y **no responder** cuando la norma no cubre la pregunta. El LLM solo redacta sobre lo que el recuperador le pasa, así que medimos el recuperador + la decisión «sin base» (`AskQuestion.relevant`), que es exactamente lo que ve el LLM.

| Métrica | Definición |
|---|---|
| `hit@1` | % de preguntas del corpus cuyo **primer** fragmento coincide con una cita esperada (mismo artículo/ITC y mismo apartado base) |
| `hit@3` | Igual, pero en cualquiera de los 3 primeros |
| `cobertura` | % de preguntas del corpus que **sí** se responden (no se rechazan por error) |
| `acierto_negativas` | % de preguntas fuera de ámbito que se **rechazan** («sin base normativa») |

## 2. Conjunto de preguntas (`eval/preguntas.json`)
- **52 preguntas**: 42 con cita esperada + 10 fuera de ámbito (incluye un intento de *prompt injection*).
- Las citas esperadas se escribieron **leyendo el texto real del corpus** (campo `nota` con el dato que lo justifica). Un test (`test_las_citas_esperadas_existen_en_el_corpus`) comprueba que cada cita existe en `data/corpus/rebt.json`.
- Dos subconjuntos para no engañarnos:
  - `ajuste` (30 + 7): las que se usaron para **elegir** los parámetros del recuperador.
  - `validacion` (12 + 3): escritas **antes** de medir y no usadas para ajustar. Es la cifra honesta de generalización.

## 3. Cómo ejecutarlo
```bash
python -m normacita.evaluation                      # JSON con total / ajuste / validacion
python -m normacita.evaluation --markdown docs/evaluacion/resultados-v0.2-bm25-mejorado.md
pytest tests/test_evaluation.py                     # el CI falla si alguna métrica baja del umbral
```
Umbrales actuales del CI (sobre el total, un poco por debajo del resultado real para detectar regresiones): `hit@1 ≥ 0.70`, `hit@3 ≥ 0.90`, `cobertura ≥ 0.95`, `acierto_negativas ≥ 0.90`. Si mejoras la recuperación, **súbelos** (trinquete).

## 4. Resultados: antes / después
Mismo corpus (REBT completo, 832 fragmentos) y mismas 52 preguntas.

| Métrica | Antes · BM25 básico (v0.1) | Después · BM25 mejorado (v0.2) |
|---|---|---|
| **Total** hit@1 | 0.548 | **0.714** |
| **Total** hit@3 | 0.738 | **0.952** |
| **Total** cobertura | 1.000 | 1.000 |
| **Total** acierto negativas | 0.300 | **1.000** |
| Ajuste hit@1 / hit@3 | 0.633 / 0.767 | 0.800 / 0.967 |
| Ajuste negativas | 0.286 | 1.000 |
| **Validación** hit@1 / hit@3 | 0.333 / 0.667 | **0.500 / 0.917** |
| **Validación** negativas | 0.333 | 1.000 |

Detalle por pregunta: [antes](evaluacion/resultados-v0.1-bm25-basico-corpus-v0.2.md) · [después](evaluacion/resultados-v0.2-bm25-mejorado.md). (El fichero `resultados-v0.1-bm25-basico.md` es la primera medición, con 37 preguntas y el corpus anterior: hit@1 0.667, hit@3 0.767, negativas 0.286.)

**El caso que motivó el cambio** — «¿A qué instalaciones se aplica?»:
- Antes: ningún fragmento del art. 2 en el top-3 (ITC-BT-23, ITC-BT-01 «Amovible», ITC-BT-35); en la versión con la muestra, el art. 2.4 (**exclusiones**) salía antes que el 2.1.
- Después: art. 2.3 → **2.1** → 2.2; el 2.4 cae al puesto 38. Y la pregunta inversa («¿Qué instalaciones quedan excluidas…?») devuelve el **2.4 primero**. Ambos casos tienen test de regresión (`tests/test_retriever.py`).

## 5. Qué se cambió en el recuperador (sin dependencias nuevas)
1. **Stemming ligero en español** (`infrastructure/text.py`): plurales, género, `-ación`, participios y verbos en `-uir` (`instalaciones/instalado → instal`, `excluyen/excluidas → exclu`).
2. **Stopwords** ampliadas con palabras interrogativas («qué», «cuál», «debe»…).
3. **Campo título** con BM25 propio (artículo + título; en ITC, «Terminología · Aislamiento reforzado»), sumado al del texto.
4. **Cláusulas de exclusión**: los apartados que empiezan por «Se excluyen / No se aplicará…» se penalizan (×0,5) salvo que la pregunta sea negativa («excluidas», «no», «salvo»…), en cuyo caso se favorecen (×1,3).
5. **Prior suave para el articulado** (×1,2): ante empate, el Real Decreto antes que una ITC.
6. **Cobertura** (`RETRIEVAL_MIN_COVERAGE=0.3`): fracción del peso IDF de la pregunta presente en el mejor fragmento. Las palabras que no existen en el corpus («paella», «Australia») cuentan con IDF máximo, así que una pregunta ajena no se responde aunque comparta «instalación».

## 6. Lectura honesta
- **Sobreajuste**: en `ajuste` el salto es grande; en `validacion` el hit@1 es 0.50 (6/12). La mejora real está sobre todo en **hit@3** (0.667 → 0.917) y en las **negativas**. Con un prior más fuerte (×1,5) el ajuste no empeoraba pero la validación bajaba a 0.333, por eso se eligió ×1,2. Nota: esa elección sí miró la validación, así que tampoco es una cifra 100 % «ciega»; la próxima ampliación del conjunto debe hacerse con preguntas nuevas.
- **Conjunto pequeño**: 12 preguntas de validación → cada pregunta son 8 puntos. Ampliar a ≥ 30 con preguntas de usuarios reales (o de foros de instaladores) es la siguiente tarea.
- **Fallos típicos** que quedan: paráfrasis sin palabras compartidas («quién puede hacer instalaciones» → empresas instaladoras, art. 22) y preguntas que encajan igual de bien en el articulado y en una ITC. Es el argumento para probar búsqueda **híbrida** (ADR-0003).
- **Negativas fáciles**: las 10 preguntas fuera de ámbito son claramente ajenas (cocina, fútbol, tiempo…). Falta probar negativas *cercanas* (alta tensión, instalaciones de gas, normativa autonómica), donde el umbral de cobertura será más exigido.
- Las métricas son del recuperador; la calidad de la redacción con un LLM real (fidelidad a las citas) se evaluará aparte cuando haya clave (HU-06).
