"""Jede Zahl der README (Abschnitt „Befunde“) wird hier nachgerechnet, mit ihrer Bedingung (DEMO-PLAYBOOK §4 und §11a).

Alle Läufe sind ganzzahlig und mit festem Zufalls-Seed (SplitMix64, Seed 35, 100 Läufe, gemeinsame Zufallszahlen für alle Regeln): auf jeder Plattform dieselben Zahlen.
Bänder: ± 0,0006 um den in der README auf drei Stellen gerundeten Wert (kein exakter Float-Vergleich)."""

import itertools
from functools import lru_cache
from pathlib import Path

import pytest

import brd_constants as C
import brd_evaluation as ev
import brd_results as RES
import brd_texts as T
from brd_runs import Settings, mean, run_rules

APPROX = dict(abs=6e-4)


@lru_cache(maxsize=None)
def analysis(**kw):
    return ev.analyse(Settings(**kw))


def ratio(rule, **kw):
    return analysis(**kw).row(rule)["ratio"]


# --- Basisfall ---------------------------------------------------------------------------------------------------------------------------

def test_base_case_ratios_to_random():
    """README-Tabelle „Basisfall“: 30 Reihen, eine Tür, e = 2, 70 % Gepäck, Verstauzeit 3 bis 12 Takte, Platzwechsel 3 Takte, 100 Läufe."""
    a = analysis()
    assert a.n_runs == 100
    expected = {"b2f5": 1.228, "f2b5": 1.447, "b2fRows": 1.855, "wilma": 0.882, "steffen": 0.738}
    for rule, value in expected.items():
        assert a.row(rule)["ratio"] == pytest.approx(value, **APPROX), rule
    assert round(a.row("random")["T"]) == 563 and round(a.row("steffen")["T"]) == 416 and a.entry == 359


def test_base_case_wins_against_random():
    a = analysis()
    assert [a.row(r)["wins"] for r in ("wilma", "steffen")] == [100, 100]
    assert [a.row(r)["wins"] for r in ("b2f5", "f2b5", "b2fRows")] == [0, 0, 0]


def test_base_case_distance_to_the_entry_bound():
    """Steffen-artig liegt 1,158-fach, Zufall 1,568-fach über der Eintrittsschranke von 359 Takten."""
    a = analysis()
    assert a.row("steffen")["over_bound"] == pytest.approx(1.158, **APPROX) and a.row("random")["over_bound"] == pytest.approx(1.568, **APPROX)


def test_every_rule_has_a_distinct_waiting_time_no_dead_column():
    """Keine Nullspalte: die Wartezeit je Regel unterscheidet sich (Steffen-artig am kleinsten, Rückwärts reihenweise am größten), jede Regel weicht von Zufall ab."""
    a = analysis()
    waits = {r["rule"]: r["wait"] for r in a.rows}
    assert min(waits, key=waits.get) == "steffen" and max(waits, key=waits.get) == "b2fRows"
    assert len({round(r["T"]) for r in a.rows}) == len(a.rows)


# --- Türrate -----------------------------------------------------------------------------------------------------------------------------

DOOR_TABLE = {  # e: (Steffen/Zufall, Steffen/Schranke, Zufall/Schranke, Rückwärts in 5 Blöcken/Zufall)
    1: (0.544, 1.591, 2.927, 1.300), 2: (0.738, 1.158, 1.568, 1.228), 3: (0.878, 1.069, 1.217, 1.077),
    4: (0.935, 1.037, 1.110, 0.977), 6: (0.969, 1.014, 1.046, 0.985), 8: (0.981, 1.007, 1.026, 0.990),
}


@pytest.mark.parametrize("e", sorted(DOOR_TABLE))
def test_door_rate_table(e):
    """README-Tabelle „Türrate“ (Basisfall, nur e verändert)."""
    a = analysis(e=e)
    expected = DOOR_TABLE[e]
    assert a.row("steffen")["ratio"] == pytest.approx(expected[0], **APPROX)
    assert a.row("steffen")["over_bound"] == pytest.approx(expected[1], **APPROX)
    assert a.row("random")["over_bound"] == pytest.approx(expected[2], **APPROX)
    assert a.row("b2f5")["ratio"] == pytest.approx(expected[3], **APPROX)


