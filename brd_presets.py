"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import brd_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: object = None
    hi: object = None
    options: tuple | None = None     # Auswahlregler: erlaubte Werte; `lo` und `hi` sind dann der erste und der letzte Eintrag


def _choice(url_param, caster, default, options):
    return SettingSpec(url_param, caster, default, options[0], options[-1], tuple(options))


SETTING_SPECS = {
    "rows_slider": SettingSpec("rows", int, C.DEFAULT_R, C.R_MIN, C.R_MAX),
    "doors_radio": _choice("doors", int, C.DEFAULT_DOORS, C.DOORS),
    "e_slider": SettingSpec("e", int, C.DEFAULT_E, C.E_MIN, C.E_MAX),
    "ell_slider": SettingSpec("ell", int, C.DEFAULT_ELL, C.ELL_MIN, C.ELL_MAX),
    "smax_slider": SettingSpec("smax", int, C.DEFAULT_SMAX, C.SMAX_MIN, C.SMAX_MAX),
    "sh_slider": SettingSpec("sh", int, C.DEFAULT_SH, C.SH_MIN, C.SH_MAX),
    "g_slider": SettingSpec("g", int, C.DEFAULT_G, C.G_MIN, C.G_MAX),
    "gtype_select": _choice("gtype", str, "seite", tuple(C.GROUP_TYPES)),
    "gmode_select": _choice("gmode", str, "min", tuple(C.GROUP_KEYS)),
    "intra_select": _choice("intra", str, "window_first", tuple(C.INTRA_ORDERS)),
    "delta_slider": SettingSpec("delta", int, C.DEFAULT_DELTA, C.DELTA_MIN, C.DELTA_MAX),
    "view_select": _choice("view", str, C.DEFAULT_VIEW_RULE, C.MAIN_RULES),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
# Schlüssel eines Presets (Name im Preset-Wörterbuch) -> Schlüssel im Session State; Werte, die ein Preset nicht nennt, bekommen den Standardwert
PRESET_KEYS = {"e": "e_slider", "ell": "ell_slider", "smax": "smax_slider", "sh": "sh_slider", "g": "g_slider", "delta": "delta_slider", "doors": "doors_radio"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def options(state_key):
    return SETTING_SPECS[state_key].options


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt bzw. nur erlaubte Auswahlwerte."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.options is not None:
                if value not in spec.options:
                    continue
            else:
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def preset_value(name, state_key):
    """Wert eines Reglers unter einem Preset: der genannte oder der Standardwert."""
    preset = C.PRESETS[name]
    key = next((k for k, v in PRESET_KEYS.items() if v == state_key), None)
    spec = SETTING_SPECS[state_key]
    return preset.get(key, spec.default) if key is not None else spec.default


def apply_preset(name):
    """Alle Regler auf das Preset setzen; was das Preset nicht nennt (auch Ansichtsregel und Zufalls-Seed), bekommt seinen Standardwert."""
    for state_key in SETTING_SPECS:
        st.session_state[state_key] = preset_value(name, state_key)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert)
    mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS, dann hebt auch seine Änderung die
    Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    for name in C.PRESETS:
        if all(st.session_state.get(state_key, spec.default) == preset_value(name, state_key) for state_key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
