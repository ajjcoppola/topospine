"""Loop 4: PLA/BLIF readers, literal objectives, real-ABC c17 sanity."""

from __future__ import annotations

from pathlib import Path

import pytest

from topospine.checkers.logic_trace import verify_logic_trace
from topospine.formats import read_blif, read_pla, spec_to_states
from topospine.synth.logic_passes import (
    DontCareSpinePass,
    LogicPassManager,
    LogicState,
    abc_optimize_blif_text,
    find_abc,
)

DATA = Path(__file__).resolve().parents[1] / "examples" / "data"


def test_blif_roundtrip_with_aig_export():
    st = LogicState.from_minterms(4, {1, 2, 4, 7, 8, 11, 13, 14})
    spec = read_blif(st.aig.to_blif(st.out))
    assert spec.n == 4 and spec.on["f"] == set(st.on)


def test_c17_truth_tables_match_nand_semantics():
    spec = read_blif((DATA / "c17.blif").read_text())
    assert spec.n == 5 and spec.gate_count_reference == 6
    nand = lambda a, b: 1 - (a & b)  # noqa: E731
    for m in range(32):
        n1, n2, n3, n6, n7 = [(m >> (4 - i)) & 1 for i in range(5)]
        n10, n11 = nand(n1, n3), nand(n3, n6)
        n16, n19 = nand(n2, n11), nand(n11, n7)
        assert (m in spec.on["N22"]) == bool(nand(n10, n16))
        assert (m in spec.on["N23"]) == bool(nand(n16, n19))


def test_c17_resynthesis_is_certified():
    spec = read_blif((DATA / "c17.blif").read_text())
    for name, st in spec_to_states(spec).items():
        out = LogicPassManager().run(st)
        spine = next(e for e in out.log if e.get("pass") == "DontCareSpine")
        assert spine["optimality"] == "ProvenMinimum"
        ok, why = verify_logic_trace(out.log[-2], out)
        assert ok, why


def test_pla_fd_semantics():
    spec = read_pla((DATA / "demo.pla").read_text())
    assert spec.inputs == ["a", "b", "c", "d"] and spec.outputs == ["f", "g"]
    assert spec.on["f"] == {3, 7, 8, 12, 15} and spec.dc["f"] == {10}
    assert spec.on["g"] == {5, 7, 10, 15} and spec.dc["g"] == {3}
    st = spec_to_states(spec)["f"]
    res = DontCareSpinePass().try_apply(st)
    ok, why = verify_logic_trace(res.certificate, res.state)
    assert ok, why


def test_readers_enforce_caps():
    with pytest.raises(ValueError):
        read_pla(".i 12\n.o 1\n.e\n")
    with pytest.raises(ValueError):
        read_blif(".model m\n.inputs " + " ".join(f"x{i}" for i in range(12)) + "\n.outputs f\n.end\n")


def test_objectives_are_ordered_and_audited():
    on, dc = {4, 8, 10, 11, 12, 15}, {9, 14}
    res = {}
    for obj in DontCareSpinePass.OBJECTIVES:
        st = LogicState.from_minterms(4, on, dc)
        r = DontCareSpinePass(objective=obj).try_apply(st)
        ok, why = verify_logic_trace(r.certificate, r.state)
        assert ok, why
        assert r.certificate["optimality"] == "ProvenMinimum"
        res[obj] = (len(r.state.cubes), r.state.literals())
    assert res["literals"][1] <= res["cubes"][1]
    assert res["cubes"][0] <= res["literals"][0]
    assert res["cubes_then_literals"][0] == res["cubes"][0]
    assert res["cubes_then_literals"][1] <= res["cubes"][1]


def test_bad_objective_rejected():
    with pytest.raises(ValueError):
        DontCareSpinePass(objective="bogus")


@pytest.mark.skipif(find_abc() is None, reason="abc / yosys-abc not installed")
def test_abc_on_c17_does_not_grow():
    r = abc_optimize_blif_text((DATA / "c17.blif").read_text())
    assert r["returncode"] == 0 and r["ands_final"] <= r["ands_initial"]


def test_literal_objective_strictly_beats_cube_objective_on_known_5var_case():
    on = {0, 1, 3, 5, 6, 8, 10, 15, 18, 21, 22, 31}
    dc = {26, 11, 20, 14}
    c = DontCareSpinePass(objective="cubes").try_apply(LogicState.from_minterms(5, on, dc)).state
    lit = DontCareSpinePass(objective="literals").try_apply(LogicState.from_minterms(5, on, dc)).state
    both = DontCareSpinePass(objective="cubes_then_literals").try_apply(LogicState.from_minterms(5, on, dc)).state
    assert (len(c.cubes), c.literals()) == (7, 28)
    assert (len(lit.cubes), lit.literals()) == (7, 27)
    assert (len(both.cubes), both.literals()) == (7, 27)
