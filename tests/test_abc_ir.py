"""Loop 3: covering-mode collapse, AIG/factor IR, don't-care spine, ABC adapter."""

from __future__ import annotations

import random

from topospine.checkers.logic_trace import verify_logic_trace
from topospine.checkers.pass_trace import verify_pass_trace
from topospine.core.covering import graded_table_from_cubical
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.core.cubical import CubicalComplex
from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes
from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.synth.aig import AIG, minterm_sop, quick_factor, sop_to_aig
from topospine.synth.ir import SynthesisState
from topospine.synth.logic_passes import (
    AbcBaselineAdapterPass,
    DontCareSpinePass,
    FactorDiagramRewritePass,
    LogicPassManager,
    LogicState,
    parse_abc_and_count,
)
from topospine.synth.passes import (
    CoveringAwareCollapsePass,
    ElementaryCubicalCollapsePass,
    covering_collapse_closure,
)


def cube(s: str) -> BooleanCube:
    return parse_boolean_cube(s)


# ---------------------------------------------------------------- covering mode
def test_covering_collapse_never_empties_single_top():
    st = SynthesisState(complex=CubicalComplex([cube("--")], name="square"))
    # Contrast: the deletion-style elementary pass empties the IR.
    deleted = ElementaryCubicalCollapsePass().try_apply(st)
    assert deleted.accepted and deleted.state.size() == 0
    # Covering mode keeps a column and strictly lowers dimension.
    res = CoveringAwareCollapsePass().try_apply(st)
    assert res.accepted
    ok, why = verify_pass_trace(res.certificate, res.state, st)
    assert ok, why
    assert res.state.size() == 1
    closed = covering_collapse_closure(st)
    assert closed.size() == 1
    assert closed.complex.top_cells[0].dimension == 0
    # decode map goes all the way back to the original top cell
    (face, parent), = closed.meta["decode"].items()
    assert parent == "--" and face == str(closed.complex.top_cells[0])


def test_covering_collapse_fail_closed_on_2007_complex():
    """Every free face of the 2007 core is inadmissible -> no insertion (fail-closed)."""
    cx = coppola_2007_boolean_complex()
    st = SynthesisState(complex=cx)
    cm = graded_table_from_cubical(cx)
    free = list_collapsible_primes(cm)
    assert free, "2007 complex has free faces"
    assert all(not cover_admissible_free_face(cm, j, f) for j, fs in free for f in fs)
    closed = covering_collapse_closure(st)
    assert closed.size() == st.size() > 0
    assert closed.log == []


def test_covering_collapse_preserves_size_on_disjoint_squares():
    st = SynthesisState(complex=CubicalComplex([cube("--0"), cube("--1")], name="two squares"))
    closed = covering_collapse_closure(st)
    assert closed.size() == 2
    assert [c.dimension for c in closed.complex.top_cells] == [0, 0]
    assert len(closed.log) == 4  # each square: 2 -> 1 -> 0
    for entry in closed.log:
        assert entry["pass"] == "CoveringAwareCollapse"
        assert entry["size_before"] == entry["size_after"]


def test_covering_collapse_skips_inadmissible_faces():
    tops = [cube("0--"), cube("-00")]
    st = SynthesisState(complex=CubicalComplex(tops, name="partial-overlap"))
    cm = graded_table_from_cubical(st.complex)
    j = next(j for j, c in enumerate(cm.col_cubes) if str(c) == "0--")
    assert not cover_admissible_free_face(cm, j, cube("00-"))
    assert any(str(f) == "00-" for jj, fs in list_collapsible_primes(cm) if jj == j for f in fs)
    res = CoveringAwareCollapsePass().try_apply(st)
    assert res.accepted
    if res.certificate["cell"] == "0--":
        assert res.certificate["inserted_face"] != "00-"


def test_covering_collapse_respects_relative_subcomplex():
    st = SynthesisState(complex=CubicalComplex([cube("--")], name="sq"), relative={"--"})
    assert not CoveringAwareCollapsePass().try_apply(st).accepted


def test_checker_rejects_emptied_covering_ir():
    st = SynthesisState(complex=CubicalComplex([cube("--")], name="sq"))
    res = CoveringAwareCollapsePass().try_apply(st)
    emptied = res.state.snapshot()
    emptied.complex = CubicalComplex([], name="sq")
    cert = dict(res.certificate, size_after=0)
    ok, why = verify_pass_trace(cert, emptied, st)
    assert not ok and "emptied" in why


# ---------------------------------------------------------------- AIG
def test_aig_strash_and_constants():
    a = AIG(3)
    x, y = a.input_lit(0), a.input_lit(1)
    g1 = a.and_(x, y)
    assert a.and_(y, x) == g1
    assert a.and_(x, x ^ 1) == 0
    assert a.and_(x, 1) == x and a.and_(x, 0) == 0
    assert len(a.ands) == 1


