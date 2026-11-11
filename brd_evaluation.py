"""Kennzahlen, Regime-Karte, Experimente und Verdikte (die Verdikte sind reine Funktionen: Art und Text, geprüft in tests/test_verdicts.py)."""

from dataclasses import dataclass

import brd_constants as C
from brd_format import de
from brd_runs import Settings, mean, paired_ratio, run_rules, wins

__all__ = ["Settings", "Analysis", "analyse", "regime_map", "experiment_groups", "experiment_disobedience", "experiment_swap",
           "verdict_regime", "verdict_groups", "verdict_disobedience", "verdict_swap", "verdict_lookahead", "regime_label", "half_point"]


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    rows: tuple            # je Regel: dict(rule, T, ratio, se, wins, wait, over_bound)
    entry: float           # mittlere Eintrittsschranke 1 + (N - 1) e (bei zwei Türen die größere Hälfte)
    n_runs: int
    grouped: float         # mittlerer tatsächlicher Anteil in Gruppen

    def row(self, rule: str) -> dict:
        return next(r for r in self.rows if r["rule"] == rule)


def analyse(settings: Settings, n_runs: int = C.N_RUNS) -> Analysis:
    """Alle Hauptregeln auf denselben `n_runs` Instanzen; Verhältnisse gepaart gegen Zufall, Abstand zur Eintrittsschranke."""
    res = run_rules(settings, C.MAIN_RULES, n_runs)
    base = res["T"]["random"]
    entry = mean(res["entry"])
    rows = []
    for rule in C.MAIN_RULES:
        ratio, se = paired_ratio(res["T"][rule], base)
        rows.append({"rule": rule, "T": mean(res["T"][rule]), "ratio": ratio, "se": se, "wins": wins(res["T"][rule], base),
                     "wait": mean(res["wait"][rule]), "over_bound": mean(res["T"][rule]) / entry})
    return Analysis(settings, tuple(rows), entry, n_runs, mean(res["grouped"]))


def _ratio_of(settings: Settings, rule: str, n_runs: int) -> tuple[float, float, float]:
    """(Verhältnis Regel/Zufall, Standardfehler, Regel/Eintrittsschranke) für zwei Regeln auf denselben Instanzen."""
    res = run_rules(settings, ("random", rule), n_runs)
    ratio, se = paired_ratio(res["T"][rule], res["T"]["random"])
    return ratio, se, mean(res["T"][rule]) / mean(res["entry"])


def regime_map(settings: Settings, e_values=C.GRID_E, smax_values=C.GRID_SMAX, n_runs: int = C.N_RUNS_GRID, rule: str = "steffen") -> dict:
    """Regime-Karte: Verhältnis `rule`/Zufall und Abstand zur Eintrittsschranke über Türrate e und längste Verstauzeit (übrige Regler wie `settings`)."""
    ratio, over_bound, random_over_bound = [], [], []
    for smax in smax_values:
        r_row, b_row, z_row = [], [], []
        for e in e_values:
            s = Settings(**{**settings.__dict__, "e": e, "smax": smax})
            res = run_rules(s, ("random", rule), n_runs)
            entry = mean(res["entry"])
            r_row.append(mean(res["T"][rule]) / mean(res["T"]["random"]))
            b_row.append(mean(res["T"][rule]) / entry)
            z_row.append(mean(res["T"]["random"]) / entry)
        ratio.append(r_row)
        over_bound.append(b_row)
        random_over_bound.append(z_row)
    return {"rule": rule, "e": list(e_values), "smax": list(smax_values), "ratio": ratio, "over_bound": over_bound, "random_over_bound": random_over_bound, "n_runs": n_runs}


def experiment_groups(settings: Settings, g_values=C.GRID_G, n_runs: int = C.N_RUNS_GRID) -> dict:
    """Gruppenanteil: Verhältnis Steffen-artig, WilMA und Rückwärts-Blöcke zu Zufall; dazu mit dem Aufruf des frühesten und des spätesten Mitglieds."""
    rows = []
    for g in g_values:
        row = {"g": g}
        for gmode in ("min", "max"):
            s = Settings(**{**settings.__dict__, "g": g, "gmode": gmode})
            res = run_rules(s, ("random", "steffen", "wilma", "b2f5"), n_runs)
            row["grouped_" + gmode] = mean(res["grouped"])
            for rule in ("steffen", "wilma", "b2f5"):
                row[f"{rule}_{gmode}"] = paired_ratio(res["T"][rule], res["T"]["random"])[0]
        rows.append(row)
    return {"rows": rows, "n_runs": n_runs}


