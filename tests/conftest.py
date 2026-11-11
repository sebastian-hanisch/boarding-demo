"""Gemeinsame Hilfen: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def mk(passengers):
    """passengers: Liste (Reihe, Seite, Platz, Verstauzeit) in Warteschlangenreihenfolge -> (order, row, side, pos, stow)."""
    row, side, pos, stow = [], [], [], []
    for r, s, p, w in passengers:
        row.append(r)
        side.append(s)
        pos.append(p)
        stow.append(w)
    return list(range(len(passengers))), row, side, pos, stow


@pytest.fixture
def mini():
    """3 Reihen, 3 Fahrgäste: (Reihe 2, Gang, 4 Takte), (Reihe 3, Fenster, 2 Takte), (Reihe 1, Mitte, 3 Takte); e = 2, Platzwechsel 3.

    Handrechnung: Fahrgast 0 betritt bei Takt 1, erreicht Reihe 2 bei Takt 2 und sitzt nach 4 Takten bei Takt 6. Fahrgast 1 betritt bei Takt 3, kommt bis Zelle 1 und
    wartet dort, bis Fahrgast 0 bei Takt 6 die Zelle 2 räumt; er erreicht Reihe 3 bei Takt 7 und sitzt nach 2 Takten bei Takt 9. Fahrgast 2 kann erst bei Takt 6 eintreten
    (die erste Zelle wird erst dann frei), steht dann in Reihe 1 und sitzt nach 3 Takten bei Takt 9. Die Boarding-Zeit ist 9."""
    return mk([(2, 0, 2, 4), (3, 0, 0, 2), (1, 0, 1, 3)])
