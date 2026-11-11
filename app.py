"""Flugzeug-Boarding – wann lohnt sich eine Regel? - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Vergleicht Boarding-Regeln auf denselben simulierten Flugzeugen (gemeinsame Zufallszahlen) und fragt, wann sich eine Regel lohnt: der Vorsprung hängt an der Türrate und
der Verstauzeit, und die Eintrittsschranke begrenzt, was zu holen ist. Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import brd_algorithm as A
import brd_constants as C
import brd_exhaustive as X
import brd_evaluation as ev
import brd_texts as T
import brd_visualization as V
from brd_format import de
from brd_layout import dunkles_design, kopf_css
from brd_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    options,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from brd_results import load_results, lookahead_rows
from brd_runs import Settings, build_instances, run_seeds
from brd_scenario import make_order

st.set_page_config(page_title="Flugzeug-Boarding – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _regime(settings):
    return ev.regime_map(settings)


@st.cache_data(show_spinner=False)
def _groups(settings):
    return ev.experiment_groups(settings)


@st.cache_data(show_spinner=False)
def _disobedience(settings):
    return ev.experiment_disobedience(settings)


@st.cache_data(show_spinner=False)
def _swap(settings):
    return ev.experiment_swap(settings)


@st.cache_data(show_spinner=False)
def _exact(seed, ell, smax, e, sh):
    row, side, pos, stow = X.mini_instance(seed, ell / 100.0, smax)
    return X.enumerate_all(row, side, pos, stow, e, sh)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in brd_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("✈️ Flugzeug-Boarding – wann lohnt sich eine Regel?")
st.markdown(
    """
Wer sein Gepäck verstaut, hält alle hinter sich im Gang auf. Diese Demo vergleicht **Boarding-Regeln** (zufällig, hinten zuerst, Fenster vor Gang, Steffen-artig) auf denselben
simulierten Flugzeugen und fragt, **wann sich eine Regel überhaupt lohnt**: Der Vorsprung hängt vor allem an der **Türrate** und der **Verstauzeit** (daneben an Gepäckanteil, Platzwechsel und Ungehorsam), und die **Eintrittsschranke**
(die Tür lässt nicht schneller ein) begrenzt, was zu holen ist. Alle Verhaltensparameter sind Annahmen, ein Takt ist keine Sekunde: belastbar sind Verhältnisse zwischen Regeln unter diesen Annahmen.