def test_slow_door_leaves_little_to_win():
    """Bei e = 8 liegen Steffen-artig und Zufall höchstens 2,6 % über der Eintrittsschranke; bei e = 1 liegt Zufall fast dreifach darüber."""
    assert analysis(e=8).row("random")["over_bound"] == pytest.approx(1.026, **APPROX) and analysis(e=8).row("random")["over_bound"] < 1.0265
    assert analysis(e=1).row("random")["over_bound"] > 2.9


def test_bottleneck_label_in_the_base_case():
    """Die App nennt den Gang den Engpass, wenn Zufall mindestens 15 % über der Eintrittsschranke liegt: im Basisfall bei e = 1 bis 3 Gang, ab e = 4 Tür; Regime-Karte 6 Türraten × 4 Verstauzeiten = 24 Zellen."""
    labels = {e: ev.regime_label(analysis(e=e).row("random")["over_bound"]) for e in (1, 2, 3, 4, 6, 8)}
    assert labels == {1: "Gang", 2: "Gang", 3: "Gang", 4: "Tür", 6: "Tür", 8: "Tür"} and C.GANG_BOUND == 1.15
    assert len(C.GRID_E) * len(C.GRID_SMAX) == 24


def test_backward_blocks_beat_random_only_with_a_slow_door():
    """Rückwärts in 5 Blöcken: bei e = 1 bis 3 schlechter als Zufall, bei e = 4, 6, 8 um 1,0 bis 2,4 % besser (Basisfall)."""
    assert all(ratio("b2f5", e=e) > 1.0 for e in (1, 2, 3))
    gains = [100 * (1 - ratio("b2f5", e=e)) for e in (4, 6, 8)]
    assert all(1.0 <= g <= 2.4 for g in gains), gains


def test_rank_order_grid():
    """Raster 3 Türraten (e 1 bis 3) × 3 Gepäckanteile (30, 70, 100 %) × 2 Ungehorsamenanteile (0, 30 %) × 2 Gruppenanteile (0, 50 %) × 2 Platzwechselzeiten (3, 6) = 72 Zellen, je 40 Läufe:
    Steffen-artig < WilMA < Zufall in 72 von 72 Zellen; Zufall < Rückwärts in 5 Blöcken in 61 von 72 (die 11 Ausnahmen haben alle 30 % Gepäck und e = 2 oder 3)."""
    steffen_wilma_random = zufall_besser = 0
    exceptions = []
    for e, ell, delta, g, sh in itertools.product((1, 2, 3), (30, 70, 100), (0, 30), (0, 50), (3, 6)):
        res = run_rules(Settings(e=e, ell=ell, delta=delta, g=g, sh=sh), ("random", "b2f5", "wilma", "steffen"), 40)
        m = {k: mean(v) for k, v in res["T"].items()}
        steffen_wilma_random += m["steffen"] < m["wilma"] < m["random"]
        if m["random"] < m["b2f5"]:
            zufall_besser += 1
        else:
            exceptions.append((e, ell))
    assert steffen_wilma_random == 72 and zufall_besser == 61
    assert len(exceptions) == 11 and all(ell == 30 and e in (2, 3) for e, ell in exceptions)


# --- Verstauzeit, Gepäck, Platzwechsel ----------------------------------------------------------------------------------------------------

def test_longer_stowing_time_helps_parallel_stowing_not_wilma():
    """Verstauzeit höchstens 6 / 12 / 24 / 40 Takte: Steffen-artig 0,823 / 0,738 / 0,627 / 0,562; WilMA 0,886 / 0,882 / 0,912 / 0,935 (Basisfall)."""
    for smax, steffen, wilma in ((6, 0.823, 0.886), (12, 0.738, 0.882), (24, 0.627, 0.912), (40, 0.562, 0.935)):
        assert ratio("steffen", smax=smax) == pytest.approx(steffen, **APPROX), smax
        assert ratio("wilma", smax=smax) == pytest.approx(wilma, **APPROX), smax


def test_baggage_share():
    """Gepäckanteil 0 / 30 / 70 / 100 %: Steffen-artig 0,907 / 0,838 / 0,738 / 0,679 (Basisfall)."""
    for ell, steffen in ((0, 0.907), (30, 0.838), (70, 0.738), (100, 0.679)):
        assert ratio("steffen", ell=ell) == pytest.approx(steffen, **APPROX), ell


