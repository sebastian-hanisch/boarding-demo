"""Vorgerechnete Messreihe (`data/brd_results.json`, erzeugt von `tools/make_results.py`): Experiment „Voraussicht“."""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "brd_results.json"


def load_results() -> dict | None:
    """Die vorgerechnete Messreihe oder None, wenn die Datei fehlt oder nicht lesbar ist (die App zeigt dann einen Hinweis, keinen Fehler)."""
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def lookahead_rows(results: dict | None) -> list[dict]:
    """Zeilen des Experiments Voraussicht (je Gruppenanteil: beste gefundene Reihenfolge, Steffen-artig, Zufall, Eintrittsschranke); leer ohne Messreihe."""
    if not results:
        return []
    return list(results.get("lookahead", []))
