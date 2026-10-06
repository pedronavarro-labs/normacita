"""Ingesta de normativa desde la API de datos abiertos del BOE → corpus JSON.

Uso (desde la raíz del proyecto, con el entorno activado):

    python scripts/ingest_boe.py --id BOE-A-2002-18099 --bloques a1,a2,a3,a4 \\
        --norma "REBT (Real Decreto 842/2002), Reglamento electrotécnico para baja tensión" \\
        --salida data/corpus/rebt.json

    # Sin --bloques descarga el índice y procesa todos los preceptos (artículos).

API: https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{ID}/texto/...
Cada bloque se divide en fragmentos por apartado ("1. …", "2. …") para que las
citas apunten a un trozo concreto.

NOTA: escrito y probado de forma unitaria con XML de ejemplo; la API real no era
accesible desde el entorno donde se generó. Pruébalo en tu máquina y ajusta el
parseo si el XML cambia (ver tests/test_ingest.py).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET  # noqa: N817
from pathlib import Path

import httpx

API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{id}/texto"
_APARTADO = re.compile(r"^(\d+)\.\s")
_HEADING = re.compile(r"^Art[íi]culo\s+(\d+\w*)\.?\s*(.*?)\.?$")


def _text(el: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def parse_bloque(xml: str, id_norma: str, norma: str) -> list[dict[str, str]]:
    """Convierte el XML de un bloque (artículo) en fragmentos por apartado."""
    root = ET.fromstring(xml)  # noqa: S314 (fuente oficial, sin DTD externas)
    bloque = root.find(".//bloque")
    if bloque is None:
        return []
    versiones = bloque.findall("version")
    if not versiones:
        return []
    ultima = versiones[-1]  # versión vigente = la última
    bloque_id = bloque.get("id", "")
    articulo, titulo = bloque.get("titulo", bloque_id), ""
    apartados: dict[str, list[str]] = {}
    actual = "único"
    for p in ultima.iter("p"):
        texto = _text(p)
        clase = p.get("class", "")
        if not texto or clase.startswith("nota"):
            continue
        if clase == "articulo":
            m = _HEADING.match(texto)
            if m:
                articulo, titulo = f"Artículo {m.group(1)}", m.group(2)
            continue
        m = _APARTADO.match(texto)
        if m:
            actual = m.group(1)
        apartados.setdefault(actual, []).append(texto)
    url = f"https://www.boe.es/buscar/act.php?id={id_norma}#{bloque_id}"
    return [
        {
            "id": f"{id_norma.lower()}-{bloque_id}-{ap}",
            "norma": norma,
            "articulo": articulo,
            "titulo": titulo,
            "apartado": ap,
            "texto": " ".join(partes),
            "url": url,
        }
        for ap, partes in apartados.items()
    ]


def parse_indice(xml: str) -> list[str]:
    """Devuelve los ids de bloque de tipo precepto (artículos) del índice."""
    root = ET.fromstring(xml)  # noqa: S314
    ids = []
    for b in root.iter("bloque"):
        bid = b.findtext("id") or b.get("id")
        tipo = b.findtext("tipo") or b.get("tipo") or ""
        if bid and tipo == "precepto":
            ids.append(bid)
    return ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--id", required=True, help="Identificador BOE, p. ej. BOE-A-2002-18099")
    ap.add_argument("--norma", required=True, help="Nombre legible de la norma")
    ap.add_argument("--bloques", default="", help="Lista separada por comas (vacío = todos)")
    ap.add_argument("--salida", required=True, type=Path)
    args = ap.parse_args(argv)

    base = API.format(id=args.id)
    with httpx.Client(timeout=30, headers={"Accept": "application/xml"}) as client:
        bloques = [b.strip() for b in args.bloques.split(",") if b.strip()]
        if not bloques:
            bloques = parse_indice(client.get(f"{base}/indice").raise_for_status().text)
        fragmentos = []
        for b in bloques:
            resp = client.get(f"{base}/bloque/{b}").raise_for_status()
            fragmentos += parse_bloque(resp.text, args.id, args.norma)
            time.sleep(0.3)  # ser amables con el servidor público
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    corpus = {
        "_fuente": f"{base} (consultado {time.strftime('%Y-%m-%d')})",
        "fragmentos": fragmentos,
    }
    args.salida.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(fragmentos)} fragmentos → {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
