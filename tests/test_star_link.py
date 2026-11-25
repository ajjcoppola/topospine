"""Face-row star absolute (Theorem A) and Link(opp) bounds (Theorem C)."""

from __future__ import annotations

from topospine.cover.grid2d import (
    FILLED,
    HOLLOW,
    ABSENT,
    audit_face_row_theorem_a,
    audit_link_bounds,
    build_grid,
    collapsible_pairs,
    link_out_complex,
    star_collapse_face_rows,
    star_of_free_face,
    to_core,
    free_faces,
)


def test_theorem_a_2x2_and_2x3():
    a22 = audit_face_row_theorem_a(2, 2)
    assert a22["checked"] > 0 and a22["mismatches"] == 0
    a23 = audit_face_row_theorem_a(2, 3)
    assert a23["checked"] > 0 and a23["mismatches"] == 0


def test_theorem_a_single_square():
    cfg = {(0, 0): FILLED, (1, 0): ABSENT, (0, 1): ABSENT, (1, 1): ABSENT}
    g = build_grid(cfg, 2, 2)
    p = next(c for c in g.columns if c.dim == 2)
    f = free_faces(p.cell, [])[0]
    rec = star_collapse_face_rows(g, p, f)
    assert rec["ok"]
    assert rec["opt"] == 1.0
    assert rec["collapsed_plus_one"] == 1.0
    assert rec["st_size"] == len(star_of_free_face(p.cell, f))


def test_link_bounds_3x3():
    out = audit_link_bounds(3, 3)
    assert out["checked"] > 1000
    assert out["violations"] == 0
    assert out["exact_rate"] > 0.9


def test_2x3_ring_link_stitch_exact():
    """Old free-face swap failed here; Link(opp) stitch U equals opt."""
    cfg = {
        (0, 0): HOLLOW,
        (1, 0): HOLLOW,
        (0, 1): FILLED,
        (1, 1): HOLLOW,
        (0, 2): HOLLOW,
        (1, 2): HOLLOW,
    }
    core = to_core(build_grid(cfg, 2, 3))
    assert core is not None
    for p, f in collapsible_pairs(core):
        inst = link_out_complex(core, p, f)
        assert inst.L <= inst.opt <= inst.U
        assert inst.U == inst.opt
        assert inst.exact_stitch