def experiment_disobedience(settings: Settings, deltas=C.GRID_DELTA, n_runs: int = C.N_RUNS_GRID) -> dict:
    """Ungehorsam: Verhältnis zu Zufall über den Anteil ungehorsamer Gruppen."""
    rows = []
    for d in deltas:
        s = Settings(**{**settings.__dict__, "delta": d})
        res = run_rules(s, ("random", "steffen", "wilma", "b2f5"), n_runs)
        row = {"delta": d}
        for rule in ("steffen", "wilma", "b2f5"):
            row[rule] = paired_ratio(res["T"][rule], res["T"]["random"])[0]
        rows.append(row)
    return {"rows": rows, "n_runs": n_runs}


def experiment_swap(settings: Settings, n_runs: int = C.N_RUNS_GRID) -> dict:
    """Platzwechselzeit 0 gegen die eingestellte: woher WilMA und Steffen-artig ihren Vorsprung haben."""
    rows = []
    for sh in sorted({0, settings.sh}):
        s = Settings(**{**settings.__dict__, "sh": sh})
        res = run_rules(s, ("random", "steffen", "wilma"), n_runs)
        row = {"sh": sh, "n_runs": n_runs}
        for rule in ("steffen", "wilma"):
            row[rule], _ = paired_ratio(res["T"][rule], res["T"]["random"])
            row[rule + "_wins"] = wins(res["T"][rule], res["T"]["random"])
        rows.append(row)
    return {"rows": rows, "n_runs": n_runs}


# --- Verdikte (rein) ---------------------------------------------------------------------------------------------------------------------

def regime_label(random_over_bound: float) -> str:
    """Wer bremst? Liegt Zufall mindestens 15 % (C.GANG_BOUND) über der Eintrittsschranke, bremst der Gang, sonst die Tür. Die Schwelle ist eine Festlegung dieser Demo, keine Regel."""
    return "Gang" if random_over_bound >= C.GANG_BOUND else "Tür"


def half_point(deltas: list, leads: list) -> float | None:
    """Anteil Ungehorsamer, bei dem der Vorsprung auf die Hälfte seines Werts ohne Ungehorsam fällt (lineare Interpolation zwischen den Rasterpunkten); None, wenn er im Raster nicht fällt."""
    if leads[0] <= 0:
        return None                                  # ohne Ungehorsam gibt es keinen Vorsprung, der sich halbieren könnte
    target = leads[0] / 2.0
    for i in range(1, len(deltas)):
        if leads[i] <= target:                       # erster Rasterpunkt unter der Hälfte; der davor liegt darüber (sonst wäre er der erste)
            span = leads[i - 1] - leads[i]
            return deltas[i - 1] + (deltas[i] - deltas[i - 1]) * (leads[i - 1] - target) / span
    return None


def verdict_regime(a: Analysis) -> tuple[str, str]:
    """Kernfrage: wann lohnt sich eine Regel? Aus der Analyse des eingestellten Szenarios; jede Aussage folgt aus den angezeigten Zahlen."""
    s = a.settings
    best = min(a.rows, key=lambda r: r["T"])
    steffen, rand = a.row("steffen"), a.row("random")
    headroom = 100.0 * (rand["over_bound"] - 1.0)
    brake = (f"Zufall liegt {de(headroom)} % über der Eintrittsschranke von {de(a.entry, 0)} Takten: bei e = {s.e} bremst {regime_label(rand['over_bound'])} "
             f"(Schwelle der Demo: Zufall mindestens {de(100 * (C.GANG_BOUND - 1), 0)} % darüber = Gang).")
    if best["rule"] == "random":
        return "info", f"Hier schlägt keine Regel den Zufall: die beste ist Zufall mit {de(best['T'], 0)} Takten. {brake}"
    gain = 100.0 * (1.0 - best["ratio"])
    if gain < 5.0:
        tail = "Mehr ist nicht zu holen." if headroom < 5.0 else "Die Regeln holen davon kaum etwas."
        return "info", (f"Die beste Regel ({C.RULE_NAMES[best['rule']]}) spart hier nur {de(gain)} % gegen Zufall ({de(best['T'], 0)} gegen {de(rand['T'], 0)} Takte). {brake} {tail}")
    left = 100.0 * (best["over_bound"] - 1.0)
    return "success", (f"Die beste Regel ({C.RULE_NAMES[best['rule']]}) spart **{de(gain)} %** gegen Zufall ({de(best['T'], 0)} gegen {de(rand['T'], 0)} Takte) und liegt noch {de(left)} % über der Eintrittsschranke. "
                       f"{brake} Steffen-artig liegt {de(100.0 * (1.0 - steffen['ratio']))} % unter Zufall.")


