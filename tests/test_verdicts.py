"""Verdikte (reine Funktionen in brd_evaluation.py): Schwellen und jede Zahl im Text an handgesetzten Werten (DEMO-PLAYBOOK §12, Bauregel 2)."""

import brd_constants as C
import brd_evaluation as ev
from brd_runs import Settings


def _analysis(settings, ratios, times, entry=359.0):
    """Handgesetzte Analyse: je Regel Verhältnis und Zeit; über_Schranke = Zeit / Schranke."""
    rows = tuple({"rule": r, "T": times[r], "ratio": ratios[r], "se": 0.003, "wins": 0, "wait": 1.0, "over_bound": times[r] / entry} for r in C.MAIN_RULES)
    return ev.Analysis(settings, rows, entry, 100, 0.0)


TIMES = {"random": 560.0, "b2f5": 690.0, "f2b5": 810.0, "b2fRows": 1040.0, "wilma": 500.0, "steffen": 420.0}
RATIOS = {r: TIMES[r] / TIMES["random"] for r in TIMES}


def test_regime_verdict_success_names_every_number():
    kind, text = ev.verdict_regime(_analysis(Settings(e=2), RATIOS, TIMES))
    assert kind == "success"
    # 420 / 560 = 0,75: 25,0 % gespart; 420 / 359 = 1,1699: noch 17,0 % über der Schranke; Zufall 560 / 359 = 1,56: 56,0 % darüber, also bremst der Gang (ab 15 %)
    assert "**25,0 %**" in text and "420 gegen 560 Takte" in text and "noch 17,0 % über der Eintrittsschranke." in text
    assert "Zufall liegt 56,0 % über der Eintrittsschranke von 359 Takten: bei e = 2 bremst Gang" in text and "Steffen-artig liegt 25,0 % unter Zufall" in text
    assert "Steffen-artig (Rekonstruktion)" in text


def test_regime_verdict_small_gain_but_far_from_the_bound_does_not_claim_that_nothing_is_left():
    """Regressionstest der Aussagenprüfung: bei kleinem Gewinn, aber weit entfernter Schranke (z. B. viel Ungehorsam) darf nicht „Mehr ist nicht zu holen“ stehen."""
    times = {**TIMES, "steffen": 540.0, "wilma": 552.0, "b2f5": 570.0, "f2b5": 600.0, "b2fRows": 610.0}
    kind, text = ev.verdict_regime(_analysis(Settings(e=2), {r: times[r] / times["random"] for r in times}, times))
    assert kind == "info" and "spart hier nur 3,6 %" in text and "540 gegen 560 Takte" in text
    assert "Die Regeln holen davon kaum etwas." in text and "Mehr ist nicht zu holen" not in text and "bremst Gang" in text


def test_regime_verdict_slow_door_close_to_the_bound_says_nothing_is_left():
    times = {**TIMES, "steffen": 540.0, "wilma": 552.0, "b2f5": 570.0, "f2b5": 600.0, "b2fRows": 610.0}
    kind, text = ev.verdict_regime(_analysis(Settings(e=6), {r: times[r] / times["random"] for r in times}, times, entry=545.0))
    # Zufall 560 / 545 = 1,0275: 2,8 % darüber, also bremst die Tür
    assert kind == "info" and "Zufall liegt 2,8 % über der Eintrittsschranke von 545 Takten: bei e = 6 bremst Tür" in text and text.endswith("Mehr ist nicht zu holen.")


def test_regime_verdict_random_is_best():
    times = {**TIMES, "steffen": 600.0, "wilma": 580.0}
    kind, text = ev.verdict_regime(_analysis(Settings(e=8), {r: times[r] / times["random"] for r in times}, times))
    assert kind == "info" and "schlägt keine Regel den Zufall" in text and "Zufall mit 560 Takten" in text


