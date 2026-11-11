"""Läufe: Einstellungen, Instanzen je Zufalls-Seed, Boarding-Zeit je Regel und gepaarte Vergleiche.

Alle Regeln werden auf denselben Instanzen gerechnet (gemeinsame Zufallszahlen). Verhältnisse sind Verhältnisse der Mittelwerte über die Läufe; der Standardfehler
kommt aus der gepaarten Differenz T_Regel - Verhältnis * T_Zufall (Delta-Methode)."""

import math
from dataclasses import dataclass

import brd_algorithm as A
import brd_constants as C
from brd_scenario import Instance, make_order


@dataclass(frozen=True)
class Settings:
    rows: int = C.DEFAULT_R
    doors: int = C.DEFAULT_DOORS
    e: int = C.DEFAULT_E
    ell: int = C.DEFAULT_ELL        # Prozent
    smax: int = C.DEFAULT_SMAX
    sh: int = C.DEFAULT_SH
    g: int = C.DEFAULT_G            # Prozent
    gtype: str = "seite"
    gmode: str = "min"
    intra: str = "window_first"
    delta: int = C.DEFAULT_DELTA    # Prozent
    view: str = C.DEFAULT_VIEW_RULE
    seed: int = C.DEFAULT_SEED


def run_seeds(settings: Settings, n_runs: int = C.N_RUNS) -> list[int]:
    """Zufalls-Seeds der Läufe eines Szenarios: ein neuer Seed des Reglers liefert eine neue Läufe-Menge."""
    return [settings.seed * C.SEED_STRIDE + i for i in range(n_runs)]


def build_instances(settings: Settings, seed: int) -> list[Instance]:
    """Eine Instanz je Tür; bei zwei Türen zwei unabhängige Hälften zu je rows // 2 Reihen."""
    kw = dict(g=settings.g / 100.0, ell=settings.ell / 100.0, smin=C.SMIN, smax=max(settings.smax, C.SMIN), delta=settings.delta / 100.0, gtype=settings.gtype)
    if settings.doors == 1:
        return [Instance(seed, R=settings.rows, **kw)]
    half = settings.rows // 2
    return [Instance(seed, R=half, sub=k, **kw) for k in range(2)]


def simulate(insts: list[Instance], rule: str, settings: Settings) -> tuple[int, list[int], int]:
    """(Boarding-Zeit T in Takten, Wartezeit im Gang je Fahrgast, Eintrittsschranke) einer Regel; bei zwei Türen das Maximum der Hälften."""
    total = 0
    waits: list[int] = []
    entry = 0
    for inst in insts:
        order = make_order(inst, rule, intra=settings.intra, gmode=settings.gmode)
        t, w = A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, inst.R, e=settings.e, sh=settings.sh)
        total = max(total, t)
        waits.extend(w)
        entry = max(entry, 1 + (len(order) - 1) * settings.e)
    return total, waits, entry


def run_rules(settings: Settings, rules=C.MAIN_RULES, n_runs: int = C.N_RUNS, seeds=None) -> dict:
    """Alle Regeln auf denselben Instanzen. Rückgabe: {"T": {Regel: [T je Lauf]}, "wait": {Regel: [mittlere Wartezeit je Lauf]}, "entry": [Schranke je Lauf],
    "grouped": [Anteil in Gruppen je Lauf], "seeds": [...]}."""
    seeds = list(seeds) if seeds is not None else run_seeds(settings, n_runs)
    times = {r: [] for r in rules}
    waits = {r: [] for r in rules}
    entry: list[int] = []
    grouped: list[float] = []
    for seed in seeds:
        insts = build_instances(settings, seed)
        grouped.append(sum(i.grouped_share * i.N for i in insts) / sum(i.N for i in insts))
        bound = 0
        for r in rules:
            t, w, b = simulate(insts, r, settings)
            times[r].append(t)
            waits[r].append(sum(w) / len(w))
            bound = max(bound, b)
        entry.append(bound)
    return {"T": times, "wait": waits, "entry": entry, "grouped": grouped, "seeds": seeds}


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def paired_ratio(times, base) -> tuple[float, float]:
    """(Verhältnis der Mittelwerte times/base, Standardfehler) über gepaarte Läufe."""
    n = len(times)
    ratio = sum(times) / sum(base)
    mb = sum(base) / n
    if n < 2:
        return ratio, 0.0
    d = [t - ratio * b for t, b in zip(times, base)]
    md = sum(d) / n
    var = sum((x - md) ** 2 for x in d) / (n - 1)
    return ratio, math.sqrt(var / n) / mb


def wins(times, base) -> int:
    """Zahl der Läufe, in denen die Regel strikt schneller ist als die Basis."""
    return sum(1 for t, b in zip(times, base) if t < b)