def verdict_groups(exp: dict) -> tuple[str, str]:
    """Experiment Gruppen: Vorsprung der Steffen-artigen Reihenfolge ohne und mit dem größten Gruppenanteil, Aufruf nach frühestem gegen spätestem Mitglied."""
    first, last = exp["rows"][0], exp["rows"][-1]
    lead0 = 100.0 * (1.0 - first["steffen_min"])
    lead1 = 100.0 * (1.0 - last["steffen_min"])
    lead1_max = 100.0 * (1.0 - last["steffen_max"])
    return "info", (f"Ohne Gruppen liegt die Steffen-artige Reihenfolge {de(lead0)} % unter Zufall, bei {last['g']} % Sollanteil in Gruppen (tatsächlich {de(100 * last['grouped_min'], 0)} %) "
                    f"noch {de(lead1)} %. Steigt eine Gruppe zum Aufruf ihres spätesten Mitglieds ein, sind es {de(lead1_max)} %.")


def verdict_disobedience(exp: dict) -> tuple[str, str]:
    """Experiment Ungehorsam: Vorsprung der Steffen-artigen Reihenfolge, Halbierungspunkt (interpoliert) und das Verhalten von Rückwärts in 5 Blöcken."""
    rows = exp["rows"]
    deltas = [r["delta"] for r in rows]
    leads = [1.0 - r["steffen"] for r in rows]
    half = half_point(deltas, leads)
    last = rows[-1]
    half_text = f"Der Vorsprung halbiert sich bei etwa {de(half, 0)} % Ungehorsamen." if half is not None else "Der Vorsprung halbiert sich im gemessenen Bereich nicht."
    first_b, last_b = rows[0]["b2f5"], last["b2f5"]
    trend = "wird dadurch besser" if last_b < first_b else "wird dadurch nicht besser"
    return "info", (f"Die Steffen-artige Reihenfolge liegt ohne Ungehorsam {de(100 * leads[0])} % unter Zufall, bei {last['delta']} % ungehorsamen Gruppen {de(100 * leads[-1])} %. {half_text} "
                    f"Rückwärts in 5 Blöcken {trend}: Verhältnis zu Zufall {de(first_b, 3)} gegen {de(last_b, 3)}.")


def verdict_swap(exp: dict) -> tuple[str, str]:
    """Experiment Platzwechsel: Vorsprung von WilMA und Steffen-artig bei Platzwechselzeit 0 gegen die eingestellte."""
    zero = exp["rows"][0]
    if len(exp["rows"]) == 1:
        return "info", (f"Die Platzwechselzeit ist schon 0: WilMA liegt bei {de(zero['wilma'], 3)} des Zufalls ({zero['wilma_wins']} von {exp['n_runs']} Siegen), "
                        f"Steffen-artig bei {de(zero['steffen'], 3)}. Der Vorsprung von WilMA verschwindet, bei Steffen-artig bleibt ein Rest (paralleles Verstauen).")
    other = exp["rows"][-1]
    return "info", (f"Bei Platzwechselzeit 0 liegt WilMA bei {de(zero['wilma'], 3)} des Zufalls ({zero['wilma_wins']} von {exp['n_runs']} Siegen), bei {other['sh']} Takten bei {de(other['wilma'], 3)}; "
                    f"Steffen-artig bei {de(zero['steffen'], 3)} gegen {de(other['steffen'], 3)}. WilMA gewinnt in diesem Modell fast nur durch den vermiedenen Platzwechsel; bei Steffen-artig bleibt ohne Platzwechsel ein Vorsprung durch paralleles Verstauen, der Rest kommt ebenfalls vom vermiedenen Platzwechsel (Deutung, nicht gesondert gemessen).")


def verdict_lookahead(rows: list[dict]) -> tuple[str, str]:
    """Experiment Voraussicht: beste gefundene Reihenfolge (Annealing mit bekannten Verstauzeiten) gegen Steffen-artig und Eintrittsschranke, ohne und mit dem größten Gruppenanteil."""
    first, last = rows[0], rows[-1]
    gap0 = 100.0 * (1.0 - first["best"] / first["steffen"])
    gap1 = 100.0 * (1.0 - last["best"] / last["steffen"])
    over = 100.0 * (last["best"] / last["entry"] - 1.0)
    return "info", (f"Eine Reihenfolge, die die Verstauzeiten kennt, ist bei {first['g']} % Gruppen {de(gap0)} % schneller als die Steffen-artige, bei {last['g']} % Gruppen {de(gap1)} %; "
                    f"sie liegt dann noch {de(over)} % über der Eintrittsschranke. So viel ist mindestens möglich; es ist keine Regel, und das wahre Optimum kann noch tiefer liegen (gefunden per Annealing auf wenigen Instanzen, nicht bewiesen optimal).")
