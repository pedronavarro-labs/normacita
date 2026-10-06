"""Fixtures compartidas. Ningún test usa red ni claves de API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from normacita.api.app import create_app
from normacita.config import PROJECT_ROOT, Settings
from normacita.infrastructure.bm25_retriever import BM25Retriever
from normacita.infrastructure.corpus_loader import load_corpus

CORPUS = PROJECT_ROOT / "data" / "corpus" / "rebt.json"


@pytest.fixture(scope="session")
def fragments():
    return load_corpus(CORPUS)


@pytest.fixture(scope="session")
def retriever(fragments):
    return BM25Retriever(fragments)


@pytest.fixture
def settings():
    return Settings(llm_provider="fake", corpus_path=CORPUS, rate_limit_per_minute=100)


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))
