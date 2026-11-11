"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Alle Verhaltensparameter (Türrate, Gepäckzeit, Platzwechselzeit, Gruppenanteile) sind Annahmen, keine Messungen. Ein Takt ist nicht in Sekunden
kalibriert; belastbar sind nur Verhältnisse zwischen Regeln auf denselben Instanzen unter diesen Annahmen."""

# --- Regler (Grenzen und Standardwerte) ----------------------------------------------------------------------------------------------------
R_MIN, R_MAX, DEFAULT_R = 10, 40, 30            # Reihen (je Reihe 2 Seiten x 3 Plätze); R_STEP 2, damit zwei Türen gleiche Hälften haben
R_STEP = 2
E_MIN, E_MAX, DEFAULT_E = 1, 8, 2               # Takte zwischen zwei Fahrgästen an der Tür (Türrate)
ELL_MIN, ELL_MAX, DEFAULT_ELL = 0, 100, 70      # Anteil der Fahrgäste mit Gepäck in Prozent
SMIN = 3                                        # kürzeste Verstauzeit (Takte), fest
SMAX_MIN, SMAX_MAX, DEFAULT_SMAX = 3, 40, 12    # längste Verstauzeit (Takte), gleichverteilt ganzzahlig in [SMIN, SMAX]
SH_MIN, SH_MAX, DEFAULT_SH = 0, 10, 3           # Platzwechselzeit je Mitreisendem, der zwischen Gang und eigenem Platz schon sitzt (Takte)
G_MIN, G_MAX, DEFAULT_G = 0, 70, 0              # Anteil der Fahrgäste in Gruppen in Prozent (Sollwert; tatsächlich etwas darüber oder darunter)
DELTA_MIN, DELTA_MAX, DEFAULT_DELTA = 0, 90, 0  # Anteil ungehorsamer Gruppen in Prozent
DOORS = (1, 2)
DEFAULT_DOORS = 1
SEED_MAX, DEFAULT_SEED = 999999, 35

GROUP_TYPES = {"seite": "nebeneinander in einer Reihenseite", "reihe": "beliebige Sitze einer Reihe", "nachbar": "über zwei Reihen verteilt"}
GROUP_KEYS = {"min": "frühestes Mitglied", "max": "spätestes Mitglied"}
INTRA_ORDERS = {"window_first": "Fenster zuerst", "aisle_first": "Gang zuerst"}

# --- Regeln ----------------------------------------------------------------------------------------------------------------------------------
MAIN_RULES = ("random", "b2f5", "f2b5", "b2fRows", "wilma", "steffen")
RULE_NAMES = {
    "random": "Zufall",
    "b2f5": "Rückwärts in 5 Blöcken",
    "f2b5": "Vorwärts in 5 Blöcken",
    "b2fRows": "Rückwärts reihenweise",
    "wilma": "WilMA (Fenster, Mitte, Gang)",
    "steffen": "Steffen-artig (Rekonstruktion)",
}
RULE_SHORT = {"random": "Zufall", "b2f5": "Rückw. 5 Blöcke", "f2b5": "Vorw. 5 Blöcke", "b2fRows": "Rückw. reihenweise", "wilma": "WilMA", "steffen": "Steffen-artig"}
RULE_COLORS = {
    "random": "#7f7f7f", "b2f5": "#c0504d", "f2b5": "#e8a09a", "b2fRows": "#8c2d2a", "wilma": "#4c78a8", "steffen": "#2F6B65",
}
DEFAULT_VIEW_RULE = "steffen"
GANG_BOUND = 1.15                               # Zufall mindestens 15 % über der Eintrittsschranke: der Gang bremst, sonst die Tür (Schwelle dieser Demo, keine Regel)

# --- Läufe -----------------------------------------------------------------------------------------------------------------------------------
N_RUNS = 100                                    # Instanzen je Vergleich (gemeinsame Zufallszahlen für alle Regeln)
N_RUNS_GRID = 40                                # Instanzen je Zelle der Regime-Karte und der Experimente (Rechenzeit, Streuung im Band)
SEED_STRIDE = 1000                              # Läufe eines Szenarios: seed * SEED_STRIDE + 0 bis N_RUNS - 1
GRID_E = (1, 2, 3, 4, 6, 8)
GRID_SMAX = (6, 12, 24, 40)
GRID_G = (0, 10, 30, 50, 70)
GRID_DELTA = (0, 10, 20, 30, 50, 75)
MAX_TICKS = 100000                              # Abbruch der Taktsimulation (ein Fehler, keine Rechengrenze)

# --- Anzeige ---------------------------------------------------------------------------------------------------------------------------------
COLOR_SEAT_FREE = "rgba(150,150,150,0.25)"
COLOR_SEAT_TAKEN = "#2F6B65"
COLOR_WALKING = "#c0504d"
COLOR_WORKING = "#e8a63b"
COLOR_LINE = "#4c78a8"
FREE_WAIT = "rgba(150,150,150,0.25)"

PRESETS = {
    "Gang ist der Engpass (Voreinstellung)": {"e": DEFAULT_E, "ell": DEFAULT_ELL, "smax": DEFAULT_SMAX, "sh": DEFAULT_SH, "g": 0, "delta": 0, "doors": 1},
    "Langsame Tür": {"e": 6},
    "Viele Gruppen": {"g": 70},
    "Ungehorsam": {"delta": 30},
    "Lange Verstauzeit": {"smax": 24},
    "Ohne Platzwechsel": {"sh": 0},
    "Zwei Türen": {"doors": 2},
}
PRESET_HELP = {
    "Gang ist der Engpass (Voreinstellung)": "30 Reihen, eine Tür, ein Fahrgast alle 2 Takte, 70 % mit Gepäck: Steffen-artig liegt vorn, Rückwärts reihenweise hinten, und Rückwärts in Blöcken ist langsamer als Zufall.",
    "Langsame Tür": "Ein Fahrgast alle 6 Takte: bei 70 % Gepäck und Verstauzeit bis 12 Takte ist die Tür der Engpass, und die Regel zählt kaum.",
    "Viele Gruppen": "70 % der Fahrgäste reisen in Gruppen (Paare und Dreiergruppen sitzen und steigen zusammen ein).",
    "Ungehorsam": "30 % der Gruppen halten sich nicht an die Reihenfolge und reihen sich an einer zufälligen Stelle ein.",
    "Lange Verstauzeit": "Verstauzeit bis 24 Takte: der Vorsprung der Steffen-artigen Reihenfolge wächst, der von WilMA wird kleiner.",
    "Ohne Platzwechsel": "Platzwechselzeit 0: Negativkontrolle. WilMA verliert hier seinen Vorsprung.",
    "Zwei Türen": "Zwei unabhängige Hälften zu je 15 Reihen, die Zeit ist das Maximum beider Hälften.",
}