def test_wilma_lead_comes_from_the_seat_change():
    """Platzwechsel 0 / 3 / 6 / 10 Takte: WilMA 0,995 / 0,882 / 0,768 / 0,645, Steffen-artig 0,833 / 0,738 / 0,643 / 0,540; bei 0 Takten schlägt WilMA Zufall nur in 58 von 100 Läufen, sonst in 100 von 100."""
    for sh, wilma, steffen in ((0, 0.995, 0.833), (3, 0.882, 0.738), (6, 0.768, 0.643), (10, 0.645, 0.540)):
        assert ratio("wilma", sh=sh) == pytest.approx(wilma, **APPROX), sh
        assert ratio("steffen", sh=sh) == pytest.approx(steffen, **APPROX), sh
    assert analysis(sh=0).row("wilma")["wins"] == 58 and all(analysis(sh=sh).row("wilma")["wins"] == 100 for sh in (3, 6, 10))


# --- Gruppen -----------------------------------------------------------------------------------------------------------------------------

def test_groups_steffen_ratio_and_share():
    """Gruppen als Paare und Dreier nebeneinander in einer Reihenseite: Sollanteil 0 / 10 / 30 / 50 / 70 % (tatsächlich 0 / 10,3 / 30,3 / 50,7 / 70,1 %): Steffen-artig 0,738 / 0,743 / 0,755 / 0,768 / 0,781."""
    for g, steffen, share in ((0, 0.738, 0.0), (10, 0.743, 0.103), (30, 0.755, 0.303), (50, 0.768, 0.507), (70, 0.781, 0.701)):
        a = analysis(g=g)
        assert a.row("steffen")["ratio"] == pytest.approx(steffen, **APPROX), g
        assert a.grouped == pytest.approx(share, abs=6e-4), g


def test_groups_cost_steffen_four_points_and_keep_the_order():
    """Steffen-artig: Vorsprung 26,2 % ohne Gruppen, 21,9 % bei 70 % Gruppen; WilMA 0,882 → 0,923; Rückwärts reihenweise wird besser (1,855 → 1,656)."""
    assert 100 * (1 - ratio("steffen", g=0)) == pytest.approx(26.2, abs=0.05) and 100 * (1 - ratio("steffen", g=70)) == pytest.approx(21.9, abs=0.05)
    assert ratio("wilma", g=70) == pytest.approx(0.923, **APPROX)
    assert ratio("b2fRows", g=0) == pytest.approx(1.855, **APPROX) and ratio("b2fRows", g=70) == pytest.approx(1.656, **APPROX)
    assert ratio("steffen", g=70) < ratio("wilma", g=70) < 1.0 < ratio("b2f5", g=70)


def test_calling_a_group_at_its_latest_member_wins_back_part_of_the_loss():
    """Aufruf zum spätesten Mitglied bei 70 % Gruppen: Steffen-artig 0,753 statt 0,781 (Vorsprung 24,7 statt 21,9 %); WilMA 0,936 statt 0,923 (verliert)."""
    assert ratio("steffen", g=70, gmode="max") == pytest.approx(0.753, **APPROX)
    assert ratio("wilma", g=70, gmode="max") == pytest.approx(0.936, **APPROX) and ratio("wilma", g=70, gmode="max") > ratio("wilma", g=70)


# --- Ungehorsam --------------------------------------------------------------------------------------------------------------------------

def test_disobedience_table_and_half_point():
    """Ungehorsame Gruppen 0 / 10 / 20 / 30 / 50 / 75 %: Steffen-artig 0,738 / 0,779 / 0,813 / 0,843 / 0,900 / 0,963; der Vorsprung halbiert sich bei etwa 39 % (lineare Interpolation)."""
    deltas = (0, 10, 20, 30, 50, 75)
    steffen = (0.738, 0.779, 0.813, 0.843, 0.900, 0.963)
    for d, value in zip(deltas, steffen):
        assert ratio("steffen", delta=d) == pytest.approx(value, **APPROX), d
    half = ev.half_point(list(deltas), [1 - ratio("steffen", delta=d) for d in deltas])
    assert half == pytest.approx(39.2, abs=0.1)


