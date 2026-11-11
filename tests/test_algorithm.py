"""Einheiten des Kerns an der Mini-Instanz von Hand (DEMO-PLAYBOOK §1b): Zufallsgenerator, Instanz, Regeln, Taktsimulation, Zustand und Schranken."""

import pytest

import brd_algorithm as A
import brd_scenario as S
from conftest import mk


def test_splitmix64_reference_values():
    """Referenzwerte des SplitMix64-Generators (Seed 0 und Seed 1234567, Testvektoren von Vigna)."""
    r = S.SplitMix64(0)
    assert [r.next_u64() for _ in range(3)] == [16294208416658607535, 7960286522194355700, 487617019471545679]
    r = S.SplitMix64(1234567)
    assert [r.next_u64() for _ in range(2)] == [6457827717110365317, 3203168211198807973]


def test_random_is_in_unit_interval_and_deterministic():
    a = [S.SplitMix64(7).random() for _ in range(3)]
    assert a[0] == a[1] == a[2] and 0.0 <= a[0] < 1.0


def test_mini_instance_by_hand(mini):
    """Handrechnung: T = 9 in Taktsimulation und Rekursion; Fahrgast 1 wartet in Zelle 1 von Takt 4 bis 5 (2 Takte)."""
    order, row, side, pos, stow = mini
    t_tick, waits_tick = A.tick_sim(order, row, side, pos, stow, 3, e=2, sh=3)
    t_rec, waits_rec = A.recursion(order, row, side, pos, stow, 3, e=2, sh=3)
    assert t_tick == t_rec == 9
    assert waits_tick == waits_rec == [0, 2, 0]


def test_state_over_time_by_hand(mini):
    """Zustand der Mini-Instanz: Takt 0 leer, Takt 2 Fahrgast 0 verstaut in Reihe 2, Takt 6 sitzt Fahrgast 0 und Fahrgast 2 steht in Reihe 1, Takt 9 alle sitzen."""
    order, row, side, pos, stow = mini
    args = (order, row, side, pos, stow, 3)
    occ, seated, working = A.tick_state(*args, e=2, sh=3, t_stop=0)
    assert occ == [None, None, None] and seated == set() and working == set()
    occ, seated, working = A.tick_state(*args, e=2, sh=3, t_stop=2)
    assert occ == [None, 0, None] and seated == set() and working == {0}
    occ, seated, working = A.tick_state(*args, e=2, sh=3, t_stop=6)
    assert seated == {0} and occ == [2, 1, None] and working == {2}
    occ, seated, working = A.tick_state(*args, e=2, sh=3, t_stop=9)
    assert seated == {0, 1, 2} and occ == [None, None, None]
    occ, seated, working = A.tick_state(*args, e=2, sh=3, t_stop=500)
    assert seated == {0, 1, 2}


def test_lower_bounds_of_the_mini_instance(mini):
    """Eintrittsschranke 1 + (3 - 1) * 2 = 5; Reihenschranke max(2 + 4, 3 + 2, 1 + 3) = 6; beide liegen unter T = 9."""
    order, row, side, pos, stow = mini
    entry, rows_b, chain, any_b = A.lower_bounds(order, row, stow, 3, e=2)
    assert entry == 5 and rows_b == 6 and any_b == 6 and chain <= 9


def test_seat_change_costs_time():
    """Ein Fahrgast auf dem Fensterplatz, der Gangplatz derselben Reihenseite ist schon besetzt: Platzwechsel sh Takte zusätzlich."""
    order, row, side, pos, stow = mk([(2, 0, 2, 0), (2, 0, 0, 0)])
    t0, _ = A.recursion(order, row, side, pos, stow, 3, e=1, sh=0)
    t3, _ = A.recursion(order, row, side, pos, stow, 3, e=1, sh=3)
    assert t3 - t0 == 3
    reverse = mk([(2, 0, 0, 0), (2, 0, 2, 0)])       # Fenster zuerst: kein Platzwechsel
    assert A.recursion(*reverse, 3, e=1, sh=3)[0] == A.recursion(*reverse, 3, e=1, sh=0)[0]


