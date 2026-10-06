"""Ingesta de normativa desde la API de datos abiertos del BOE → corpus JSON.

Dos pasos (se pueden ejecutar juntos o por separado):

1. ``descargar``: guarda el XML original de cada bloque (índice + artículos + ITC)
   en una carpeta. Así el texto queda tal cual lo publica el BOE y se puede
   auditar o reprocesar sin volver a llamar a la API.
2. ``construir``: convierte esos XML en el corpus JSON (un fragmento por apartado).

Uso (desde la raíz del proyecto, con el entorno activado)::

    # Todo de una vez (artículos del RD + ITC-BT):
    python scripts/ingest_boe.py todo --id BOE-A-2002-18099 --raw data/raw/rebt \\
        --norma "REBT (Real Decreto 842/2002), Reglamento electrotécnico para baja tensión" \\
        --salida data/corpus/rebt.json

    # Solo artículos (sin ITC):  añadir  --sin-itc
    # Reprocesar sin red:        python scripts/ingest_boe.py construir --raw data/raw/rebt ...

API: https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{ID}/texto/...
Si tu red no llega a boe.es, el workflow manual ``.github/workflows/ingest-boe.yml``
ejecuta este mismo script en GitHub Actions y publica el resultado como artefacto.
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
USER_AGENT = "NormaCita/0.1 (TFM educativo; https://github.com/pedronavarro-labs/normacita)"

_ARTICULO_ID = re.compile(r"^a\d+(-\d+)?$")  # a1 … a9, a1-2 … a2-11 (artículos 1-29)
_ITC_ID = re.compile(r"^ib(-\d+)?$")  # ib, ib-2 … ib-52 (ITC-BT-01 … 52)
_APARTADO = re.compile(r"^(\d+)\.\s")  # "1. Texto…" (artículos)
_SECCION_ITC = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")  # "2.1 Texto…" o "3. TÍTULO"
_HEADING = re.compile(r"^Art[íi]culo\s+(\d+\w*)\.?\s*(.*?)\.?$")
_MAX_CHARS = 2500  # trocea secciones muy largas para que el fragmento sea citable


def _text(el: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _ultima_version(xml: str) -> tuple[ET.Element | None, ET.Element | None]:
    root = ET.fromstring(xml)  # noqa: S314 (fuente oficial, sin DTD externas)
    bloque = root.find(".//bloque")
    if bloque is None:
        return None, None
    versiones = bloque.findall("version")
    return bloque, (versiones[-1] if versiones else None)  # vigente = la última


def _trocear(texto: str) -> list[str]:
    """Divide un texto largo por frases en trozos de <= _MAX_CHARS."""
    if len(texto) <= _MAX_CHARS:
        return [texto]
    trozos, actual = [], ""
    for frase in re.split(r"(?<=[.;:])\s+", texto):
        if actual and len(actual) + len(frase) + 1 > _MAX_CHARS:
            trozos.append(actual)
            actual = frase
        else:
            actual = f"{actual} {frase}".strip()
    if actual:
        trozos.append(actual)
    return trozos


def parse_articulo(xml: str, id_norma: str, norma: str) -> list[dict[str, str]]:
    """Bloque de artículo → un fragmento por apartado ("1.", "2."…)."""
    bloque, ultima = _ultima_version(xml)
    if bloque is None or ultima is None:
        return []
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


def parse_itc(xml: str, id_norma: str, norma: str) -> list[dict[str, str]]:
    """Bloque de ITC-BT → un fragmento por sección numerada de primer nivel.

    Las ITC se estructuran como "1. OBJETO", "2. CAMPO DE APLICACIÓN", "2.1 …".
    Agrupamos por la sección principal (1, 2, 3…) y troceamos si es muy larga.
    """
    bloque, ultima = _ultima_version(xml)
    if bloque is None or ultima is None:
        return []
    bloque_id = bloque.get("id", "")
    itc = bloque.get("titulo", bloque_id)  # "ITC-BT-19"
    titulo_itc = ""
    secciones: dict[str, list[str]] = {}
    titulos: dict[str, str] = {}
    actual = "0"
    for p in ultima.iter("p"):
        texto = _text(p)
        clase = p.get("class", "")
        if not texto or clase.startswith("nota") or clase == "cita_con_pleca":
            continue
        if not titulo_itc and clase.startswith("centro_negrita") and not texto.startswith("ITC"):
            titulo_itc = texto.title() if texto.isupper() else texto
            continue
        m = _SECCION_ITC.match(texto)
        if m and ("." not in m.group(1)) and len(texto) < 160:
            actual = m.group(1)
            titulos.setdefault(actual, texto)
        secciones.setdefault(actual, []).append(texto)
    url = f"https://www.boe.es/buscar/act.php?id={id_norma}#{bloque_id}"
    fragmentos = []
    for sec, partes in secciones.items():
        for i, trozo in enumerate(_trocear(" ".join(partes)), start=1):
            ap = sec if i == 1 else f"{sec} (parte {i})"
            fragmentos.append(
                {
                    "id": f"{id_norma.lower()}-{bloque_id}-{sec}-{i}",
                    "norma": norma,
                    "articulo": itc,
                    "titulo": titulos.get(sec, titulo_itc) or titulo_itc,
                    "apartado": ap if sec != "0" else "preliminar",
                    "texto": trozo,
                    "url": url,
                }
            )
    return fragmentos


def parse_indice(xml: str, incluir_itc: bool = True) -> list[str]:
    """Ids de bloque a procesar: artículos (a*) y, opcionalmente, ITC (ib*).

    El índice del BOE no indica el tipo de bloque, así que filtramos por el id.
    """
    root = ET.fromstring(xml)  # noqa: S314
    ids = []
    for b in root.iter("bloque"):
        bid = b.findtext("id") or b.get("id") or ""
        if _ARTICULO_ID.match(bid) or (incluir_itc and _ITC_ID.match(bid)):
            ids.append(bid)
    return ids


def descargar(id_norma: str, raw: Path, incluir_itc: bool) -> list[str]:
    raw.mkdir(parents=True, exist_ok=True)
    base = API.format(id=id_norma)
    headers = {"Accept": "application/xml", "User-Agent": USER_AGENT}
    with httpx.Client(timeout=60, headers=headers, follow_redirects=True) as client:
        indice = client.get(f"{base}/indice").raise_for_status().text
        (raw / "indice.xml").write_text(indice, encoding="utf-8")
        bloques = parse_indice(indice, incluir_itc)
        for b in bloques:
            destino = raw / f"{b}.xml"
            if not destino.exists():
                destino.write_text(
                    client.get(f"{base}/bloque/{b}").raise_for_status().text, encoding="utf-8"
                )
                time.sleep(0.3)  # ser amables con el servidor público
    print(f"{len(bloques)} bloques descargados en {raw}")
    return bloques


def construir(id_norma: str, norma: str, raw: Path, salida: Path, incluir_itc: bool) -> int:
    bloques = parse_indice((raw / "indice.xml").read_text(encoding="utf-8"), incluir_itc)
    fragmentos: list[dict[str, str]] = []
    for b in bloques:
        xml = (raw / f"{b}.xml").read_text(encoding="utf-8")
        parser = parse_itc if _ITC_ID.match(b) else parse_articulo
        fragmentos += parser(xml, id_norma, norma)
    salida.parent.mkdir(parents=True, exist_ok=True)
    corpus = {
        "_fuente": f"{API.format(id=id_norma)} (consolidado; generado {time.strftime('%Y-%m-%d')})",
        "_aviso": "Texto oficial del BOE. Orientativo: consulte la versión vigente en boe.es.",
        "fragmentos": fragmentos,
    }
    salida.write_text(json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(fragmentos)} fragmentos de {len(bloques)} bloques → {salida}")
    return len(fragmentos)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("modo", choices=["descargar", "construir", "todo"])
    ap.add_argument("--id", default="BOE-A-2002-18099", help="Identificador BOE")
    ap.add_argument(
        "--norma",
        default="REBT (Real Decreto 842/2002), Reglamento electrotécnico para baja tensión",
    )
    ap.add_argument("--raw", type=Path, default=Path("data/raw/rebt"), help="Carpeta de XML")
    ap.add_argument("--salida", type=Path, default=Path("data/corpus/rebt.json"))
    ap.add_argument("--sin-itc", action="store_true", help="Solo los artículos del reglamento")
    args = ap.parse_args(argv)
    incluir_itc = not args.sin_itc
    if args.modo in ("descargar", "todo"):
        descargar(args.id, args.raw, incluir_itc)
    if args.modo in ("construir", "todo"):
        construir(args.id, args.norma, args.raw, args.salida, incluir_itc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