def test_bottleneck_label_follows_the_distance_to_the_bound_not_the_door_rate():
    """Gang ab 15 % Abstand von Zufall zur Eintrittsschranke (Grenze inklusive), sonst Tür; unabhängig von e (Regressionstest: bei Verstauzeit 40 und e = 4 stand „Tür“ trotz 72 % Abstand)."""
    assert ev.regime_label(1.15) == "Gang" and ev.regime_label(1.149) == "Tür" and ev.regime_label(2.9) == "Gang" and ev.regime_label(1.0) == "Tür"
    kind, text = ev.verdict_regime(_analysis(Settings(e=4, smax=40), RATIOS, TIMES))
    assert "bei e = 4 bremst Gang" in text


def test_groups_verdict():
    rows = [{"g": 0, "grouped_min": 0.0, "steffen_min": 0.74, "steffen_max": 0.74}, {"g": 70, "grouped_min": 0.7, "steffen_min": 0.78, "steffen_max": 0.75}]
    kind, text = ev.verdict_groups({"rows": rows, "n_runs": 40})
    assert kind == "info"
    assert "26,0 % unter Zufall" in text and "bei 70 % Sollanteil in Gruppen (tatsächlich 70 %) noch 22,0 %" in text and "sind es 25,0 %" in text


def test_disobedience_verdict_with_interpolated_half():
    rows = [{"delta": 0, "steffen": 0.74, "b2f5": 1.2}, {"delta": 30, "steffen": 0.84, "b2f5": 1.08}, {"delta": 50, "steffen": 0.90, "b2f5": 1.02}]
    kind, text = ev.verdict_disobedience({"rows": rows, "n_runs": 40})
    # Vorsprung 0,26 -> 0,16 -> 0,10; Hälfte 0,13 liegt zwischen 30 und 50: 30 + 20 * (0,16 - 0,13) / (0,16 - 0,10) = 40
    assert kind == "info" and "26,0 % unter Zufall" in text and "10,0 %" in text and "bei etwa 40 % Ungehorsamen" in text and "1,200 gegen 1,020" in text


def test_disobedience_verdict_does_not_call_a_worse_ratio_better():
    """Regressionstest der Aussagenprüfung: bei langsamer Tür steigt das Verhältnis von Rückwärts in 5 Blöcken (0,977 → 0,995), der Text darf es nicht „besser“ nennen."""
    rows = [{"delta": 0, "steffen": 0.935, "b2f5": 0.977}, {"delta": 75, "steffen": 0.99, "b2f5": 0.995}]
    text = ev.verdict_disobedience({"rows": rows, "n_runs": 40})[1]
    assert "wird dadurch nicht besser: Verhältnis zu Zufall 0,977 gegen 0,995" in text and "wird dadurch besser" not in text


def test_disobedience_verdict_without_halving():
    rows = [{"delta": 0, "steffen": 0.74, "b2f5": 1.2}, {"delta": 30, "steffen": 0.78, "b2f5": 1.1}]
    assert "halbiert sich im gemessenen Bereich nicht" in ev.verdict_disobedience({"rows": rows, "n_runs": 40})[1]


def test_swap_verdict_both_forms():
    rows = [{"sh": 0, "steffen": 0.833, "wilma": 0.995, "wilma_wins": 40, "steffen_wins": 40}, {"sh": 3, "steffen": 0.738, "wilma": 0.882, "wilma_wins": 40, "steffen_wins": 40}]
    text = ev.verdict_swap({"rows": rows, "n_runs": 40})[1]
    assert "WilMA bei 0,995 des Zufalls (40 von 40 Siegen), bei 3 Takten bei 0,882" in text and "0,833 gegen 0,738" in text
    single = ev.verdict_swap({"rows": rows[:1], "n_runs": 40})[1]
    assert "Platzwechselzeit ist schon 0" in single and "0,995" in single


def test_lookahead_verdict():
    rows = [{"g": 0, "best": 387.0, "steffen": 412.0, "random": 566.0, "entry": 359}, {"g": 70, "best": 401.0, "steffen": 457.0, "random": 596.0, "entry": 359}]
    text = ev.verdict_lookahead(rows)[1]
    assert "bei 0 % Gruppen 6,1 % schneller" in text and "bei 70 % Gruppen 12,3 %" in text and "noch 11,7 % über der Eintrittsschranke" in text
