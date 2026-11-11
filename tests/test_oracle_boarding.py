"""Orakel-Tests des Boarding-Kerns (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §2): andere Rechenwege als der der App.

Die App rechnet mit der Zeit-Gitter-Rekursion (`recursion`). Orakel: (1) die unabhängig geschriebene Taktsimulation (`tick_sim`) auf Zufallsinstanzen, (2) geschlossene Zeiten für
einen und zwei Fahrgäste, (3) die Formel T = max_k((k-1) e + r_k) ohne Verstauzeit und Platzwechsel für jede Regel, (4) die Reihe an der Tür von Hand, (5) die Aufzählung aller
Reihenfolgen bei kleiner Fahrgastzahl, (6) die Schranken. Zufallsinstanzen mit festen Seeds, insgesamt wenige Sekunden."""

from itertools import permutations

import pytest

import brd_algorithm as A
import brd_exhaustive as X
import brd_scenario as S
from conftest import mk

RULES = ("random", "b2f5", "f2b5", "b2fRows", "wilma", "steffen")


def test_one_passenger_takes_row_plus_baggage_time():
    """Ein Fahrgast: T = Reihe + Verstauzeit, in beiden Rechenwegen (für jede Reihe, Verstauzeit 0 bis 12 und Türrate)."""
    count = 0
    for r in range(1, 31):
        for w in (0, 1, 5, 12):
            for e in (1, 2, 4):
                order, row, side, pos, stow = mk([(r, 0, 1, w)])
                assert A.tick_sim(order, row, side, pos, stow, 30, e=e, sh=3)[0] == A.recursion(order, row, side, pos, stow, 30, e=e, sh=3)[0] == r + w
                count += 1
    assert count == 360


def test_two_passengers_follow_the_closed_formula():
    """Zwei Fahrgäste: geschlossene Zeit je nach Lage der zweiten Reihe zur ersten (vorn, hinten, gleiche Reihe mit Platzwechsel)."""
    rng = S.SplitMix64(777)
    cases = {"vorn": 0, "hinten": 0, "gleich": 0}
    for _ in range(1500):
        rows = 12
        r1, r2 = 1 + int(rng.random() * rows), 1 + int(rng.random() * rows)
        s1, s2 = int(rng.random() * 2), int(rng.random() * 2)
        p1, p2 = int(rng.random() * 3), int(rng.random() * 3)
        if (r1, s1, p1) == (r2, s2, p2):
            continue
        w1 = int(rng.random() * 13) if rng.random() < 0.7 else 0
        w2 = int(rng.random() * 13) if rng.random() < 0.7 else 0
        e, sh = 1 + int(rng.random() * 4), int(rng.random() * 5)
        order, row, side, pos, stow = mk([(r1, s1, p1, w1), (r2, s2, p2, w2)])
        end1 = r1 + w1
        extra = sh if (r1 == r2 and s1 == s2 and p1 > p2) else 0   # der Gangplatz (größerer Platz) sitzt schon: Platzwechsel für den Fensterplatz
        if r2 < r1:
            expected = max(end1, r2 + e + w2 + extra)
            cases["vorn"] += 1
        else:
            arrive2 = max(r2 + e, end1 + (r2 - r1))
            expected = max(end1, arrive2 + w2 + extra)
            cases["hinten" if r2 > r1 else "gleich"] += 1
        for fn in (A.tick_sim, A.recursion):
            assert fn(order, row, side, pos, stow, rows, e=e, sh=sh)[0] == expected, (r1, r2, s1, s2, p1, p2, w1, w2, e, sh)
    assert all(v > 30 for v in cases.values()), cases      # alle drei Fälle kommen vor


def test_without_baggage_and_seat_change_time_is_the_entry_rhythm():
    """Ohne Verstauzeit und Platzwechsel: T = max_k((k - 1) e + r_k) für k = 1, …, N (im Test mit k ab 0 geschrieben: k e + r_k) für jede Regel und Gruppenform."""
    for seed in range(60):
        for rule in RULES:
            inst = S.Instance(seed, R=30, g=0.3, ell=0.0)
            order = S.make_order(inst, rule)
            e = (1, 2, 4)[seed % 3]
            expected = max(k * e + inst.row[p] for k, p in enumerate(order))
            assert A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, 30, e=e, sh=0)[0] == expected, (seed, rule, e)
            assert A.tick_sim(order, inst.row, inst.side, inst.pos, inst.stow, 30, e=e, sh=0)[0] == expected, (seed, rule, e)


def test_row_at_the_door_by_hand():
    """Reihe 1 liegt an der Tür: Fahrgast k sitzt bei max(Eintritt, Ende von k-1) + Verstauzeit + Platzwechsel (Rekursion von Hand, 1 bis 6 Fahrgäste)."""
    rng = S.SplitMix64(4242)
    for _ in range(300):
        seats = sorted([(s, p) for s in range(2) for p in range(3)], key=lambda x: rng.random())[: 1 + int(rng.random() * 6)]
        weights = [int(rng.random() * 13) if rng.random() < 0.7 else 0 for _ in seats]
        e, sh = 1 + int(rng.random() * 4), int(rng.random() * 5)
        order, row, side, pos, stow = mk([(1, s, p, w) for (s, p), w in zip(seats, weights)])
        expected, prev_end, prev_arrival, seated = 0, 0, 0, []
        for k, ((s, p), w) in enumerate(zip(seats, weights)):
            extra = sh * sum(1 for (s2, p2) in seated if s2 == s and p2 > p)
            arrival = 1 if k == 0 else max(prev_arrival + e, prev_end)
            prev_arrival, prev_end = arrival, arrival + w + extra
            expected = max(expected, prev_end)
            seated.append((s, p))
        assert A.tick_sim(order, row, side, pos, stow, 1, e=e, sh=sh)[0] == A.recursion(order, row, side, pos, stow, 1, e=e, sh=sh)[0] == expected


