#!/usr/bin/env python3
"""Runnable companion for tutorials/01_cyclic_core_and_certificates.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.checkers import verify_cover_optimality_witness, verify_elementary_collapse_trace
from topospine.core.homology import betti_numbers_f2
from topospine.cover.auditor import audit_collapse_branch
from topospine.cover.collapse import expand_collapse_once, list_collapsible_primes
from topospine.cover.minimize import minimize_cover
from topospine.examples.bio import cell_cycle_toy
from topospine.examples.zoo import coppola_2007_graded, filled_triangle_simplices


def main() -> None:
    print("=== Tutorial 01: cyclic cores & certificates ===\n")

    cm = coppola_2007_graded()
    print(f"1. Derived graded T_C: {cm.n_rows()}×{cm.n_cols()} typed={all(r is not None for r in cm.row_cubes)}")

    coll = list_collapsible_primes(cm)
    print(f"2. Collapsible primes: {len(coll)}")
    j, faces = coll[0]
    expanded, p_name, face_name = expand_collapse_once(cm, j, faces[0])
    print(f"   Expanded {p_name} → {face_name}; cols now {expanded.n_cols()}")

    bio = cell_cycle_toy()
    aud = audit_collapse_branch(bio, name="bio_toy", depth_limit=32)
    print("3. Auditor (bio toy):", json.dumps(aud.as_dict(), indent=2))

    cover, cost, _ = minimize_cover(bio.copy(), use_collapse=True)
    wit = {"type": "CoverOptimalityWitness", "decode_cover": cover, "cost": cost}
    print("4. Cover witness:", verify_cover_optimality_witness(bio, wit))

    trace = {
        "type": "ElementaryCollapseTrace",
        "cell": p_name,
        "free_face": str(faces[0]),
        "other_top_cells": [c for i, c in enumerate(cm.cols) if i != j],
        "chi_before": 0,
        "chi_after": 0,
    }
    print("5. Collapse trace:", verify_elementary_collapse_trace(trace))

    b = betti_numbers_f2(filled_triangle_simplices())
    print(f"6. β(Δ²) = {b} (expect β1=0)")
    assert b[1] == 0
    print("\nTutorial 01 OK.")


if __name__ == "__main__":
    main()
