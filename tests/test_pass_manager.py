"""Pass manager + certificate checker tests."""

from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.synth import PassManager, SynthesisState
from topospine.synth.passes import ElementaryCubicalCollapsePass


def test_elementary_collapse_reduces_size():
    cx = coppola_2007_boolean_complex()
    state = SynthesisState(complex=cx)
    before = state.size()
    res = ElementaryCubicalCollapsePass().try_apply(state)
    assert res.accepted
    assert res.state.size() == before - 1
    assert res.certificate["cell"] not in res.state.cell_names()


def test_pass_manager_runs_and_exports():
    cx = coppola_2007_boolean_complex()
    grades = {str(c): float(c.dimension) for c in cx.top_cells}
    state = SynthesisState(complex=cx, grades=grades)
    pm = PassManager.default()
    out = pm.run(state)
    assert out.size() <= state.size()
    exp = pm.export(out)
    assert "log" in exp and exp["size"] == out.size()


def test_relative_blocks_collapse_of_a_cells():
    cx = coppola_2007_boolean_complex()
    # Mark all collapsible outer cells as relative — manager should not strip them via Relative pass preference
    coll = cx.collapsible_cells()
    relative = {str(c) for c, _ in coll}
    state = SynthesisState(complex=cx, relative=relative)
    # Elementary alone should refuse first relative cell
    from topospine.synth.passes import ElementaryCubicalCollapsePass

    res = ElementaryCubicalCollapsePass().try_apply(state)
    assert res.accepted is False


# ---------------------------------------------------------------- Loop 4: modes
import pytest  # noqa: E402

from topospine.checkers.pass_trace import verify_pass_trace  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402


def test_default_manager_is_homotopy_and_empties_2007_core():
    """Documented, intentional: the simple-homotopy view deletes cells (9 -> 0)."""
    st = SynthesisState(complex=coppola_2007_boolean_complex())
    out = PassManager.default().run(st)
    assert out.mode == "homotopy" and out.size() == 0


def test_covering_mode_never_empties_2007_core():
    st = SynthesisState(complex=coppola_2007_boolean_complex())
    out = PassManager.default(mode="covering").run(st)
    assert out.mode == "covering"
    assert out.size() == st.size() == 9
    assert all(e.get("pass") != "ElementaryCubicalCollapse" for e in out.log)


def test_covering_mode_reduces_dimension_on_disjoint_squares():
    cx = CubicalComplex([parse_boolean_cube("--0"), parse_boolean_cube("--1")], name="two squares")
    st = SynthesisState(complex=cx)
    out = PassManager.default(mode="covering").run(st)
    assert out.size() == 2 and out.total_dimension() == 0
    assert st.total_dimension() == 4


def test_deletion_style_pass_blocked_and_rejected_in_covering_mode():
    cx = CubicalComplex([parse_boolean_cube("--")], name="sq")
    cov = SynthesisState(complex=cx, mode="covering")
    assert not ElementaryCubicalCollapsePass().try_apply(cov).accepted
    # forged deletion-style certificate in a covering-mode state is rejected by the checker
    hom = SynthesisState(complex=cx)
    res = ElementaryCubicalCollapsePass().try_apply(hom)
    forged_new = res.state.snapshot()
    forged_new.mode = "covering"
    ok, why = verify_pass_trace(res.certificate, forged_new, cov)
    assert not ok and "deletion-style" in why


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        PassManager.default(mode="bogus")
