# ✈️ Flugzeug-Boarding – wann lohnt sich eine Regel?

Fall-Demo im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning), Themenseite
[ÖPNV und Fernverkehr optimieren](https://sebastianhanisch.net/oepnv-fernverkehr-optimierung.html). Erste Demo des Portfolios, die den **Einstieg der Fahrgäste als Reihenfolge-Regel** zeigt
(die Bahn-Demos zeigen die Betreiber-Sicht, [sitzplatz-demo](https://github.com/sebastian-hanisch/sitzplatz-demo) die Platzwahl des Fahrgastes). Vehikel: ein Flugzeug mit einem Gang.

## Kernfrage

Wer sein Gepäck verstaut, hält alle hinter sich im Gang auf. Welche **Boarding-Regel** (zufällig, hinten zuerst, Fenster vor Gang, Steffen-artig) die Zeit senkt, ist keine Eigenschaft der Regel allein:
Der Vorsprung hängt vor allem an der **Türrate** und der **Verstauzeit** (daneben an Gepäckanteil, Platzwechsel und Ungehorsam), und die **Eintrittsschranke** (die Tür lässt nicht schneller ein als ein Fahrgast alle e Takte) begrenzt, was überhaupt zu holen ist.
Die Demo vergleicht alle Regeln auf denselben simulierten Flugzeugen (gemeinsame Zufallszahlen), zeigt den Gang zu einem Zeitpunkt und beantwortet die Frage mit einer Regime-Karte über Türrate und Verstauzeit.
Alle Verhaltensparameter sind Annahmen; ein Takt ist nicht in Sekunden kalibriert.

## Modell

Ein Gang mit den Zellen 1 bis R (Zelle c liegt vor Reihe c), je Reihe zwei Seiten mal drei Plätze (Fenster, Mitte, Gang). Niemand überholt. Ein Fahrgast legt eine Zelle je Takt zurück, wenn die nächste frei ist.
Ein neuer Fahrgast betritt den Gang höchstens alle e Takte und nur bei freier erster Zelle. Am Ziel verweilt er seine Verstauzeit plus eine feste Zahl Takte je Mitreisendem, der zwischen Gang und eigenem Platz
schon sitzt (Platzwechsel); in dieser Zeit blockiert er den Gang. Die Boarding-Zeit T ist der Takt, in dem der letzte sitzt. Bei K Blöcken und R Reihen gehört Reihe r zum Block ⌊(r − 1)·K / R⌋ (Block 0 = vorn); „Rückwärts“ ruft den letzten Block zuerst auf. Bei zwei Türen bedient jede Tür R / 2 Reihen und rechnet mit eigenen Zufallszahlen; die Zeit ist das Maximum beider Hälften. Formeln im Expander **📐 Mathematische Formulierung** der App. Dazu gehört: Beim Durchqueren der Zelle c setzt der Fahrgast L_c auf den Takt, in dem er die nächste Zelle erreicht; anfangs ist A_1(0) = 1 − e und L_c = 0.

Es gibt zwei unabhängig geschriebene Rechenwege desselben Modells: die Taktsimulation (zeigt den Gang zu jedem Takt) und eine Zeit-Gitter-Rekursion (rechnet die Läufe); `tests/test_oracle_boarding.py` prüft, dass beide
dieselbe Zeit und dieselbe Wartezeit je Fahrgast liefern.

## Methodik: die Regeln

| Regel | Beschreibung |
|---|---|
| Zufall | Fahrgäste steigen in zufälliger Reihenfolge ein. Verteilt die Verstauzeiten über den ganzen Gang, ohne dass jemand gezielt wartet. |
| Rückwärts in 5 Blöcken | Rückwärts in 5 Blöcken: die hinteren Reihen zuerst, innerhalb eines Blocks zufällig. Jeder Block drängt sich in wenigen Reihen. |
| Vorwärts in 5 Blöcken | Vorwärts in 5 Blöcken: die vorderen Reihen zuerst. Negativkontrolle: jeder spätere Block muss durch die Zone der noch Verstauenden gehen. |
| Rückwärts reihenweise | Rückwärts reihenweise: Reihe für Reihe von hinten. Aufeinanderfolgende Fahrgäste verstauen nebeneinander im selben Abschnitt des Gangs und blockieren sich. |
| WilMA (Fenster, Mitte, Gang) | WilMA: erst alle Fensterplätze, dann die Mittelplätze, dann die Gangplätze, innerhalb einer Klasse zufällig. Vermeidet, dass Sitzende für Fensterplätze aufstehen müssen. |
| Steffen-artig (Rekonstruktion) | Steffen-artig (Rekonstruktion): Fenster vor Mitte vor Gang; innerhalb einer Klasse gerade Reihen von hinten nach vorn, dann ungerade. Innerhalb einer Klasse und einer Seite sitzen aufeinanderfolgende Fahrgäste zwei Reihen auseinander und können gleichzeitig verstauen (an den Übergängen zwischen Klassen, Seiten und geraden und ungeraden Reihen nicht). Die genaue Folge der Quelle (Steffen 2008) steht nur in einer Abbildung; diese Fassung folgt dem Prinzip „zwei Reihen Abstand, Fenster vor Mitte vor Gang“. |

Zusätzlich: ein **exakter Referenzweg** im Expander „Methodenvergleich“ (Tab „🧮 Exakt“): in einem Mini-Flugzeug (4 Reihen, eine Seite, 8 Fahrgäste) werden alle 8! = 40320 Reihenfolgen durchgerechnet; die beste
Reihenfolge kennt die Verstauzeiten und ist die beste Reihenfolge dieser Instanz (durch Aufzählung bewiesen), keine Regel.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen gelten für den **Basisfall**: 30 Reihen, eine Tür, e = 2, 70 % der Fahrgäste mit Gepäck, Verstauzeit gleichverteilt zwischen 3 und 12 Takten, Platzwechsel 3 Takte, 100 Läufe (Zufalls-Seed 35), alle Regeln auf denselben
Instanzen; wo etwas verändert ist, steht es dabei. Verhältnisse sind Verhältnisse der Mittelwerte über die Läufe (kleiner als 1 = schneller als Zufall); der in der App gezeigte Standardfehler kommt aus der gepaarten Differenz je Instanz (Delta-Methode). Prozentangaben sind aus den ungerundeten Mitteln gerechnet, die Verhältnisse in den Tabellen auf drei Stellen gerundet. Zufallszahlen kommen aus einem ganzzahligen Generator (SplitMix64) mit festem Zufalls-Seed.
Die Tests stehen in `tests/test_claims.py`.

**Basisfall** (`test_base_case_*`): Zufall braucht im Mittel 563 Takte, die Eintrittsschranke ist 359 Takte (1 + 179 · 2). Verhältnis zu Zufall: Steffen-artig 0,738 (416 Takte), WilMA 0,882, Rückwärts in 5 Blöcken 1,228,
Vorwärts in 5 Blöcken 1,447, Rückwärts reihenweise 1,855. Steffen-artig und WilMA schlagen Zufall in 100 von 100 Läufen, die drei anderen Regeln in 0 von 100. Steffen-artig liegt beim 1,158-Fachen, Zufall beim 1,568-Fachen der Eintrittsschranke.

**Türrate** (`test_door_rate_table`; Basisfall, nur e verändert):

| e (Takte zwischen zwei Fahrgästen) | 1 | 2 | 3 | 4 | 6 | 8 |
|---|---|---|---|---|---|---|
| Steffen-artig / Zufall | 0,544 | 0,738 | 0,878 | 0,935 | 0,969 | 0,981 |
| Steffen-artig / Eintrittsschranke | 1,591 | 1,158 | 1,069 | 1,037 | 1,014 | 1,007 |
| Zufall / Eintrittsschranke | 2,927 | 1,568 | 1,217 | 1,110 | 1,046 | 1,026 |
| Rückwärts in 5 Blöcken / Zufall | 1,300 | 1,228 | 1,077 | 0,977 | 0,985 | 0,990 |

Die App nennt den Gang den Engpass, wenn Zufall mindestens 15 % über der Eintrittsschranke liegt, sonst die Tür (Schwelle der Demo, keine Regel; im Basisfall Gang bei e = 1 bis 3, Tür ab e = 4). Die Regime-Karte rechnet die Türraten 1, 2, 3, 4, 6, 8 mal die Verstauzeiten 6, 12, 24, 40 (24 Zellen).

Je langsamer die Tür, desto weniger holt eine Regel: bei e = 8 liegen Steffen-artig und Zufall höchstens 2,6 % über der Schranke. Im Basisfall (70 % Gepäck, Verstauzeit bis 12 Takte) schlägt Zufall Rückwärts in Blöcken, wenn der Gang der Engpass ist (e = 1 bis 3); mit wenig Gepäck gilt das nicht (siehe Raster).
Bei e = 4, 6 und 8 ist Rückwärts in 5 Blöcken im Basisfall um 1,0 bis 2,4 % besser als Zufall (`test_backward_blocks_beat_random_only_with_a_slow_door`).
Über ein Raster von 72 Zellen (e = 1 bis 3, 30 / 70 / 100 % Gepäck, 0 / 30 % Ungehorsam, 0 / 50 % Gruppen, Platzwechsel 3 / 6 Takte, je 40 Läufe) gilt Steffen-artig < WilMA < Zufall in **72 von 72** Zellen, Zufall < Rückwärts in 5 Blöcken in
**61 von 72**; die 11 Ausnahmen haben alle nur 30 % Gepäck bei e = 2 oder 3 (`test_rank_order_grid`).

**Verstauzeit und Gepäck** (`test_longer_stowing_time_*`, `test_baggage_share`): Verstauzeit höchstens 6 / 12 / 24 / 40 Takte: Steffen-artig 0,823 / 0,738 / 0,627 / 0,562, WilMA 0,886 / 0,882 / 0,912 / 0,935. Gepäckanteil 0 / 30 / 70 / 100 %:
Steffen-artig 0,907 / 0,838 / 0,738 / 0,679.

**Woher der Vorsprung kommt** (`test_wilma_lead_comes_from_the_seat_change`): Platzwechsel 0 / 3 / 6 / 10 Takte: WilMA 0,995 / 0,882 / 0,768 / 0,645, Steffen-artig 0,833 / 0,738 / 0,643 / 0,540. Bei Platzwechsel 0 schlägt WilMA Zufall nur in
58 von 100 Läufen (bei 3, 6 und 10 Takten in 100 von 100). WilMA gewinnt in diesem Modell fast nur durch den vermiedenen Platzwechsel; bei Steffen-artig bleibt ohne Platzwechsel ein Vorsprung von 16,7 % durch paralleles Verstauen, der Rest kommt ebenfalls vom vermiedenen Platzwechsel (Deutung aus diesem Vergleich, nicht gesondert gemessen).

**Gruppen** (`test_groups_*`, `test_calling_a_group_*`; Paare und Dreiergruppen, Dreier ein Viertel der Gruppen, nebeneinander in einer Reihenseite, steigen zusammen ein, Fenster zuerst): Sollanteil 0 / 10 / 30 / 50 / 70 %
(tatsächlich 0 / 10,3 / 30,3 / 50,7 / 70,1 %): Steffen-artig 0,738 / 0,743 / 0,755 / 0,768 / 0,781, der Vorsprung gegen Zufall sinkt von 26,2 auf 21,9 %. WilMA 0,882 → 0,923 bei 70 %. Rückwärts reihenweise wird besser (1,855 → 1,656), teils weil die Mitglieder
einer Reihe hintereinander mit Fenster zuerst einsteigen (Deutung; mit „Gang zuerst“ innerhalb der Gruppe ist die Verbesserung kleiner: 1,724). Steigt die Gruppe zum Aufruf ihres spätesten statt ihres frühesten Mitglieds ein, liegt Steffen-artig bei 70 % Gruppen bei 0,753 (Vorsprung 24,7 %); WilMA verliert dabei (0,936).
Die Vermutung „Gruppen zerstören geordnete Reihenfolgen“ bestätigt sich im Basisfall und in diesem Gruppenmodell nicht.

**Ungehorsam** (`test_disobedience_*`; ungehorsame Gruppen reihen sich an gleichverteilt zufälliger Stelle ein): Anteil 0 / 10 / 20 / 30 / 50 / 75 %: Steffen-artig 0,738 / 0,779 / 0,813 / 0,843 / 0,900 / 0,963; der Vorsprung halbiert sich bei etwa 39 %
(lineare Interpolation zwischen den Rasterpunkten 30 und 50 %). Im Basisfall (e = 2) wird Rückwärts in 5 Blöcken dadurch besser: 1,228 / 1,085 / 1,015 / 0,989 bei 0 / 30 / 50 / 75 % (nähert sich dem Zufall); bei e = 4 und e = 8 wird sie nicht besser (0,977 → 0,995 bzw. 0,990 → 0,998 bei 0 → 75 %).

**Zwei Türen** (`test_two_doors`; zwei unabhängige Hälften zu je 15 Reihen, Zeit = Maximum): Zufall 348 Takte statt 563 (Eintrittsschranke: die der größeren Hälfte); Steffen-artig 0,689, WilMA 0,848, Rückwärts reihenweise 1,569 des Zufalls.

**Voraussicht** (`test_lookahead_*`, vorgerechnet in `data/brd_results.json` mit `tools/make_results.py`; 8 Instanzen, 30 Reihen, e = 2, 70 % Gepäck, Platzwechsel 3, Gruppen als beliebige Sitze einer Reihe, 30000 Auswertungen je Lauf, Start von Steffen-artig und von Zufall):
die beste gefundene Reihenfolge, die die Verstauzeiten kennt, braucht 387 / 393 / 402 Takte bei 0 / 30 / 70 % Gruppen gegen 412 / 427 / 457 bei Steffen-artig, also 6,0 / 8,0 / 12,2 % weniger; sie liegt 7,8 / 9,4 / 11,8 % über der Eintrittsschranke von 359 Takten. Die 412 Takte der Steffen-artigen Reihenfolge ohne Gruppen (acht Instanzen) und die 416 des Basisfalls (100 Läufe) stammen aus verschiedenen Stichproben.
So viel ist mindestens möglich; es ist keine Regel, und das wahre Optimum kann tiefer liegen (Annealing auf acht Instanzen, nicht bewiesen optimal).

## Ehrliche Grenzen

* Alle Verhaltensparameter sind **Annahmen**, keine Messungen; ein Takt ist nicht in Sekunden kalibriert. Belastbar sind Verhältnisse zwischen Regeln unter diesen Annahmen, keine Minuten.
* Im getesteten **Raster** (Türrate 1 bis 3, 30 Reihen) bleibt Steffen-artig vor WilMA und WilMA vor Zufall; die Plätze der übrigen Regeln und die **Größe** des Vorsprungs hängen an den Parametern (bei Türrate ab 4 schlägt Rückwärts in 5 Blöcken den Zufall).
* Die **Steffen-artige Reihenfolge** ist eine Rekonstruktion nach dem Prinzip der Quelle („zwei Reihen Abstand, Fenster vor Mitte vor Gang“), nicht die Abbildung der Quelle, die nur als Bild vorliegt. Gerade/ungerade Reihen und die Reihenfolge der Seiten sind unsere Wahl.
* Die Ergebnisse gelten für das hier modellierte Gruppenverhalten (zusammen einsteigen, Fenster zuerst); getrennt sitzende Gruppen und langsame Fahrgäste fehlen.
* Die **Regime-Karte** und die **Experimente** der App rechnen je Zelle mit 40 statt 100 Läufen und streuen deshalb stärker als der Vergleich oben.
* Die gefundene Reihenfolge (Experiment 4) ist ein Annealing auf acht Instanzen und nicht auf Optimalität bewiesen; bewiesen optimal ist nur die beste Reihenfolge im Mini-Flugzeug (alle 8! Reihenfolgen).

## Annahmen, Grenzen und bekannte Probleme

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

## Tests

117 Tests (`pytest tests`, je nach Rechner eine halbe bis zwei Minuten): Einheiten des Kerns an der Mini-Instanz von Hand (`test_algorithm.py`), **Orakel** (`test_oracle_boarding.py`: Taktsimulation gegen Rekursion auf 500 Zufallsinstanzen,
geschlossene Zeiten für einen und zwei Fahrgäste, T = max_k((k − 1)·e + r_k) für k = 1, …, N ohne Verstauzeit und Platzwechsel, Reihe an der Tür von Hand, Aufzählung aller Reihenfolgen, Schranken), Randfälle (`test_edge_cases.py`), Verdikte an handgesetzten Werten
(`test_verdicts.py`), jede Zahl dieser README (`test_claims.py`), Presets, Layout (fester Kopf, Schnellstart, Hervorhebung des aktiven Presets), Footer, AppTest-Rauchtests und die Laufzeit-Importe.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Ergebnis, Gangansicht, Kernfrage mit Regime-Karte, vier Experimente, Expander |
| `brd_scenario.py` | SplitMix64, Sitzplan mit Gruppen, Regeln, Warteschlange |
| `brd_algorithm.py` | Taktsimulation, Zeit-Gitter-Rekursion, Zustand zu einem Takt, untere Schranken |
| `brd_runs.py` | Einstellungen, Läufe über alle Regeln, gepaarter Vergleich |
| `brd_evaluation.py` | Analyse, Regime-Karte, Experimente, Verdikte (reine Funktionen) |
| `brd_exhaustive.py` | exakter Referenzweg im Mini-Flugzeug (alle Reihenfolgen) |
| `brd_results.py`, `data/brd_results.json`, `tools/make_results.py` | vorgerechnete Voraussicht-Messreihe und ihr Erzeuger |
| `brd_visualization.py`, `brd_presets.py`, `brd_constants.py`, `brd_layout.py`, `brd_texts.py`, `brd_format.py` | Figuren, Regler und Permalink, Grenzen und Presets, fester Kopf, Texte, Zahlenformat |

## Bewusst nicht umgesetzt

* **Aussteigen** (Gegenrichtung): eine andere Regel mit eigenem Modell (Gang zuerst oder Fenster zuerst), nicht gemessen.
* **Echte Zeiten**: keine Kalibrierung auf Sekunden, keine Fluglinien-Daten.
* **Exakte Optimierung für 180 Fahrgäste:** die gefundene Reihenfolge ist ein Annealing, ein Optimalitätsbeweis gibt es nur im Mini-Flugzeug.
* **Optimale Gruppen-Reihenfolge nach der Literatur (Bachmat u. a.):** nicht rekonstruiert.
* **PDF-Export:** die Demo zeigt Verfahren und Messungen, keine Planungsunterlage.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Streamlit Community Cloud: die Python-Version ist dort in den App-Einstellungen gewählt; lokal läuft die Demo mit Python 3.14, die CI mit 3.12. <!-- lint-ok: dezimalpunkt -->

## Literatur

* Steffen, J. H. (2008). *Optimal boarding method for airline passengers.* Journal of Air Transport Management 14(3), 146–150 (arXiv 0802.0733). Die arXiv-Fassung (v2, HTML) wurde gelesen: Prinzip „zwei Reihen Abstand, Fenster vor Mitte vor Gang“; die Folge steht nur in einer Abbildung.
* Bachmat, E., Berend, D., Sapir, L., Skiena, S., Stolyarov, N. (2006). *Analysis of airplane boarding via space-time geometry and random matrix theory.* Journal of Physics A 39 (Abstract gelesen).
* Bachmat, E., Berend, D., Sapir, L., Skiena, S., Stolyarov, N. (2009). *Analysis of airplane boarding times.* Operations Research 57(2), 499–513 (Titel und Seiten aus der Suche, nicht gelesen).
* Bachmat, E., Elkin, M. (2008). *Bounds on the performance of back-to-front airplane boarding policies.* Operations Research Letters 36(5), 597–601 (Abstract gelesen).
* Steffen, J. H., Hotchkiss, J. (2012). *Experimental test of airplane boarding methods.* Journal of Air Transport Management 18(1), 64–67 (Abstract gelesen).
* Jaehn, F., Neumann, S. (2015). *Airplane boarding.* European Journal of Operational Research 244(2), 339–359 (Abstract gelesen).

Gebaut mit Streamlit und Plotly.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [ÖPNV und Fernverkehr optimieren](https://sebastianhanisch.net/oepnv-fernverkehr-optimierung.html).