def test_aig_truth_table_matches_direct_evaluation():
    rng = random.Random(7)
    for _ in range(20):
        n = 4
        on = {m for m in range(1 << n) if rng.random() < 0.4}
        aig, out = sop_to_aig(n, minterm_sop(n, on))
        tt = aig.truth_table(out)
        for m in range(1 << n):
            assign = [(m >> (n - 1 - i)) & 1 for i in range(n)]
            assert aig.evaluate(out, assign) == ((tt >> m) & 1) == (1 if m in on else 0)


def test_quick_factor_is_equivalent_and_not_larger():
    # ab + ac + ad  ->  a(b + c + d)
    cubes = [cube("11--"), cube("1-1-"), cube("1--1")]
    plain_aig, plain_out = sop_to_aig(4, cubes)
    from topospine.synth.aig import expr_to_aig

    f_aig = AIG(4)
    out = expr_to_aig(f_aig, quick_factor(cubes))
    assert f_aig.truth_table(out) == plain_aig.truth_table(plain_out)
    assert f_aig.gate_count([out]) < plain_aig.gate_count([plain_out])


def test_blif_export_mentions_inputs_and_output():
    aig, out = sop_to_aig(3, [cube("1-0"), cube("-11")])
    blif = aig.to_blif(out)
    assert ".inputs x0 x1 x2" in blif and ".outputs f" in blif and blif.strip().endswith(".end")


# ---------------------------------------------------------------- don't-care spine
def test_dont_care_spine_single_cube():
    st = LogicState.from_minterms(3, {1, 3, 5, 7})
    res = DontCareSpinePass().try_apply(st)
    assert res.accepted
    assert [str(c) for c in res.state.cubes] == ["--1"]
    ok, why = verify_logic_trace(res.certificate, res.state)
    assert ok, why
    assert res.certificate["optimality"] == "ProvenMinimum"


def test_dont_cares_strictly_help_on_kmap_example():
    on, dc = {4, 8, 10, 11, 12, 15}, {9, 14}
    without = DontCareSpinePass().try_apply(LogicState.from_minterms(4, on)).state
    with_dc = DontCareSpinePass().try_apply(LogicState.from_minterms(4, on, dc)).state
    assert len(with_dc.cubes) <= len(without.cubes)
    assert with_dc.literals() < without.literals()
    ok, why = verify_logic_trace(with_dc.log[-1], with_dc)
    assert ok, why


def test_random_functions_certified_end_to_end():
    rng = random.Random(11)
    for _ in range(12):
        n = 4
        on = {m for m in range(1 << n) if rng.random() < 0.35}
        dc = {m for m in range(1 << n) if m not in on and rng.random() < 0.2}
        if not on:
            continue
        st = LogicState.from_minterms(n, on, dc)
        out = LogicPassManager().run(st)
        for entry in out.log:
            if entry.get("rolled_back"):
                raise AssertionError(entry)
        assert len(out.cubes) <= len(on)
        ok, why = verify_logic_trace(out.log[-2] if len(out.log) >= 2 else out.log[-1], out)
        assert ok, why


def test_checker_rejects_tampered_aig():
    st = LogicState.from_minterms(3, {1, 3, 5, 7})
    res = DontCareSpinePass().try_apply(st)
    bad = res.state.snapshot()
    bad.aig, bad.out = sop_to_aig(3, [cube("--0")])  # wrong function
    ok, why = verify_logic_trace(res.certificate, bad)
    assert not ok


def test_factor_pass_never_grows_gates():
    st = LogicState.from_minterms(4, {7, 11, 13, 14, 15, 3, 5, 6, 9, 10, 12})
    spine = DontCareSpinePass().try_apply(st).state
    fac = FactorDiagramRewritePass().try_apply(spine)
    if fac.accepted:
        assert fac.state.gates() <= spine.gates()
        ok, why = verify_logic_trace(fac.certificate, fac.state)
        assert ok, why


# ---------------------------------------------------------------- ABC adapter
def test_abc_adapter_noop_without_binary(monkeypatch):
    import topospine.synth.logic_passes as lp

    monkeypatch.setattr(lp.shutil, "which", lambda _name: None)  # neither abc nor yosys-abc
    st = LogicState.from_minterms(3, {1, 3})
    res = AbcBaselineAdapterPass().try_apply(st)
    assert not res.accepted
    assert res.certificate["abc_available"] is False
    assert res.certificate["action"] == "baseline_only_no_mutation"
    ok, why = verify_logic_trace(res.certificate, res.state)
    assert ok, why


def test_parse_abc_stats():
    txt = "f : i/o = 4/1 lat = 0 and = 12 lev = 3\nf : i/o = 4/1 lat = 0 and = 9 lev = 3\n"
    assert parse_abc_and_count(txt) == 9


def test_abc_real_binary_when_available():
    """Skipped unless abc / yosys-abc is installed; then ABC must run and return AND counts."""
    import pytest

    from topospine.synth.logic_passes import abc_optimize, find_abc

    if find_abc() is None:
        pytest.skip("abc / yosys-abc not installed")
    st = LogicState.from_minterms(4, {4, 8, 10, 11, 12, 15})
    res = abc_optimize(st.aig, st.out)
    assert res["available"] and res["returncode"] == 0
    assert res["ands_initial"] is not None and res["ands_final"] is not None
    assert res["ands_final"] <= res["ands_initial"]
