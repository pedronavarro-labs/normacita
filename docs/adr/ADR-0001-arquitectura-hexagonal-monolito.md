# ADR-0001 · Monolito modular con arquitectura hexagonal en Python/FastAPI

- **Estado:** aceptada · **Fecha:** 2026-10-06

## Contexto
TFM individual en ~4 semanas. Debe demostrar arquitectura clara, tests y despliegue gratuito. El ecosistema de IA/RAG (LangChain, embeddings, evaluación) es más maduro en Python.

## Decisión
- Un único servicio **FastAPI** que sirve la API y una UI estática (HTML+JS sin framework).
- Capas `domain` → `application` (puertos + casos de uso) → `infrastructure` (adaptadores) → `api`.
- Inyección de dependencias manual en `create_app()` (*composition root*).

## Alternativas consideradas
- **Next.js full-stack (TS):** buena UI, pero duplicaría el ecosistema (Python para RAG + TS para web).
- **Microservicios (API + worker de ingesta):** innecesario para el MVP; más coste y complejidad de despliegue.
- **LangChain desde el primer día:** se pospone; los puertos permiten introducirlo en un adaptador sin reescribir el caso de uso.

## Consecuencias
- ✅ Tests rápidos y deterministas del núcleo con dobles.
- ✅ Despliegue en un solo contenedor.
- ⚠️ La UI es básica; si se necesita más interacción, se puede añadir un frontend separado más adelante.
