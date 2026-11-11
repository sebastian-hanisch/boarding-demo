"""Texte der App, die die README wörtlich enthält (tests/test_claims.py vergleicht sie): Annahmen, Grenzen und bekannte Probleme sowie die Regelbeschreibungen."""

import brd_constants as C

RULE_DESCRIPTIONS = {
    "random": "Fahrgäste steigen in zufälliger Reihenfolge ein. Verteilt die Verstauzeiten über den ganzen Gang, ohne dass jemand gezielt wartet.",
    "b2f5": "Rückwärts in 5 Blöcken: die hinteren Reihen zuerst, innerhalb eines Blocks zufällig. Jeder Block drängt sich in wenigen Reihen.",
    "f2b5": "Vorwärts in 5 Blöcken: die vorderen Reihen zuerst. Negativkontrolle: jeder spätere Block muss durch die Zone der noch Verstauenden gehen.",
    "b2fRows": "Rückwärts reihenweise: Reihe für Reihe von hinten. Aufeinanderfolgende Fahrgäste verstauen nebeneinander im selben Abschnitt des Gangs und blockieren sich.",
    "wilma": "WilMA: erst alle Fensterplätze, dann die Mittelplätze, dann die Gangplätze, innerhalb einer Klasse zufällig. Vermeidet, dass Sitzende für Fensterplätze aufstehen müssen.",
    "steffen": ("Steffen-artig (Rekonstruktion): Fenster vor Mitte vor Gang; innerhalb einer Klasse gerade Reihen von hinten nach vorn, dann ungerade. "
                "Innerhalb einer Klasse und einer Seite sitzen aufeinanderfolgende Fahrgäste zwei Reihen auseinander und können gleichzeitig verstauen (an den Übergängen zwischen Klassen, Seiten und geraden und ungeraden Reihen nicht). Die genaue Folge der Quelle (Steffen 2008) steht nur in einer Abbildung; "
                "diese Fassung folgt dem Prinzip „zwei Reihen Abstand, Fenster vor Mitte vor Gang“."),
}

ASSUMPTIONS_MARKDOWN = """
**Annahmen** (alle Verhaltensparameter sind Annahmen, keine Messungen; ein Takt ist nicht in Sekunden kalibriert)

| Annahme | Wert | Wer setzt an |
|---|---|---|
| Flugzeug | ein Gang, je Reihe 2 Seiten mal 3 Plätze; Reihenzahl wählbar | Regler |
| Schritt im Gang | 1 Takt je Reihe, niemand überholt | Modell, fest |
| Türrate | höchstens ein Fahrgast alle e Takte, nur bei freier erster Zelle | Regler |
| Gepäck | Anteil der Fahrgäste mit Gepäck wählbar; Verstauzeit gleichverteilt ganzzahlig zwischen 3 Takten und der gewählten Obergrenze, ohne Gepäck 0 Takte | Regler und Modell |
| Platzwechsel | je Mitreisendem, der schon zwischen Gang und eigenem Platz sitzt, eine feste Zahl Takte (auch für Fahrgäste ohne Gepäck); der Fahrgast bleibt dabei im Gang | Regler |
| Gruppen | Paare und Dreiergruppen (Dreier: ein Viertel der Gruppen) sitzen nebeneinander und steigen zusammen ein, Fenster zuerst | Regler (Anteil, Form, Aufruf) |
| Ungehorsam | eine ungehorsame Gruppe reiht sich an gleichverteilt zufälliger Stelle in die Schlange ein | Regler |
| Zwei Türen | zwei unabhängige Hälften zu je der halben Reihenzahl, die Zeit ist das Maximum beider | Regler |

**Grenzen:** kein Überholen im Gang, keine Gegenrichtung (Aussteigen), kein Platzmangel im Gepäckfach, keine langsamen Fahrgäste (Kinder, Gehhilfen), kein Vorrang für Statusgruppen,
ein Gang. Gruppen, die getrennt sitzen oder sich im Gang aufteilen, fehlen. Im getesteten Raster (Türrate 1 bis 3, 30 Reihen) bleibt Steffen-artig vor WilMA und WilMA vor Zufall; die Plätze der übrigen Regeln und der Abstand hängen an Türrate, Gepäck, Ungehorsam und Platzwechsel (bei Türrate ab 4 schlägt Rückwärts in 5 Blöcken den Zufall).

**Bekannte Probleme und Unsicherheiten:** Die Steffen-artige Reihenfolge ist eine Rekonstruktion nach dem Prinzip der Quelle, nicht ihre Abbildung. Das Experiment „Voraussicht“ ist ein Annealing
auf acht Instanzen und nicht auf Optimalität bewiesen: es zeigt, dass mindestens so viel möglich ist. Die Regime-Karte und die Experimente rechnen je Zelle mit weniger Läufen als der Vergleich oben; ihre Werte streuen entsprechend mehr.
"""


def assumptions_markdown() -> str:
    return ASSUMPTIONS_MARKDOWN


def rule_table_markdown() -> str:
    """Tabelle der Regeln mit kurzer Beschreibung (für den Expander Methodenvergleich)."""
    lines = ["| Regel | Beschreibung |", "|---|---|"]
    for rule in C.MAIN_RULES:
        lines.append(f"| {C.RULE_NAMES[rule]} | {RULE_DESCRIPTIONS[rule]} |")
    return "\n".join(lines)