def test_tick_simulation_equals_recursion_on_random_instances():
    """Taktsimulation und Rekursion liefern auf Zufallsinstanzen (alle Regeln, Gruppenformen, Ungehorsam) dieselbe Zeit und dieselbe Wartezeit je Fahrgast; die Schranken liegen darunter."""
    rng = S.SplitMix64(31337)
    pick = lambda options: options[int(rng.random() * len(options))]  # noqa: E731
    for k in range(500):
        rows, g, ell, delta = pick([4, 8, 15, 30]), pick([0, 0.2, 0.5, 0.7]), pick([0.0, 0.3, 0.7, 1.0]), pick([0, 0.1, 0.3, 1.0])
        e, sh, rule = pick([1, 2, 4]), pick([0, 3, 5]), pick(list(RULES))
        inst = S.Instance(k, R=rows, g=g, ell=ell, delta=delta, gtype=pick(["seite", "reihe", "nachbar"]))
        order = S.make_order(inst, rule, intra=pick(["window_first", "aisle_first"]), gmode=pick(["min", "max"]))
        a, wa = A.tick_sim(order, inst.row, inst.side, inst.pos, inst.stow, rows, e=e, sh=sh)
        b, wb = A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, rows, e=e, sh=sh)
        assert a == b and wa == wb, (k, rule, rows, g, ell, delta, e, sh)
        assert all(bound <= a for bound in A.lower_bounds(order, inst.row, inst.stow, rows, e=e)), k


def test_waiting_time_is_zero_without_baggage_for_window_first_rules():
    """Ohne Verstauzeit blockiert niemand: Fenster vor Gang und Steffen-artig (Abstand zwei Reihen) lassen jeden durch; die Wartezeit ist 0 bei e = 2 für Steffen-artig und WilMA."""
    for seed in range(20):
        inst = S.Instance(seed, R=30, ell=0.0)
        for rule in ("wilma", "steffen"):
            order = S.make_order(inst, rule)
            assert max(A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, 30, e=2, sh=3)[1]) == 0


def test_enumeration_of_all_orders_equals_between_both_computations():
    """Aufzählung aller Reihenfolgen bei 6 Fahrgästen: das Minimum ist in Taktsimulation und Rekursion dasselbe; die Reihenfolge der Rekursion erreicht es."""
    for seed in range(3):
        rng = S.SplitMix64(seed + 99)
        passengers = [(1 + int(rng.random() * 3), 0, (0, 2)[i % 2], int(rng.random() * 8)) for i in range(6)]
        _, row, side, pos, stow = mk(passengers)
        if len({(r, p) for r, p in zip(row, pos)}) < 6:
            continue                                       # zwei Fahrgäste auf demselben Sitz: keine gültige Belegung
        best_rec = min(A.recursion(list(o), row, side, pos, stow, 3, e=2, sh=3)[0] for o in permutations(range(6)))
        best_tick = min(A.tick_sim(list(o), row, side, pos, stow, 3, e=2, sh=3)[0] for o in permutations(range(6)))
        assert best_rec == best_tick


def test_mini_aircraft_enumeration_matches_the_independent_simulation():
    """`enumerate_all` (Rekursion über alle 8! Reihenfolgen) gegen die Taktsimulation auf einer Stichprobe der Reihenfolgen; beste und schlechteste Zeit liegen in den Schranken."""
    row, side, pos, stow = X.mini_instance(5, 0.7, 12)
    result = X.enumerate_all(row, side, pos, stow, 2, 3)
    assert result["count"] == 40320
    assert result["best"] <= result["steffen"] <= result["worst"] and result["best"] <= result["mean"] <= result["worst"]
    order = X.steffen_like_order(row, pos)
    assert A.tick_sim(order, row, side, pos, stow, X.MINI_ROWS, e=2, sh=3)[0] == result["steffen"]
    for idx, perm in enumerate(permutations(range(8))):
        if idx % 997 == 0:
            t = A.tick_sim(list(perm), row, side, pos, stow, X.MINI_ROWS, e=2, sh=3)[0]
            assert result["best"] <= t <= result["worst"]
    entry, rows_b, _, any_b = A.lower_bounds(order, row, stow, X.MINI_ROWS, e=2)
    assert result["best"] >= any_b


def test_bounds_hold_for_every_order_of_a_small_instance():
    order, row, side, pos, stow = mk([(2, 0, 0, 3), (2, 0, 2, 4), (3, 1, 1, 5), (1, 0, 1, 2), (3, 0, 2, 0)])
    bound = A.lower_bounds(order, row, stow, 3, e=2)[3]
    assert all(A.recursion(list(o), row, side, pos, stow, 3, e=2, sh=3)[0] >= bound for o in permutations(range(5)))


@pytest.mark.parametrize("sh", [0, 3])
def test_seat_change_time_does_not_change_the_window_first_order(sh):
    """Fenster vor Gang: nie ein Platzwechsel, die Zeit hängt nicht von sh ab."""
    inst = S.Instance(11, R=20, ell=0.7)
    order = S.make_order(inst, "wilma")
    base = A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, 20, e=2, sh=0)[0]
    assert A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, 20, e=2, sh=sh)[0] == base
