# ADR-0003 · Recuperación léxica BM25 primero; vectorial/híbrida después

- **Estado:** aceptada · **Fecha:** 2026-10-06 · **Revisada:** 2026-10-06 (v0.2, mejoras de BM25 medidas con la evaluación)

## Contexto
El riesgo técnico principal es recuperar el artículo correcto. Los embeddings añaden coste, dependencia de un proveedor y una base vectorial. El vocabulario normativo es muy específico («tensión nominal», «ITC-BT-28»), lo que favorece la búsqueda léxica.

## Decisión
- Implementar `BM25Retriever` en Python puro (sin dependencias), con normalización de tildes y palabras vacías en español, indexando título + texto de cada apartado.
- Umbral `RETRIEVAL_MIN_SCORE`: por debajo se considera «sin base» y no se llama al LLM.
- Medir con un conjunto de evaluación (HU-07) antes de decidir pasar a búsqueda **híbrida** (BM25 + embeddings en pgvector, fusión RRF).

## Consecuencias
- ✅ Determinista, gratis y testeable.
- ⚠️ No entiende sinónimos ni paráfrasis («enchufe» vs «toma de corriente»). Mitigación futura: búsqueda híbrida o expansión de consulta con el LLM.
- ⚠️ Índice en memoria: válido para miles de fragmentos, no para millones.

## Revisión v0.2 · Mejoras medidas (sin dependencias nuevas)
Con el corpus completo (832 fragmentos) el BM25 básico fallaba casos evidentes («¿A qué instalaciones se aplica?» devolvía exclusiones o ITC ajenas) y respondía preguntas fuera de ámbito (negativas 0.30). Se añadió, siempre en Python puro:
- stemming ligero en español y stopwords interrogativas;
- BM25 por campos (texto + título, con el título de la ITC como contexto);
- penalización ×0,5 de cláusulas de exclusión salvo en preguntas negativas (×1,3);
- prior ×1,2 para el articulado del Real Decreto;
- **umbral de cobertura** (`RETRIEVAL_MIN_COVERAGE=0.3`) además de `RETRIEVAL_MIN_SCORE`, para rechazar preguntas cuyo vocabulario apenas aparece en el corpus.

Resultado (52 preguntas, ver [EVALUACION.md](../EVALUACION.md)): hit@1 0.548 → 0.714, hit@3 0.738 → 0.952, negativas 0.30 → 1.00; en el subconjunto de validación hit@1 0.333 → 0.500 y hit@3 0.667 → 0.917.

Se mantiene la decisión: la búsqueda híbrida queda como siguiente paso si los fallos por paráfrasis (p. ej. «quién puede hacer instalaciones» → empresas instaladoras) siguen siendo relevantes al ampliar la evaluación.
