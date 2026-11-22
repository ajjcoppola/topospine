#!/usr/bin/env python3
"""Tutorial 06 runner: embedding ablation, GUDHI edge collapse, real Betti numbers."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.core.cohomology import CohomologyF2, sphere2, torus7  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402
from topospine.core.laplacian import (  # noqa: E402
    cubical_spectrum,
    pair_collapse_cubical,
    resource_counts,
    rp2,
    simplicial_betti_real,
)
from topospine.embeddings.clouds import (  # noqa: E402
    indices_with_label,
    suggest_base_scale,
    synthetic_embedding_cloud,
)
from topospine.spines.gudhi_baseline import gudhi_available, rips_edge_collapse  # noqa: E402
from topospine.spines.relative_tower import ablation_report  # noqa: E402
from topospine.synth.ir import SynthesisState  # noqa: E402
from topospine.synth.passes import FlagEdgeCollapseAdapterPass  # noqa: E402


def main() -> None:
    print("=== Tutorial 06: embedding spines and real Laplacians ===\n")
    pts, labels, _ = synthetic_embedding_cloud(n_per=8, n_bridge=3, seed=1)
    A = indices_with_label(labels, 0)
    scale = suggest_base_scale(pts)
    rep = ablation_report(pts, A, scale, n_levels=2)
    rel = rep["methods"]["relative"]["A_cover_radius"]
    kc = rep["methods"]["kcenter_same_budget"]["A_cover_radius"]
    rnd = rep["methods"]["random_same_budget"]["A_cover_radius"]
    print(f"synthetic cloud n={len(pts)} |A|={len(A)} scale={scale:.3f}")
    print(f"  A-radius relative {rel}  k-center {kc}  random {rnd}")
    print(f"  NN recall relative {rep['methods']['relative']['nn_recall_A']}")
    print(f"  own Rips matches GUDHI: {rep['own_rips_matches_gudhi']}")
    assert rep["gudhi_available"] is gudhi_available()

    cx = CubicalComplex([parse_boolean_cube("--0"), parse_boolean_cube("--1")])
    res = FlagEdgeCollapseAdapterPass().try_apply(SynthesisState(complex=cx))
    print(f"\nGUDHI edge collapse on two squares: {res.certificate.get('edges_before')} -> "
          f"{res.certificate.get('edges_after')} edges (state size still {res.state.size()})")
    if gudhi_available():
        stats = rips_edge_collapse(pts, radius=scale, iterations=4)
        print(f"Rips graph at that scale: {stats['edges_before']} -> {stats['edges_after']} edges, "
              f"flag Betti preserved? {stats['betti_preserved']}")

    print("\nBetti F2 / real:")
    for name, facets in (("torus", torus7()), ("sphere", sphere2()), ("RP2", rp2())):
        f2, real = CohomologyF2(facets).betti(), simplicial_betti_real(facets)
        print(f"  {name:6s}  F2 {f2}   R {real}")
    assert simplicial_betti_real(rp2()) != CohomologyF2(rp2()).betti()

    square = CubicalComplex([parse_boolean_cube("--")])
    before, after = cubical_spectrum(square), cubical_spectrum(pair_collapse_cubical(square))
    print(f"\nsquare pair collapse: cells {before['n_cells']} -> {after['n_cells']}, "
          f"qubits {resource_counts(before['n_cells'])['qubits_one_per_cell']} -> "
          f"{resource_counts(after['n_cells'])['qubits_one_per_cell']}, "
          f"gap {before['spectral_gaps'][0]:.3f} -> {after['spectral_gaps'][0]:.3f}")
    assert before["betti_real"][0] == after["betti_real"][0] == 1
    print("\nTutorial 06 OK.")


if __name__ == "__main__":
    main()
