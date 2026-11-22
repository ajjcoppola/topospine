"""Real Hodge Betti numbers, torsion, pair collapse, and encoding-size counts."""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from topospine.checkers.pass_trace import verify_pass_trace  # noqa: E402
from topospine.core.cohomology import CohomologyF2, sphere2, torus7  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402
from topospine.core.laplacian import (  # noqa: E402
    collapse_simplicial_once,
    cubical_betti_real,
    cubical_boundaries,
    cubical_spectrum,
    delete_one_top,
    free_pair_simplicial,
    pair_collapse_cubical,
    resource_counts,
    rp2,
    simplicial_betti_real,
    simplicial_spectrum,
)
from topospine.synth.ir import SynthesisState  # noqa: E402
from topospine.synth.passes import PairCollapsePass  # noqa: E402


def _pad(a, b):
    n = max(len(a), len(b))
    return a + [0] * (n - len(a)), b + [0] * (n - len(b))


def test_real_betti_matches_f2_on_torsion_free_surfaces_and_differs_on_rp2():
    assert simplicial_betti_real(torus7()) == CohomologyF2(torus7()).betti() == [1, 2, 1]
    assert simplicial_betti_real(sphere2()) == [1, 0, 1]
    real, f2 = simplicial_betti_real(rp2()), CohomologyF2(rp2()).betti()
    assert real == [1, 0, 0]
    assert f2 == [1, 1, 1]
    assert real != f2


def test_boundary_squared_vanishes_on_a_boolean_cube():
    cx = CubicalComplex([parse_boolean_cube("---")])
    bounds = cubical_boundaries(cx)
    for k in range(2, max(bounds) + 1):
        assert np.allclose(bounds[k - 1] @ bounds[k], 0)


def test_pair_collapse_preserves_real_betti_and_random_deletion_does_not():
    disk = [(0, 1, 2)]
    assert free_pair_simplicial(torus7()) is None  # closed surface
    collapsed = collapse_simplicial_once(disk)
    assert collapsed is not None
    assert _pad(simplicial_betti_real(disk), simplicial_betti_real(collapsed))[0] == _pad(
        simplicial_betti_real(disk), simplicial_betti_real(collapsed)
    )[1]

    square = CubicalComplex([parse_boolean_cube("--")])
    before = cubical_spectrum(square)
    stepped = pair_collapse_cubical(square)
    assert stepped is not None
    after = cubical_spectrum(stepped)
    b0, b1 = _pad(before["betti_real"], after["betti_real"])
    assert b0 == b1 == [1, 0, 0]
    assert after["n_cells"] < before["n_cells"]
    # positive spectrum is reported and is not part of the preservation claim
    assert before["spectral_gaps"][0] != after["spectral_gaps"][0]

    cycle = CubicalComplex(
        [parse_boolean_cube("01-"), parse_boolean_cube("0-1"), parse_boolean_cube("-01"),
         parse_boolean_cube("10-"), parse_boolean_cube("1-0"), parse_boolean_cube("-10")],
        name="C6",
    )
    intact = cubical_betti_real(cycle)
    broken = cubical_betti_real(delete_one_top(cycle, 0))
    assert intact != broken


def test_qubit_count_drops_only_for_the_collapse_that_keeps_betti():
    square = CubicalComplex([parse_boolean_cube("--")])
    before = cubical_spectrum(square)
    after = cubical_spectrum(pair_collapse_cubical(square))
    rb, ra = resource_counts(before["n_cells"]), resource_counts(after["n_cells"])
    assert ra["qubits_one_per_cell"] < rb["qubits_one_per_cell"]
    assert ra["dirac_dimension"] == after["n_cells"]
    assert resource_counts(1)["qubits_log_encoding"] == 0
    assert resource_counts(3)["qubits_log_encoding"] == 2


def test_pair_collapse_pass_is_rechecked():
    st = SynthesisState(complex=CubicalComplex([parse_boolean_cube("--")], name="square"))
    res = PairCollapsePass().try_apply(st)
    assert res.accepted
    ok, why = verify_pass_trace(res.certificate, res.state, st)
    assert ok, why
    bad = dict(res.certificate, real_betti_after=[9])
    ok, why = verify_pass_trace(bad, res.state, st)
    assert not ok
