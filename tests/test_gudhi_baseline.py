"""GUDHI Rips agreement and edge-collapse baseline (skipped when gudhi is absent)."""

from __future__ import annotations

import math

import pytest

from topospine.core.cubes import parse_boolean_cube
from topospine.core.cubical import CubicalComplex
from topospine.spines.gudhi_baseline import (
    collapse_graph_edges,
    gudhi_available,
    gudhi_rips_betti,
    rips_edge_collapse,
)
from topospine.spines.relative_tower import rips_betti_f2
from topospine.synth.ir import SynthesisState
from topospine.synth.passes import FlagEdgeCollapseAdapterPass

gudhi = pytest.mark.skipif(not gudhi_available(), reason="gudhi not installed")


@gudhi
def test_gudhi_rips_matches_own_f2_on_a_circle():
    circ = [(math.cos(2 * math.pi * k / 12), math.sin(2 * math.pi * k / 12)) for k in range(12)]
    for radius, expected in ((0.55, [1, 1]), (0.1, [12, 0]), (2.5, [1, 0])):
        own = rips_betti_f2(circ, range(12), radius)
        ext = gudhi_rips_betti(circ, range(12), radius, max_dim=2)
        assert own == expected
        assert ext[:2] == own


@gudhi
def test_edge_collapse_does_not_grow_and_reports_betti():
    circ = [(math.cos(2 * math.pi * k / 12), math.sin(2 * math.pi * k / 12)) for k in range(12)]
    stats = rips_edge_collapse(circ, radius=2.5, iterations=8)
    assert stats["edges_after"] <= stats["edges_before"]
    assert stats["edges_before"] > stats["edges_after"]
    assert len(stats["betti_before"]) == 3
    # dominated complete-ish graph: a triangle's edges collapse
    tri = collapse_graph_edges(3, [(0, 1), (1, 2), (0, 2)], iterations=4)
    assert tri["edges_after"] < tri["edges_before"]


@gudhi
def test_flag_adapter_records_collapse_without_mutating():
    cx = CubicalComplex([parse_boolean_cube("--0"), parse_boolean_cube("--1")], name="two squares")
    st = SynthesisState(complex=cx)
    res = FlagEdgeCollapseAdapterPass().try_apply(st)
    assert res.accepted is False
    assert res.state.size() == st.size()
    cert = res.certificate
    assert cert["gudhi_available"] is True
    assert cert["action"] == "gudhi_edge_collapse_baseline"
    assert cert["edges_before"] > 0
    assert cert["edges_after"] <= cert["edges_before"]
    assert cert["size_before"] == cert["size_after"] == 2
