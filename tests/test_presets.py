"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import brd_constants as C
import brd_presets as P
from brd_runs import Settings


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regulator_bounds():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.options is not None:
                assert value in spec.options, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS))
    preset = C.PRESETS[first]
    assert Settings(rows=C.DEFAULT_R, doors=preset["doors"], e=preset["e"], ell=preset["ell"], smax=preset["smax"], sh=preset["sh"], g=preset["g"], delta=preset["delta"]) == Settings()
    for state_key, spec in P.SETTING_SPECS.items():
        assert P.preset_value(first, state_key) == spec.default


def test_unnamed_regulators_take_their_default_value():
    assert P.preset_value("Langsame Tür", "e_slider") == 6
    assert P.preset_value("Langsame Tür", "g_slider") == C.DEFAULT_G and P.preset_value("Langsame Tür", "view_select") == C.DEFAULT_VIEW_RULE


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)     # Adresszeilen-Namen eindeutig


def test_choice_specs_have_first_and_last_option_as_bounds():
    for state_key, spec in P.SETTING_SPECS.items():
        if spec.options is not None:
            assert (spec.lo, spec.hi) == (spec.options[0], spec.options[-1]) and spec.default in spec.options, state_key


def test_regulator_defaults_equal_the_settings_defaults():
    s = Settings()
    d = {k: spec.default for k, spec in P.SETTING_SPECS.items()}
    assert (s.rows, s.doors, s.e, s.ell, s.smax, s.sh, s.g, s.delta, s.view, s.seed) == (
        d["rows_slider"], d["doors_radio"], d["e_slider"], d["ell_slider"], d["smax_slider"], d["sh_slider"], d["g_slider"], d["delta_slider"], d["view_select"], d["seed_input"])
    assert (s.gtype, s.gmode, s.intra) == (d["gtype_select"], d["gmode_select"], d["intra_select"])


def test_rows_regulator_allows_only_even_numbers_of_rows():
    assert C.R_MIN % C.R_STEP == 0 and C.R_MAX % C.R_STEP == 0 and C.DEFAULT_R % C.R_STEP == 0