Kurz und ohne Formeln erklärt der Expander **💬 In einfachen Worten** gleich darunter, worum es geht. Weiter unten: die **Kernfrage**, vier **🔬 Experimente** und die Expander **🔧 Wie wir das erreichen – vollständiger Methodenvergleich**, **📐 Mathematische Formulierung**
und **🚧 Wo die Annahmen enden**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/boarding-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Im Flugzeug gehen alle Fahrgäste durch eine Tür und einen schmalen Gang zu ihren Plätzen. Wer sein Gepäck verstaut, hält alle hinter sich auf. Das Programm vergleicht Reihenfolgen, in denen die Fahrgäste einsteigen: zufällig, die hinteren Reihen zuerst, Fenster vor Gang und eine Reihenfolge nach dem Prinzip „zwei Reihen Abstand“. Gerechnet wird auf denselben simulierten Flugzeugen, damit der Vergleich fair ist. Es zeigt, wie viel eine Reihenfolge bringt. Das hängt davon ab, wie schnell die Tür einlässt und wie lange das Verstauen dauert, denn die Tür setzt eine Untergrenze für die Zeit. Alle Verhaltensannahmen sind gesetzt und nicht an echten Flügen gemessen, ein Takt ist keine Sekunde: Die Aussagen gelten im Modell.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/boarding-erklaert.html)
        """
    )
# erklaerseite:einfach:end

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Flugzeug und Tür**")
    rows = st.slider("Reihen", *bounds("rows_slider"), step=C.R_STEP, key="rows_slider", help="Reihen zu je 2 Seiten mal 3 Plätzen.")
    doors = st.radio("Türen", options("doors_radio"), key="doors_radio", horizontal=True, format_func=lambda d: "eine Tür" if d == 1 else "zwei Türen",
                     help="Zwei Türen: zwei unabhängige Hälften zu je der halben Reihenzahl; die Zeit ist das Maximum.")
    e = st.slider("Türrate e (Takte zwischen zwei Fahrgästen)", *bounds("e_slider"), key="e_slider",
                  help="Höchstens ein Fahrgast alle e Takte betritt den Gang. Kleines e = schnelle Tür, der Gang ist der Engpass; großes e = langsame Tür.")
    st.markdown("**Fahrgäste**")
    ell = st.slider("Anteil mit Gepäck (%)", *bounds("ell_slider"), key="ell_slider", help="Nur wer Gepäck hat, verstaut; wer andere hineinlassen muss, verweilt wegen des Platzwechsels länger.")
    smax = st.slider("Verstauzeit höchstens (Takte)", *bounds("smax_slider"), key="smax_slider",
                     help="Die Verstauzeit ist gleichverteilt ganzzahlig zwischen 3 Takten und diesem Wert.")
    sh = st.slider("Platzwechsel je Mitreisendem (Takte)", *bounds("sh_slider"), key="sh_slider",
                   help="Zeit, die ein Fahrgast im Gang verliert, weil ein Mitreisender zwischen Gang und seinem Platz schon sitzt.")
    st.markdown("**Gruppen und Ungehorsam**")
    g = st.slider("Anteil in Gruppen (%)", *bounds("g_slider"), key="g_slider", help="Sollanteil der Fahrgäste in Paaren und Dreiergruppen; der tatsächliche Anteil weicht etwas ab.")
    no_groups = g == 0
    gtype = st.selectbox("Gruppenform", options("gtype_select"), key="gtype_select", format_func=C.GROUP_TYPES.get, disabled=no_groups,
                         help="Wirkt nur mit Gruppen (Anteil größer als 0).")
    gmode = st.selectbox("Aufruf der Gruppe zum …", options("gmode_select"), key="gmode_select", format_func=C.GROUP_KEYS.get, disabled=no_groups,
                         help="Wirkt nur mit Gruppen: Die Gruppe steigt zum Aufruf ihres frühesten oder spätesten Mitglieds ein.")
    intra = st.selectbox("Innerhalb der Gruppe", options("intra_select"), key="intra_select", format_func=C.INTRA_ORDERS.get, disabled=no_groups,
                         help="Wirkt nur mit Gruppen: Reihenfolge der Mitglieder beim Einsteigen.")
    delta = st.slider("Anteil ungehorsamer Gruppen (%)", *bounds("delta_slider"), key="delta_slider",
                      help="Eine ungehorsame Gruppe (ohne Gruppen: ein einzelner Fahrgast) reiht sich an zufälliger Stelle in die Schlange ein.")
    st.markdown("**Ansicht**")
    view = st.selectbox("Regel in der Gangansicht", options("view_select"), key="view_select", format_func=C.RULE_NAMES.get,
                        help="Welche Regel die Gangansicht und die Wartezeit je Sitz zeigen.")
    seed = st.number_input("Zufalls-Seed der Läufe", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Läufe generieren", width="stretch", on_click=randomize_seed)

sync_query_params({k: st.session_state[k] for k in SETTING_SPECS})

settings = Settings(rows=int(rows), doors=int(doors), e=int(e), ell=int(ell), smax=int(smax), sh=int(sh), g=int(g), gtype=gtype, gmode=gmode, intra=intra,
                    delta=int(delta), view=view, seed=int(seed))
a = _analysis(settings)
shown = a.row(settings.view)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Mittel über {a.n_runs} Läufe auf denselben Instanzen für alle Regeln; angezeigt: **{C.RULE_NAMES[settings.view]}**. Ein Takt entspricht einer Reihe im Gang.")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
if settings.view == "random":
    m1.metric("Boarding-Zeit (Takte)", f"{shown['T']:.0f}", delta="Referenz", delta_color="off")
else:
    m1.metric("Boarding-Zeit (Takte)", f"{shown['T']:.0f}", delta=f"{shown['T'] - a.row('random')['T']:+.0f} Takte gegen Zufall", delta_color="inverse")
m2.metric("Verhältnis zu Zufall", de(shown['ratio'], 3), delta=f"± {de(shown['se'], 3)} Standardfehler", delta_color="off")
m3.metric("Abstand zur Eintrittsschranke", de(shown['over_bound'], 3), delta=f"Schranke {de(a.entry, 0)} Takte", delta_color="off")
m4.metric("Wartezeit je Fahrgast (Takte)", de(shown['wait'], 1), delta="im Gang stehen geblieben", delta_color="off")
st.plotly_chart(V.build_bars(a), width="stretch", key="bars_chart")
st.dataframe(
    [{"Regel": C.RULE_NAMES[r["rule"]], "Boarding-Zeit": r["T"], "Verhältnis zu Zufall": r["ratio"], "Standardfehler": r["se"], "Siege gegen Zufall": r["wins"],
      "Wartezeit je Fahrgast": r["wait"], "Zeit / Schranke": r["over_bound"]} for r in a.rows],
    hide_index=True, width="stretch",
    column_config={
        "Boarding-Zeit": st.column_config.NumberColumn(format="%.0f", help="Mittel in Takten"),
        "Verhältnis zu Zufall": st.column_config.NumberColumn(format="%.3f", help="Verhältnis der Mittelwerte; unter 1 ist schneller als Zufall"),
        "Standardfehler": st.column_config.NumberColumn(format="%.3f", help="aus der gepaarten Differenz je Instanz"),
        "Siege gegen Zufall": st.column_config.NumberColumn(format="%d", help=f"von {a.n_runs} Läufen"),
        "Wartezeit je Fahrgast": st.column_config.NumberColumn(format="%.1f", help="Takte, die ein Fahrgast im Gang stehen bleiben musste"),
        "Zeit / Schranke": st.column_config.NumberColumn(format="%.3f", help="1 = nicht mehr zu holen"),
    },
)

# --- Gangansicht ---------------------------------------------------------------------------------------------------------------------------

st.markdown("### 🧭 Der Gang zu einem Zeitpunkt")
view_seed = run_seeds(settings, 1)[0]
inst = build_instances(settings, view_seed)[0]
order = make_order(inst, settings.view, intra=settings.intra, gmode=settings.gmode)
total, waits = A.recursion(order, inst.row, inst.side, inst.pos, inst.stow, inst.R, e=settings.e, sh=settings.sh)
pct = st.slider("Zeitpunkt (in % der Boarding-Zeit dieses Laufs)", 0, 100, 40, 5, key="t_pct")
t_now = round(total * pct / 100)
occupants, seated, working = A.tick_state(order, inst.row, inst.side, inst.pos, inst.stow, inst.R, e=settings.e, sh=settings.sh, t_stop=t_now)
st.plotly_chart(V.build_plane(inst, occupants, seated, working, t_now, total), width="stretch", key="plane_chart")
st.plotly_chart(V.build_wait_map(inst, order, waits), width="stretch", key="wait_chart")
note = " Bei zwei Türen zeigt die Ansicht die vordere Hälfte (Tür 1)." if settings.doors == 2 else ""
st.caption(f"Ein einzelner Lauf (Zufalls-Seed {view_seed}), Regel „{C.RULE_NAMES[settings.view]}“: rote Kreise laufen, gelbe Rauten verstauen Gepäck oder wechseln den Platz und blockieren den Gang; "
           f"die Wartezeit je Sitz zeigt, wie lange der Fahrgast stehen blieb.{note}")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wann lohnt sich eine Boarding-Regel?")
kind, text = ev.verdict_regime(a)
getattr(st, kind)(text)
regime_key = replace(settings, e=0, smax=0, view=C.DEFAULT_VIEW_RULE)       # das Ergebnis hängt nicht von der Ansichtsregel ab; e und smax überschreibt die Karte
st.markdown(
    "**Regime-Karte:** Verhältnis der Steffen-artigen Reihenfolge zu Zufall und ihr Abstand zur Eintrittsschranke über die Türrate und die längste Verstauzeit "
    f"(je Zelle {C.N_RUNS_GRID} Läufe, alle übrigen Regler wie eingestellt; Türrate und Verstauzeit der Regler werden überschrieben)."
)
if st.button("Regime-Karte berechnen", key="regime_start"):
    st.session_state["regime_done"] = regime_key
if st.session_state.get("regime_done") == regime_key:
    with st.spinner("Rechne die Regime-Karte (24 Zellen, einige Sekunden)..."):
        regime = _regime(regime_key)
    fig_ratio, fig_bound = V.build_regime_heatmaps(regime)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_ratio, width="stretch", key="regime_ratio")
    c2.plotly_chart(fig_bound, width="stretch", key="regime_bound")
    st.caption("Links: unter 1 ist schneller als Zufall. Rechts: 1 bedeutet, dass die Zeit an der Eintrittsschranke liegt; je größer, desto weiter ist sie davon entfernt (ob die Schranke erreichbar ist, zeigt Experiment 4: die beste gefundene Reihenfolge bleibt darüber).")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.markdown("---")
st.subheader("🔬 Experiment 1: Gruppen kosten im Basisfall wenig")
st.markdown("Wie viel nimmt ein wachsender Anteil in Gruppen den Regeln, und hilft es, wenn eine Gruppe zum Aufruf ihres spätesten Mitglieds einsteigt?")
key_groups = replace(settings, g=0, gmode="min", view=C.DEFAULT_VIEW_RULE)    # g und gmode variiert das Experiment selbst
if st.button("Experiment rechnen", key="groups_start"):
    st.session_state["groups_done"] = key_groups
if st.session_state.get("groups_done") == key_groups:
    with st.spinner("Rechne das Experiment..."):
        exp_g = _groups(key_groups)
    xs = [r["g"] for r in exp_g["rows"]]
    series = {C.RULE_SHORT[rule]: ([r[f"{rule}_min"] for r in exp_g["rows"]], C.RULE_COLORS[rule], False) for rule in ("steffen", "wilma", "b2f5")}
    series["Steffen-artig, spätestes Mitglied"] = ([r["steffen_max"] for r in exp_g["rows"]], C.RULE_COLORS["steffen"], True)
    st.plotly_chart(V.build_lines(xs, series, "Sollanteil in Gruppen (%)", f"Verhältnis zu Zufall ({exp_g['n_runs']} Läufe je Zelle)"), width="stretch", key="groups_chart")
    kind, text = ev.verdict_groups(exp_g)
    getattr(st, kind)(text)

st.subheader("🔬 Experiment 2: Ungehorsam")
st.markdown("Wie viel Ungehorsam verträgt eine Reihenfolge, und was geschieht mit Rückwärts in Blöcken?")
key_dis = replace(settings, delta=0, view=C.DEFAULT_VIEW_RULE)                # delta variiert das Experiment selbst
if st.button("Experiment rechnen", key="dis_start"):
    st.session_state["dis_done"] = key_dis
if st.session_state.get("dis_done") == key_dis:
    with st.spinner("Rechne das Experiment..."):
        exp_d = _disobedience(key_dis)
    xs = [r["delta"] for r in exp_d["rows"]]
    series = {C.RULE_SHORT[rule]: ([r[rule] for r in exp_d["rows"]], C.RULE_COLORS[rule], False) for rule in ("steffen", "wilma", "b2f5")}
    st.plotly_chart(V.build_lines(xs, series, "Anteil ungehorsamer Gruppen (%)", f"Verhältnis zu Zufall ({exp_d['n_runs']} Läufe je Zelle)"), width="stretch", key="dis_chart")
    kind, text = ev.verdict_disobedience(exp_d)
    getattr(st, kind)(text)

st.subheader("🔬 Experiment 3: Woher kommt der Vorsprung?")
st.markdown("WilMA vermeidet den Platzwechsel, die Steffen-artige Reihenfolge verstaut parallel. Wird die Platzwechselzeit 0, zeigt sich, welcher Vorsprung woher stammt.")
key_swap = replace(settings, view=C.DEFAULT_VIEW_RULE)                          # das Experiment vergleicht Platzwechsel 0 mit dem eingestellten sh: sh bleibt im Schlüssel
if st.button("Experiment rechnen", key="swap_start"):
    st.session_state["swap_done"] = key_swap
if st.session_state.get("swap_done") == key_swap:
    with st.spinner("Rechne das Experiment..."):
        exp_s = _swap(key_swap)
    st.dataframe(
        [{"Platzwechsel (Takte)": r["sh"], "Steffen-artig / Zufall": r["steffen"], "WilMA / Zufall": r["wilma"], "WilMA-Siege": r["wilma_wins"]} for r in exp_s["rows"]],
        hide_index=True, width="stretch",
        column_config={"Steffen-artig / Zufall": st.column_config.NumberColumn(format="%.3f"), "WilMA / Zufall": st.column_config.NumberColumn(format="%.3f"),
                       "WilMA-Siege": st.column_config.NumberColumn(format="%d", help=f"von {exp_s['n_runs']} Läufen")},
    )
    kind, text = ev.verdict_swap(exp_s)
    getattr(st, kind)(text)

st.subheader("🔬 Experiment 4: Was ist mindestens möglich? (vorgerechnet)")
st.markdown("Eine Reihenfolge, die die Verstauzeiten **kennt**, ist keine Regel, zeigt aber, dass mindestens so viel möglich ist. Sie wurde vorab per Annealing gesucht (zu teuer für die Live-App).")
look = lookahead_rows(load_results())
if look:
    st.plotly_chart(V.build_lookahead(look), width="stretch", key="look_chart")
    kind, text = ev.verdict_lookahead(look)
    getattr(st, kind)(text)
    st.caption(f"Vorgerechnet (`tools/make_results.py`): {look[0]['n_instances']} Instanzen mit 30 Reihen, e = 2, 70 % mit Gepäck, Platzwechsel 3 Takte, "
               "30000 Auswertungen je Lauf, Gruppen als beliebige Sitze einer Reihe; unabhängig von den Reglern oben.")
else:
    st.info("Die vorgerechnete Messreihe (data/brd_results.json) fehlt oder ist nicht lesbar.")

st.markdown("---")

# --- Expander ------------------------------------------------------------------------------------------------------------------------------

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tab_rules, tab_exact = st.tabs(["Regeln im Überblick", "🧮 Exakt (alle Reihenfolgen im Mini-Flugzeug)"])
    with tab_rules:
        st.markdown(T.rule_table_markdown())
        st.caption("Alle Regeln laufen auf denselben Instanzen. Verglichen wird die Boarding-Zeit in Takten, nicht in Sekunden.")
    with tab_exact:
        # Der Tab ist selbstständig: eigener Button, Spinner und Ergebnis, gegen das aktuelle Szenario geprüft (DEMO-PLAYBOOK §2).
        st.markdown("Ein Mini-Flugzeug mit 4 Reihen, einer Seite und 8 Fahrgästen (Fenster- und Gangplatz je Reihe): alle 8! = 40320 Reihenfolgen werden durchgerechnet. "
                    "Türrate, Gepäckanteil, Verstauzeit, Platzwechsel und Zufalls-Seed kommen aus den Reglern.")
        exact_key = (settings.seed, settings.ell, settings.smax, settings.e, settings.sh)
        if st.button("Alle Reihenfolgen durchrechnen", key="exact_start"):
            st.session_state["exact_done"] = exact_key
        if st.session_state.get("exact_done") == exact_key:
            with st.spinner("Rechne 40320 Reihenfolgen..."):
                best = _exact(*exact_key)
            x1, x2, x3 = st.columns(3)
            x1.metric("Beste Reihenfolge (Takte)", f"{best['best']}")
            x2.metric("Steffen-artig (Takte)", f"{best['steffen']}", delta=f"{best['steffen'] - best['best']:+d} gegen die beste", delta_color="inverse")
            x3.metric("Mittel aller Reihenfolgen (Takte)", de(best['mean'], 1))
            st.caption(f"Die Steffen-artige Reihenfolge schlägt {de(100 * best['share_beaten'], 1)} % aller Reihenfolgen; {de(100 * best['share_optimal'], 2)} % aller Reihenfolgen sind optimal. "
                       "Die beste Reihenfolge kennt die Verstauzeiten: sie ist die beste dieser Instanz, keine Regel.")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/boarding-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Warteschlange von $N$ Fahrgästen mit Zielreihe, Platz und Verstauzeit, dazu die Türrate $e$ und die Platzwechselzeit $h$. Gesucht ist die Zeit $T$, zu der der letzte Fahrgast sitzt. Da niemand überholt, hängt jede Ankunftszeit nur von den Vordermännern ab.

| Symbol | Bedeutung |
|---|---|
| $N$ | Zahl der Fahrgäste |
| $k$ | Fahrgast in Reihenfolge $1, \dots, N$ |
| $r_k$ | Zielreihe von $k$ (= Zelle im Gang) |
| $e$ | Takte zwischen zwei Eintritten |
| $s_k$ | Verstauzeit von $k$ |
| $h$ | Platzwechselzeit je Mitreisendem |
| $m_k$ | Zahl der Mitreisenden, die zwischen Gang und Platz von $k$ schon sitzen |
| $A_c(k)$ | Ankunft von $k$ in Zelle $c$ |
| $L_c$ | Zeit, zu der die Zelle $c$ zuletzt frei wurde |
| $E_k$ | Zeit, zu der $k$ fertig ist und sitzt |
| $T$ | Boarding-Zeit: Zeit, zu der der letzte Fahrgast sitzt |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/boarding-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.latex(r"A_1(k) = \max\big(A_1(k-1) + e,\; L_1,\; 1\big)")
    st.latex(r"A_c(k) = \max\big(A_{c-1}(k) + 1,\; L_c\big), \qquad c = 2, \dots, r_k")
    st.latex(r"E_k = A_{r_k}(k) + s_k + h\, m_k, \qquad L_{r_k} \leftarrow E_k")
    st.latex(r"T = \max_k E_k")
    st.markdown("Beim Durchqueren der Zelle $c$ setzt der Fahrgast $L_c$ auf den Takt, in dem er die nächste Zelle erreicht; anfangs ist $A_1(0) = 1 - e$ und $L_c = 0$.")
    st.markdown("**Schranken**, die für jede Reihenfolge gelten (der letzte Fahrgast betritt den Gang frühestens bei $1 + (N-1)e$; die Fahrgäste einer Reihe verstauen nacheinander in derselben Zelle):")
    st.latex(r"T \;\ge\; 1 + (N-1)\,e, \qquad T \;\ge\; \max_r \Big( r + \sum_{k:\, r_k = r} s_k \Big)")
    st.markdown("Die Taktsimulation der Gangansicht und die Rekursion sind zwei unabhängig geschriebene Rechenwege desselben Modells; `tests/test_oracle_boarding.py` prüft, dass sie die gleiche Zeit und die gleiche Wartezeit je Fahrgast liefern.")

with st.expander("🚧 Wo die Annahmen enden"):
    st.markdown(
        "- **Takt statt Sekunde:** Die Zahlen sind Verhältnisse im Modell. Ein Takt ist nicht kalibriert; was eine Regel in Minuten bringt, sagt diese Demo nicht.\n"
        "- **Die Plätze der Regeln hängen an den Parametern:** Im getesteten Raster (Türrate 1 bis 3, 30 Reihen) bleibt Steffen-artig vor WilMA und WilMA vor Zufall; bei Türrate ab 4 schlägt Rückwärts in 5 Blöcken den Zufall, und der Abstand hängt an Türrate, Verstauzeit, Gepäck, Ungehorsam und Platzwechsel (Regler und Regime-Karte).\n"
        "- **Gruppen** sitzen und steigen zusammen ein; ein anderes Gruppenverhalten ist nicht gemessen.\n"
        "- **Aussteigen** (Gegenrichtung), langsame Fahrgäste, volle Gepäckfächer und Statusgruppen fehlen.\n"
        "- **Die Steffen-artige Reihenfolge** ist eine Rekonstruktion nach dem Prinzip „zwei Reihen Abstand, Fenster vor Mitte vor Gang“, nicht die Abbildung der Quelle.\n"
        "- **Die gefundene Reihenfolge** (Experiment 4) ist ein Annealing auf acht Instanzen, nicht auf Optimalität bewiesen."
    )

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.assumptions_markdown())

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Sitzplätze optimieren](https://sebastianhanisch.net/sitzplaetze-optimieren.html)."
)