def test_disobedience_makes_backward_blocks_better_only_with_a_fast_door():
    """Rückwärts in 5 Blöcken: 1,228 / 1,085 / 1,015 / 0,989 bei 0 / 30 / 50 / 75 % Ungehorsam (e = 2, nähert sich dem Zufall); bei e = 4 und e = 8 wird sie nicht besser:
    0,977 → 0,995 bzw. 0,990 → 0,998 bei 0 → 75 %."""
    for d, value in ((0, 1.228), (30, 1.085), (50, 1.015), (75, 0.989)):
        assert ratio("b2f5", delta=d) == pytest.approx(value, **APPROX), d
    for e, before, after in ((4, 0.977, 0.995), (8, 0.990, 0.998)):
        assert ratio("b2f5", e=e) == pytest.approx(before, **APPROX), e
        assert ratio("b2f5", e=e, delta=75) == pytest.approx(after, **APPROX) and ratio("b2f5", e=e, delta=75) > ratio("b2f5", e=e), e


def test_steffen_lead_without_seat_change_and_group_internal_order():
    """Steffen-artig ohne Platzwechsel: Vorsprung 16,7 % (0,833); Rückwärts reihenweise bei 70 % Gruppen mit „Gang zuerst“ innerhalb der Gruppe 1,724 (statt 1,656 mit „Fenster zuerst“)."""
    assert 100 * (1 - ratio("steffen", sh=0)) == pytest.approx(16.7, abs=0.05)
    assert ratio("b2fRows", g=70, intra="aisle_first") == pytest.approx(1.724, **APPROX) and ratio("b2fRows", g=70, intra="aisle_first") > ratio("b2fRows", g=70)


# --- Zwei Türen --------------------------------------------------------------------------------------------------------------------------

def test_two_doors():
    """Zwei Türen (zwei Hälften zu je 15 Reihen): Zufall 348 Takte statt 563; Steffen-artig 0,689, WilMA 0,848, Rückwärts reihenweise 1,569 des Zufalls."""
    a = analysis(doors=2)
    assert round(a.row("random")["T"]) == 348
    assert a.row("steffen")["ratio"] == pytest.approx(0.689, **APPROX) and a.row("wilma")["ratio"] == pytest.approx(0.848, **APPROX)
    assert a.row("b2fRows")["ratio"] == pytest.approx(1.569, **APPROX)


# --- Vorgerechnete Voraussicht -----------------------------------------------------------------------------------------------------------

def test_lookahead_precomputed_values():
    """`data/brd_results.json`: 8 Instanzen, 30000 Auswertungen: beste gefundene Reihenfolge 387 / 393 / 402 Takte bei 0 / 30 / 70 % Gruppen gegen Steffen-artig 412 / 427 / 457; die beste liegt 6,0 / 8,0 / 12,2 % darunter und 7,8 / 9,4 / 11,8 % über der Eintrittsschranke 359."""
    rows = RES.lookahead_rows(RES.load_results())
    assert [r["g"] for r in rows] == [0, 30, 70] and all(r["n_instances"] == 8 and r["entry"] == 359 for r in rows)
    assert [round(r["best"]) for r in rows] == [387, 393, 402] and [round(r["steffen"]) for r in rows] == [412, 427, 457]
    assert [round(100 * (1 - r["best"] / r["steffen"]), 1) for r in rows] == [6.0, 8.0, 12.2]
    assert [round(100 * (r["best"] / r["entry"] - 1), 1) for r in rows] == [7.8, 9.4, 11.8]
    assert RES.load_results()["evals"] == 30000


def test_lookahead_best_is_never_slower_than_either_start():
    for r in RES.lookahead_rows(RES.load_results()):
        assert r["best"] <= r["best_from_steffen"] and r["best"] <= r["best_from_random"] and r["best"] <= r["steffen"] and r["best"] >= r["entry"]


# --- Texte: zwei Fassungen desselben Textes ----------------------------------------------------------------------------------------------

def test_assumptions_text_in_the_readme_is_the_text_of_the_app():
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    assert T.ASSUMPTIONS_MARKDOWN.strip() in readme


def test_every_rule_description_is_in_the_readme():
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    for rule in C.MAIN_RULES:
        assert T.RULE_DESCRIPTIONS[rule] in readme, rule
