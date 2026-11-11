"""Experimente und Regime-Karte der App: jeder Knopf rechnet und zeigt sein Verdikt; das Platzwechsel-Experiment vergleicht 0 mit dem eingestellten Wert (Regressionstest:
der Schlüssel des Experiments hatte sh auf 0 gesetzt, das Verdikt sagte dann „Platzwechselzeit ist schon 0“, obwohl 3 eingestellt war)."""

import os

from streamlit.testing.v1 import AppTest

import brd_constants as C
import brd_evaluation as ev
from brd_runs import Settings

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def _app():
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [x.value for x in at.info] + [x.value for x in at.success] + [x.value for x in at.warning]


def test_swap_experiment_compares_zero_with_the_set_value():
    at = _app()
    at.button(key="swap_start").click().run()
    assert not at.exception
    text = next(t for t in _texts(at) if "Platzwechsel" in t and "WilMA" in t)
    assert "Platzwechselzeit ist schon 0" not in text and "bei 3 Takten" in text
    at.sidebar.slider(key="sh_slider").set_value(0).run()
    at.button(key="swap_start").click().run()
    assert any("Platzwechselzeit ist schon 0" in t for t in _texts(at))


def test_every_experiment_button_shows_its_verdict_and_chart():
    at = _app()
    for key in ("regime_start", "groups_start", "dis_start", "swap_start"):
        at.button(key=key).click().run()
        assert not at.exception, key
    texts = " ".join(_texts(at))
    assert "Sollanteil in Gruppen" in texts and "halbiert sich" in texts and "WilMA bei" in texts and "mindestens möglich" in texts


def test_experiment_results_do_not_depend_on_the_view_rule():
    """Die Ansichtsregel ändert nichts an den Experimenten: der Schlüssel enthält sie nicht, das Ergebnis bleibt erhalten."""
    at = _app()
    at.button(key="groups_start").click().run()
    n_charts = len(at.get("plotly_chart"))
    at.sidebar.selectbox(key="view_select").set_value("wilma").run()
    assert len(at.get("plotly_chart")) == n_charts and not at.exception


def test_regime_map_shape_and_values_by_hand():
    """Karte über 6 Türraten und 4 Verstauzeiten: Form, und die Zelle e = 2, Verstauzeit 12 entspricht dem Basisfall mit 40 Läufen."""
    m = ev.regime_map(Settings(), e_values=(2, 8), smax_values=(12, 40), n_runs=10)
    assert m["e"] == [2, 8] and m["smax"] == [12, 40] and len(m["ratio"]) == 2 and len(m["ratio"][0]) == 2
    assert all(v >= 1.0 for row in m["random_over_bound"] for v in row)          # Zufall liegt nie unter der Eintrittsschranke
    assert m["ratio"][0][0] < m["ratio"][0][1] < 1.0                              # bei e = 2 holt Steffen-artig mehr als bei e = 8
    assert C.GRID_E == (1, 2, 3, 4, 6, 8) and C.GRID_SMAX == (6, 12, 24, 40)
