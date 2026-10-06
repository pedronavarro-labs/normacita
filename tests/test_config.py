from normacita.config import PROJECT_ROOT, Settings


def test_from_env_lee_variables(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", " OpenAI_Compatible ")
    monkeypatch.setenv("LLM_MODEL", "m")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "2")
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0.5")
    monkeypatch.setenv("CORS_ORIGINS", "https://a.es, https://b.es")
    monkeypatch.setenv("CORPUS_PATH", "data/corpus/rebt.json")
    s = Settings.from_env()
    assert s.llm_provider == "openai_compatible"
    assert s.retrieval_top_k == 2 and s.retrieval_min_score == 0.5
    assert s.cors_origins == ("https://a.es", "https://b.es")
    assert s.corpus_path == PROJECT_ROOT / "data/corpus/rebt.json"


def test_from_env_valores_por_defecto(monkeypatch):
    for var in ("LLM_PROVIDER", "CORPUS_PATH", "CORS_ORIGINS"):
        monkeypatch.delenv(var, raising=False)
    s = Settings.from_env()
    assert s.llm_provider == "fake" and s.cors_origins == ()
