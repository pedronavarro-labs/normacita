from normacita.application.ask_question import NO_BASIS_MESSAGE, AskQuestion
from normacita.domain.models import Fragment, ScoredFragment


def _frag(i: int) -> Fragment:
    return Fragment(f"f{i}", "Norma X", f"Artículo {i}", "Título", "1", f"Texto {i}.", "https://x")


class StubRetriever:
    def __init__(self, hits):
        self.hits = hits

    def search(self, query, top_k):
        return self.hits[:top_k]


class StubLLM:
    name = "stub"

    def __init__(self, reply: str):
        self.reply = reply
        self.calls = 0

    def generate(self, question, fragments):
        self.calls += 1
        return self.reply


def test_sin_resultados_no_llama_al_llm():
    llm = StubLLM("no debería usarse")
    answer = AskQuestion(StubRetriever([]), llm).execute("hola")
    assert answer.sin_base and answer.texto == NO_BASIS_MESSAGE
    assert llm.calls == 0


def test_resultados_bajo_umbral_cuentan_como_sin_base():
    llm = StubLLM("x")
    hits = [ScoredFragment(_frag(1), 0.2)]
    answer = AskQuestion(StubRetriever(hits), llm, min_score=1.0).execute("hola")
    assert answer.sin_base and llm.calls == 0


def test_conserva_solo_citas_usadas_y_numeradas():
    hits = [ScoredFragment(_frag(i), 5.0) for i in (1, 2, 3)]
    answer = AskQuestion(StubRetriever(hits), StubLLM("A [3] y B [1].")).execute("pregunta")
    assert [c.numero for c in answer.citas] == [1, 3]
    assert answer.citas[1].fragment.id == "f3"


def test_elimina_citas_inventadas():
    hits = [ScoredFragment(_frag(1), 5.0)]
    answer = AskQuestion(StubRetriever(hits), StubLLM("Dato [1] y otro [7].")).execute("p")
    assert "[7]" not in answer.texto
    assert [c.numero for c in answer.citas] == [1]


def test_sin_marcadores_devuelve_todo_el_contexto():
    hits = [ScoredFragment(_frag(i), 5.0) for i in (1, 2)]
    answer = AskQuestion(StubRetriever(hits), StubLLM("Respuesta sin citas.")).execute("p")
    assert [c.numero for c in answer.citas] == [1, 2]


def test_cobertura_insuficiente_cuenta_como_sin_base():
    """Si el mejor fragmento solo casa con una parte menor de la pregunta, no se responde."""
    llm = StubLLM("x")
    hits = [ScoredFragment(_frag(1), 5.0, coverage=0.1)]
    answer = AskQuestion(StubRetriever(hits), llm, min_coverage=0.3).execute("hola")
    assert answer.sin_base and llm.calls == 0


def test_cobertura_suficiente_si_responde():
    llm = StubLLM("Respuesta [1].")
    hits = [ScoredFragment(_frag(1), 5.0, coverage=0.8)]
    answer = AskQuestion(StubRetriever(hits), llm, min_coverage=0.3).execute("hola")
    assert not answer.sin_base and llm.calls == 1