def test_rule_batches():
    """Blockzuordnung der Regeln an Hand gesetzten Sitzen (30 Reihen)."""
    assert S.rule_batch("random", 5, 0, 1, 30) == (0, 0)
    assert S.rule_batch("b2f5", 30, 0, 0, 30)[0] == 0 and S.rule_batch("b2f5", 1, 0, 0, 30)[0] == 4        # hinten zuerst
    assert [S.rule_batch("b2f5", r, 0, 0, 30)[0] for r in (6, 7, 24, 25)] == [4, 3, 1, 0]      # Block 1 = Reihen 1 bis 6, Block 5 = Reihen 25 bis 30
    assert S.rule_batch("f2b5", 1, 0, 0, 30)[0] == 0 and S.rule_batch("f2b5", 30, 0, 0, 30)[0] == 4
    assert S.rule_batch("b2fRows", 30, 0, 0, 30)[0] == 0 and S.rule_batch("b2fRows", 1, 0, 0, 30)[0] == 29
    assert [S.rule_batch("wilma", 9, 0, p, 30)[0] for p in (0, 1, 2)] == [0, 1, 2]
    assert S.rule_batch("steffen", 30, 0, 0, 30) < S.rule_batch("steffen", 28, 0, 0, 30) < S.rule_batch("steffen", 29, 0, 0, 30)   # gerade Reihen von hinten, dann ungerade
    with pytest.raises(ValueError):
        S.rule_batch("unbekannt", 1, 0, 0, 30)


def test_steffen_like_order_has_two_rows_between_consecutive_passengers():
    """Steffen-artig: Fenster vor Mitte vor Gang; innerhalb einer Klasse und Seite folgen die geraden Reihen von hinten nach vorn (je zwei Reihen auseinander), dann die ungeraden."""
    inst = S.Instance(1, R=10, g=0.0, ell=0.0)
    order = S.make_order(inst, "steffen")
    window_left = [inst.row[i] for i in order if inst.pos[i] == 0 and inst.side[i] == 0]
    assert window_left == [10, 8, 6, 4, 2, 9, 7, 5, 3, 1]
    classes = [inst.pos[i] for i in order]
    assert classes == sorted(classes)                 # erst alle Fenster, dann alle Mitten, dann alle Gänge


def test_make_order_is_a_permutation_for_every_rule_and_group_form():
    for gtype in ("seite", "reihe", "nachbar"):
        inst = S.Instance(3, R=12, g=0.5, ell=0.7, delta=0.3, gtype=gtype)
        for rule in ("random", "b2f5", "f2b5", "b2fRows", "wilma", "steffen"):
            for gmode in ("min", "max"):
                for intra in ("window_first", "aisle_first"):
                    order = S.make_order(inst, rule, intra=intra, gmode=gmode)
                    assert sorted(order) == list(range(inst.N)), (gtype, rule, gmode, intra)


def test_groups_partition_the_seats_and_stay_in_one_place():
    for gtype in ("seite", "reihe", "nachbar"):
        inst = S.Instance(5, R=10, g=0.7, ell=0.7, gtype=gtype)
        members = sorted(i for grp in inst.groups for i in grp)
        assert members == list(range(inst.N))
        assert all(1 <= len(grp) <= 3 for grp in inst.groups)
        for grp in inst.groups:
            if gtype == "seite":
                assert len({(inst.row[i], inst.side[i]) for i in grp}) == 1
            elif gtype == "reihe":
                assert len({inst.row[i] for i in grp}) == 1
            else:
                assert max(inst.row[i] for i in grp) - min(inst.row[i] for i in grp) <= 1


def test_no_groups_means_single_passengers():
    inst = S.Instance(2, R=8, g=0.0)
    assert inst.ngroups == inst.N and inst.grouped_share == 0.0


def test_baggage_share_zero_and_one():
    none = S.Instance(4, R=10, ell=0.0)
    assert set(none.stow) == {0}
    every = S.Instance(4, R=10, ell=1.0, smin=3, smax=12)
    assert all(3 <= w <= 12 for w in every.stow)


def test_shared_random_numbers_make_smaller_settings_subsets():
    """Gemeinsame Zufallszahlen: Gepäck und Gruppenanteil wachsen monoton; ungehorsam bei kleinem δ bleibt ungehorsam bei größerem."""
    for seed in range(20):
        a, b = S.Instance(seed, R=10, ell=0.3, g=0.2), S.Instance(seed, R=10, ell=0.7, g=0.5)
        assert all((a.stow[i] > 0) <= (b.stow[i] > 0) for i in range(a.N))
        assert a.grouped_share <= b.grouped_share + 1e-12
        small, large = S.Instance(seed, R=10, delta=0.1), S.Instance(seed, R=10, delta=0.4)
        assert small.groups == large.groups
        assert all(d1 <= d2 for d1, d2 in zip(small.gdis, large.gdis))


def test_two_doors_use_separate_random_streams():
    a, b = S.Instance(9, R=5, sub=0), S.Instance(9, R=5, sub=1)
    assert a.stow != b.stow
