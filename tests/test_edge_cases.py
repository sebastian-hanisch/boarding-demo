"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): ein Fahrgast, eine Reihe, alle Gleichstände, Grenzen inklusive, Entartungen der Regler."""

import brd_algorithm as A
import brd_constants as C
import brd_evaluation as ev
import brd_runs as R
import brd_scenario as S
from conftest import mk


def test_single_passenger_and_empty_queue_rules():
    """n = 1: ein Fahrgast, Zeit = Reihe + Verstauzeit; der Gleichstand mit Verstauzeit 0 (sofort sitzen) ist definiert."""
    order, row, side, pos, stow = mk([(1, 0, 0, 0)])
    assert A.recursion(order, row, side, pos, stow, 1, e=2, sh=3)[0] == 1 == A.tick_sim(order, row, side, pos, stow, 1, e=2, sh=3)[0]


def test_exactly_two_passengers_in_the_same_row_and_cell():
    """n = 2: der kleinste Fall mit Blockierung (zwei Fahrgäste derselben Reihe: der zweite wartet auf den ersten)."""
    order, row, side, pos, stow = mk([(2, 0, 2, 3), (2, 1, 0, 3)])
    t, waits = A.recursion(order, row, side, pos, stow, 2, e=1, sh=3)
    assert t == A.tick_sim(order, row, side, pos, stow, 2, e=1, sh=3)[0] == 8 and waits == [0, 2]


def test_one_row_aircraft_and_smallest_door_rate():
    inst = S.Instance(3, R=1, g=0.5, ell=1.0, smax=12)
    assert inst.N == 6
    for rule in ("random", "b2f5", "steffen"):
        order = S.make_order(inst, rule)
        assert A.tick_sim(order, inst.row, inst.side, inst.pos, inst.stow, 1, e=1, sh=3) == A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, 1, e=1, sh=3)


def test_everybody_sits_immediately_is_the_entry_rhythm():
    """Alle Verstauzeiten 0 und Platzwechsel 0: Fenster vor Gang ergibt T = max_k(k e + r_k); extremes e = 8 (Tür ist der Engpass): T hängt kaum an der Reihenfolge."""
    inst = S.Instance(1, R=10, ell=0.0)
    times = [A.recursion(S.make_order(inst, r, ), inst.row, inst.side, inst.pos, inst.stow, 10, e=8, sh=0)[0] for r in C.MAIN_RULES]
    assert max(times) - min(times) <= 10 and min(times) >= 1 + 59 * 8


def test_bounds_of_the_regulators_are_inclusive():
    """Regler-Grenzen gelten inklusive: jeder Extremwert rechnet durch (Reihen 10 und 40, e 1 und 8, 0 und 100 % Gepäck, Verstauzeit 3 und 40, Platzwechsel 0 und 10, 0 und 70 % Gruppen, 0 und 90 % Ungehorsam)."""
    for kw in ({"rows": C.R_MIN}, {"rows": C.R_MAX}, {"e": C.E_MIN}, {"e": C.E_MAX}, {"ell": C.ELL_MIN}, {"ell": C.ELL_MAX}, {"smax": C.SMAX_MIN}, {"smax": C.SMAX_MAX},
               {"sh": C.SH_MIN}, {"sh": C.SH_MAX}, {"g": C.G_MIN}, {"g": C.G_MAX}, {"delta": C.DELTA_MIN}, {"delta": C.DELTA_MAX}, {"doors": 2, "rows": C.R_MIN}):
        a = ev.analyse(R.Settings(**kw), n_runs=3)
        assert all(row["T"] >= a.entry for row in a.rows), kw        # die Eintrittsschranke gilt auch an jedem Rand


def test_all_minima_and_all_maxima_together():
    lo = R.Settings(rows=C.R_MIN, e=C.E_MIN, ell=C.ELL_MIN, smax=C.SMAX_MIN, sh=C.SH_MIN, g=C.G_MIN, delta=C.DELTA_MIN)
    hi = R.Settings(rows=C.R_MAX, e=C.E_MAX, ell=C.ELL_MAX, smax=C.SMAX_MAX, sh=C.SH_MAX, g=C.G_MAX, delta=C.DELTA_MAX, gtype="nachbar", gmode="max", intra="aisle_first")
    for s in (lo, hi):
        a = ev.analyse(s, n_runs=3)
        assert len(a.rows) == len(C.MAIN_RULES)


def test_without_bags_every_rule_waits_nowhere_when_the_door_is_slow():
    """Ohne Gepäck und mit Platzwechsel 0 gibt es keine Blockierung außer dem Eintrittsrhythmus: Wartezeit je Fahrgast ist bei e = 2 nahe 0 für Steffen-artig."""
    a = ev.analyse(R.Settings(ell=0, sh=0), n_runs=5)
    assert a.row("steffen")["wait"] == 0.0


def test_groups_cover_everyone_even_at_the_largest_share_in_every_form():
    for gtype in C.GROUP_TYPES:
        inst = S.Instance(2, R=C.R_MAX, g=C.G_MAX / 100.0, gtype=gtype)
        assert sum(len(m) for m in inst.groups) == inst.N


def test_ratio_and_standard_error_for_identical_series_and_a_single_run():
    assert R.paired_ratio([5, 5], [5, 5]) == (1.0, 0.0)
    ratio, se = R.paired_ratio([10], [20])
    assert ratio == 0.5 and se == 0.0                  # ein Lauf: kein Standardfehler (definiert, keine Division durch null)
    assert R.wins([1, 2, 3], [2, 2, 2]) == 1           # Gleichstand zählt nicht als Sieg


def test_half_point_edge_cases():
    assert ev.half_point([0, 10, 20], [0.0, 0.0, 0.0]) is None           # kein Vorsprung ohne Ungehorsam
    assert ev.half_point([0, 10, 20], [0.2, 0.18, 0.15]) is None         # fällt im Raster nicht auf die Hälfte
    assert ev.half_point([0, 10], [0.2, 0.1]) == 10                      # genau die Hälfte am Rasterpunkt
    assert abs(ev.half_point([0, 10], [0.2, 0.0]) - 5.0) < 1e-12         # lineare Interpolation
