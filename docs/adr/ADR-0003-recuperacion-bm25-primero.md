# ADR-0003 · Recuperación léxica BM25 primero; vectorial/híbrida después

- **Estado:** aceptada · **Fecha:** 2026-10-06

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
