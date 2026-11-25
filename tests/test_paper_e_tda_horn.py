"""Paper E: Horn covering, spine windows, classic Espresso, ABC-Horn SOP."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "applications" / "medical"))

from topospine.core.cubes import parse_boolean_cube as P
from topospine.cover.espresso_variants import (
    classic_espresso_minimize,
    find_classic_espresso,
)
from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.spines.tower import build_cover_tower, tower_certificate
from topospine.synth.ir import SynthesisState
from topospine.synth.logic_passes import AbcHornSopRefinePass, LogicState
from topospine.synth.passes import (
    FiltrationCompatibleHornPass,
    HornRetractionCollapsePass,
    horn_retraction_closure,
)
from topospine.checkers.pass_trace import verify_pass_trace


def test_horn_covering_nonvacuous_on_2007():
    from pipeline import reduce_2007_horn

    r = reduce_2007_horn()
    assert r["horn_steps"] >= 1
    assert r["max_dim_after"] < r["max_dim_before"]
    assert r["cohomology_preserved"] is True


def test_horn_covering_nonvacuous_on_8cube_blob():
    from pipeline import reduce_volume, synthetic_blob

    r = reduce_volume(synthetic_blob(), (8, 8, 8), mode="covering")
    assert r["horn_steps"] >= 1
    assert r["cells_after"] != r["cells_before"] or r["dim_sum_after"] != r["dim_sum_before"]


def test_filtration_compatible_horn_on_boolean_square():
    from topospine.core.cubical import CubicalComplex
    from topospine.core.cubes import parse_boolean_cube

    c = parse_boolean_cube("--")
    st = SynthesisState(
        complex=CubicalComplex([c], name="sq"),
        grades={str(c): 0.0, **{str(f): 0.0 for f in c.faces()}},
        mode="homotopy",
    )
    # Ensure face grades exist for filtration_compatible_spine
    for f in c.faces():
        st.grades[str(f)] = 0.0
    res = FiltrationCompatibleHornPass().try_apply(st)
    # May accept or reject depending on face-closed birth map; must not crash
    assert res.certificate.get("pass") == "FiltrationCompatibleHorn"


def test_spine_tower_horn_windows():
    import math

    pts = [(math.cos(2 * math.pi * i / 16), math.sin(2 * math.pi * i / 16)) for i in range(16)]
    tower = build_cover_tower(pts, base_scale=1.5, n_levels=2, spine_method="horn", horn_mode="approx")
    cert = tower_certificate(tower)
    assert cert["n_levels"] == 2
    assert "windows" in cert
    assert all(isinstance(w, tuple) and len(w) == 2 for w in cert["windows"])


@pytest.mark.skipif(find_classic_espresso() is None, reason="classic espresso binary missing")
def test_classic_espresso_covers():
    on = [P("00--"), P("11--")]
    r = classic_espresso_minimize(on)
    assert r.meta.get("available")
    assert r.cost == 2
    assert sorted(r.cover_strs) == ["00--", "11--"]


def test_abc_horn_sop_refine_runs():
    st = LogicState.from_minterms(4, {0, 1, 2, 3, 12, 13, 14, 15})
    res = AbcHornSopRefinePass(use_abc_seed=True).try_apply(st)
    assert res.certificate.get("pass") == "AbcHornSopRefine"
    assert "horn_cubes" in res.certificate
    assert "conjecture_e1" in res.certificate
