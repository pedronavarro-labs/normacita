"""Evaluación automática de la calidad de recuperación y de las negativas.

Mide, sobre ``eval/preguntas.json``:

- **hit@1**: la primera cita es una de las esperadas.
- **hit@3**: alguna de las 3 primeras citas es una de las esperadas.
- **cobertura**: preguntas del corpus que NO se rechazan por falta de base.
- **acierto de negativas**: preguntas ajenas al REBT que se rechazan (``sin_base``).

Usa el proveedor *fake* (determinista, sin red ni claves), así que el resultado es
reproducible y puede ejecutarse en CI. Uso::

    python -m normacita.evaluation                 # tabla por consola
    python -m normacita.evaluation --markdown docs/EVALUACION-resultados.md
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from normacita.application.ask_question import AskQuestion
from normacita.application.ports import Retriever
from normacita.config import PROJECT_ROOT, Settings
from normacita.domain.models import Fragment
from normacita.infrastructure.bm25_retriever import BM25Retriever
from normacita.infrastructure.corpus_loader import load_corpus
from normacita.infrastructure.llm.fake_provider import FakeLLMProvider

EVAL_PATH = PROJECT_ROOT / "eval" / "preguntas.json"


def apartado_base(apartado: str) -> str:
    """'3 (parte 2/5)' → '3' (los trozos de una misma sección cuentan como la sección)."""
    return apartado.split(" (parte")[0]


def coincide(fragment: Fragment, esperado: list[list[str]]) -> bool:
    return any(
        fragment.articulo == art and apartado_base(fragment.apartado) == ap for art, ap in esperado
    )


@dataclass
class Fila:
    id: str
    pregunta: str
    tipo: str  # "corpus" | "fuera"
    conjunto: str  # "ajuste" | "validacion"
    top: list[str]  # referencias recuperadas (por encima del umbral)
    hit1: bool = False
    hit3: bool = False
    rechazada: bool = False

    @property
    def correcta(self) -> bool:
        return self.rechazada if self.tipo == "fuera" else self.hit3


@dataclass
class Informe:
    filas: list[Fila] = field(default_factory=list)

    def _ratio(self, filas: list[Fila], attr: str) -> float:
        return round(sum(getattr(f, attr) for f in filas) / len(filas), 3) if filas else 0.0

    @property
    def metricas(self) -> dict[str, float | int]:
        return self.metricas_de()

    def metricas_de(self, conjunto: str | None = None) -> dict[str, float | int]:
        """Métricas de todo el conjunto o solo de 'ajuste' / 'validacion'."""
        filas = [f for f in self.filas if conjunto in (None, f.conjunto)]
        corpus = [f for f in filas if f.tipo == "corpus"]
        fuera = [f for f in filas if f.tipo == "fuera"]
        return {
            "preguntas_corpus": len(corpus),
            "preguntas_fuera": len(fuera),
            "hit@1": self._ratio(corpus, "hit1"),
            "hit@3": self._ratio(corpus, "hit3"),
            "cobertura": round(1 - self._ratio(corpus, "rechazada"), 3),
            "acierto_negativas": self._ratio(fuera, "rechazada"),
        }

    def markdown(self) -> str:
        total, aj, va = self.metricas, self.metricas_de("ajuste"), self.metricas_de("validacion")
        lineas = [
            "| Métrica | Total | Ajuste | Validación |",
            "|---|---|---|---|",
            *(f"| {k} | {total[k]} | {aj[k]} | {va[k]} |" for k in total),
            "",
            "| Id | Conjunto | Pregunta | Resultado | Top recuperado |",
            "|---|---|---|---|---|",
        ]
        for f in self.filas:
            estado = (
                ("✅ rechazada" if f.rechazada else "❌ respondida")
                if f.tipo == "fuera"
                else ("✅ @1" if f.hit1 else "🟡 @3" if f.hit3 else "❌")
            )
            top = "; ".join(f.top[:3]) or "—"
            lineas.append(f"| {f.id} | {f.conjunto} | {f.pregunta} | {estado} | {top} |")
        return "\n".join(lineas)


def cargar_preguntas(path: Path = EVAL_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["preguntas"]


def evaluar(
    retriever: Retriever,
    preguntas: list[dict],
    top_k: int = 4,
    min_score: float = 1.0,
    min_coverage: float = 0.3,
) -> Informe:
    ask = AskQuestion(retriever, FakeLLMProvider(), top_k, min_score, min_coverage)
    informe = Informe()
    for q in preguntas:
        frags = [h.fragment for h in ask.relevant(q["pregunta"])]
        answer = ask.execute(q["pregunta"])
        fila = Fila(
            id=q["id"],
            pregunta=q["pregunta"],
            tipo="fuera" if q["esperado"] == "fuera" else "corpus",
            conjunto=q.get("conjunto", "ajuste"),
            top=[f"{f.articulo} {apartado_base(f.apartado)}" for f in frags],
            rechazada=answer.sin_base,
        )
        if fila.tipo == "corpus":
            fila.hit1 = bool(frags) and coincide(frags[0], q["esperado"])
            fila.hit3 = any(coincide(f, q["esperado"]) for f in frags[:3])
        informe.filas.append(fila)
    return informe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evalúa NormaCita con eval/preguntas.json")
    ap.add_argument("--markdown", type=Path, help="Guardar la tabla de resultados en Markdown")
    args = ap.parse_args(argv)
    settings = Settings.from_env()
    retriever = BM25Retriever(load_corpus(settings.corpus_path))
    informe = evaluar(
        retriever,
        cargar_preguntas(),
        settings.retrieval_top_k,
        settings.retrieval_min_score,
        settings.retrieval_min_coverage,
    )
    resumen = {c: informe.metricas_de(c) for c in (None, "ajuste", "validacion")}
    print(json.dumps({k or "total": v for k, v in resumen.items()}, ensure_ascii=False, indent=2))
    if args.markdown:
        args.markdown.write_text(informe.markdown() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
