"""Rechnet die vorgerechnete Messreihe `data/brd_results.json` (Experiment „Voraussicht“, zu teuer für die Live-App).

Eine Reihenfolge, die die Verstauzeiten kennt, wird per Simulated Annealing über die Reihenfolge der Gruppen gesucht (30000 Auswertungen je Lauf, Start einmal
von der Steffen-artigen und einmal von einer Zufalls-Reihenfolge, 8 Instanzen, 30 Reihen, Türrate 2, Platzwechsel 3, Gepäckanteil 70 %; Gruppen als beliebige Sitze
einer Reihe). Das ist keine realisierbare Regel, sondern eine gefundene Reihenfolge: sie zeigt, dass mindestens so viel möglich ist; das wahre Optimum kann tiefer liegen (kein Optimalitätsbeweis).

Aufruf (aus dem Repo-Ordner, mit dem Python des Test-venv): python tools/make_results.py"""

import json
import math
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import brd_algorithm as A  # noqa: E402
from brd_scenario import Instance, SplitMix64, make_order  # noqa: E402

EVALS = 30000
SEEDS = tuple(range(1, 9))
CELLS = ((0, "seite"), (30, "reihe"), (70, "reihe"))
ROWS, E, SH = 30, 2, 3
T0, T1 = 6.0, 0.02                       # Temperatur: geometrisch von T0 auf T1


def anneal(args):
    seed, g, gtype, start = args
    inst = Instance(seed, R=ROWS, g=g / 100.0, ell=0.7, gtype=gtype)
    rng = SplitMix64(seed * 99991 + g + (7 if start == "random" else 0))
    group_of = {}
    for gi, members in enumerate(inst.groups):
        for i in members:
            group_of[i] = gi
    seq, seen = [], set()
    for i in make_order(inst, start):
        if group_of[i] not in seen:
            seen.add(group_of[i])
            seq.append(group_of[i])

    def flat(sq):
        out = []
        for gi in sq:
            out.extend(sorted(inst.groups[gi], key=lambda i: (-inst.row[i], inst.pos[i])))
        return out

    def evaluate(sq):
        return A.recursion(flat(sq), inst.row, inst.side, inst.pos, inst.stow, ROWS, e=E, sh=SH)[0]

    cur = evaluate(seq)
    best = cur
    n = len(seq)
    for it in range(EVALS):
        temp = T0 * (T1 / T0) ** (it / EVALS)
        i = int(rng.random() * n)
        j = int(rng.random() * n)
        if i == j:
            continue
        cand = list(seq)
        cand.insert(j, cand.pop(i))
        t = evaluate(cand)
        if t <= cur or rng.random() < math.exp(-(t - cur) / temp):
            seq, cur = cand, t
            best = min(best, t)
    random_t = A.recursion(make_order(inst, "random"), inst.row, inst.side, inst.pos, inst.stow, ROWS, e=E, sh=SH)[0]
    steffen_t = A.recursion(make_order(inst, "steffen"), inst.row, inst.side, inst.pos, inst.stow, ROWS, e=E, sh=SH)[0]
    return {"seed": seed, "g": g, "gtype": gtype, "start": start, "best": best, "random": random_t, "steffen": steffen_t, "entry": 1 + (ROWS * 6 - 1) * E}


def main():
    jobs = [(seed, g, gtype, start) for seed in SEEDS for g, gtype in CELLS for start in ("steffen", "random")]
    with Pool(4) as pool:
        raw = pool.map(anneal, jobs)
    rows = []
    for g, gtype in CELLS:
        cell = [r for r in raw if r["g"] == g]
        per_seed = {}
        for r in cell:
            per_seed.setdefault(r["seed"], []).append(r)
        best = [min(x["best"] for x in v) for v in per_seed.values()]
        from_steffen = [r["best"] for r in cell if r["start"] == "steffen"]
        from_random = [r["best"] for r in cell if r["start"] == "random"]
        first = [v[0] for v in per_seed.values()]
        rows.append({
            "g": g, "gtype": gtype, "n_instances": len(per_seed),
            "best": sum(best) / len(best), "best_from_steffen": sum(from_steffen) / len(from_steffen), "best_from_random": sum(from_random) / len(from_random),
            "steffen": sum(r["steffen"] for r in first) / len(first), "random": sum(r["random"] for r in first) / len(first), "entry": first[0]["entry"],
        })
    out = {"lookahead": rows, "evals": EVALS, "rows": ROWS, "e": E, "sh": SH, "ell": 70, "seeds": list(SEEDS)}
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "brd_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("fertig", json.dumps(rows))


if __name__ == "__main__":
    main()
