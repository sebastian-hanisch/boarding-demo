"""Exakter Referenzweg für ein Mini-Flugzeug: alle Reihenfolgen aufzählen (Fenster und Gang einer Seite, 4 Reihen, 8 Fahrgäste, 8! = 40320 Reihenfolgen).

Die beste Reihenfolge kennt die Verstauzeiten der Fahrgäste; sie ist die beste Reihenfolge dieser Instanz, keine Regel. Gerechnet wird mit der Zeit-Gitter-Rekursion."""

from itertools import permutations

import brd_algorithm as A
from brd_scenario import SplitMix64

MINI_ROWS = 4


def mini_instance(seed: int, ell: float, smax: int, smin: int = 3):
    """Acht Fahrgäste: je Reihe der Fensterplatz (pos 0) und der Gangplatz (pos 2) einer Seite. Rückgabe: (row, side, pos, stow) je Fahrgast 0 bis 7."""
    rng = SplitMix64(seed * 7919 + 4242)
    row, side, pos, stow = [], [], [], []
    for r in range(1, MINI_ROWS + 1):
        for p in (0, 2):
            row.append(r)
            side.append(0)
            pos.append(p)
            u_bag, u_stow = rng.random(), rng.random()     # immer zwei Zahlen je Fahrgast: ein anderer Gepäckanteil ändert die übrigen Verstauzeiten nicht
            stow.append(smin + int(u_stow * (smax - smin + 1)) if u_bag < ell else 0)
    return row, side, pos, stow


def steffen_like_order(row, pos):
    """Steffen-artig im Mini-Flugzeug: Fenster vor Gang, innerhalb einer Klasse gerade Reihen von hinten nach vorn, dann ungerade."""
    return sorted(range(len(row)), key=lambda i: (pos[i], 0 if row[i] % 2 == 0 else 1, -row[i]))


def enumerate_all(row, side, pos, stow, e: int, sh: int) -> dict:
    """Alle Reihenfolgen durchrechnen: beste Zeit, Mittel über alle, Zeit der Steffen-artigen Reihenfolge, Anteil der Reihenfolgen, die sie schlägt."""
    n = len(row)
    times = []
    for order in permutations(range(n)):
        times.append(A.recursion(list(order), row, side, pos, stow, MINI_ROWS, e=e, sh=sh)[0])
    steffen_t = A.recursion(steffen_like_order(row, pos), row, side, pos, stow, MINI_ROWS, e=e, sh=sh)[0]
    best = min(times)
    return {
        "count": len(times), "best": best, "worst": max(times), "mean": sum(times) / len(times), "steffen": steffen_t,
        "share_beaten": sum(1 for t in times if t > steffen_t) / len(times), "share_optimal": sum(1 for t in times if t == best) / len(times),
    }
