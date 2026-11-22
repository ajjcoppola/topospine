#!/usr/bin/env python3
"""Prelim figures: MiniLM embeddings, synthetic cloud, MD17 ethanol if present.

Writes benchmarks/results/figures/*.png and prelim_loop5.json.
MD17 is used only when data/md17_ethanol.npz exists or TOPOSPINE_MD17_NPZ is set.
No download.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "applications" / "molecular"))

from mol_pipeline import synthetic_conformations, try_md17  # noqa: E402
from topospine.embeddings.clouds import (  # noqa: E402
    indices_with_label,
    load_embedding_npz,
    suggest_base_scale,
    synthetic_embedding_cloud,
    write_minilm_npz,
)
from topospine.spines.gudhi_baseline import gudhi_available, rips_edge_collapse  # noqa: E402
from topospine.spines.relative_tower import ablation_report, build_relative_tower  # noqa: E402
from topospine.viz.prelim import write_prelim_figures  # noqa: E402


def _round_lists(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, float):
            out[k] = round(v, 4)
        elif isinstance(v, list) and v and isinstance(v[0], float):
            out[k] = [round(x, 4) for x in v]
        else:
            out[k] = v
    return out


def main() -> None:
    fig_dir = ROOT / "benchmarks" / "results" / "figures"
    data = ROOT / "data"
    data.mkdir(parents=True, exist_ok=True)
    tiny = data / "embeddings_minilm_tiny.npz"
    summary: dict = {"gudhi": gudhi_available()}

    if not tiny.exists():
        write_minilm_npz(tiny)
    emb_pts, emb_y, emb_meta = load_embedding_npz(tiny)
    emb_scale = suggest_base_scale(emb_pts, knn=3)
    A_emb = indices_with_label(emb_y, 0)
    emb_ab = ablation_report(emb_pts, A_emb, emb_scale, n_levels=3)
    summary["minilm"] = {
        "file": tiny.name,
        "n": len(emb_pts),
        "dim": emb_meta["dim"],
        "A_label": 0,
        "n_A": len(A_emb),
        "base_scale": round(emb_scale, 4),
        "own_rips_matches_gudhi": emb_ab["own_rips_matches_gudhi"],
        "methods": {k: _round_lists(v) for k, v in emb_ab["methods"].items()},
    }

    syn_pts, syn_y, syn_meta = synthetic_embedding_cloud(n_per=14, n_bridge=5, seed=1)
    syn_scale = suggest_base_scale(syn_pts)
    A_syn = indices_with_label(syn_y, 0)
    syn_ab = ablation_report(syn_pts, A_syn, syn_scale, n_levels=3)
    summary["synthetic_embeddings"] = {
        "meta": syn_meta,
        "base_scale": round(syn_scale, 4),
        "n_A": len(A_syn),
        "own_rips_matches_gudhi": syn_ab["own_rips_matches_gudhi"],
        "methods": {k: _round_lists(v) for k, v in syn_ab["methods"].items()},
    }

    mol_pts, mol_A, mol_meta = synthetic_conformations()
    mol_tower = build_relative_tower(mol_pts, mol_A, 2.4, n_levels=3, relative=True)
    mol_labels = [1 if i in set(mol_A) else 0 for i in range(len(mol_pts))]
    if gudhi_available():
        summary["mol_rips_collapse"] = rips_edge_collapse(mol_pts, radius=2.4, iterations=4)

    md_pts = md_labels = None
    md_title = ""
    md_path = os.environ.get("TOPOSPINE_MD17_NPZ")
    local = data / "md17_ethanol.npz"
    if not md_path and local.exists() and local.stat().st_size > 1_000_000:
        os.environ["TOPOSPINE_MD17_NPZ"] = str(local)
    md = try_md17(n_frames=12, n_A=4)
    if md is None:
        summary["md17"] = {"skipped": True}
    else:
        md_pts, md_A = md["points"], md["A"]
        md_labels = [1 if i in set(md_A) else 0 for i in range(len(md_pts))]
        md_title = f"MD17 ethanol, {md['meta']['n_frames']} frames (PCA)"
        md_ab = ablation_report(md_pts, md_A, base_scale=1.5, n_levels=3)
        summary["md17"] = {
            "meta": md["meta"],
            "n_points": len(md_pts),
            "n_A": len(md_A),
            "own_rips_matches_gudhi": md_ab["own_rips_matches_gudhi"],
            "methods": {k: _round_lists(v) for k, v in md_ab["methods"].items()},
        }

    radius_rows = [
        (name.replace("_", " "), summary["synthetic_embeddings"]["methods"][name]["A_cover_radius"])
        for name in ("relative", "kcenter_same_budget", "random_same_budget", "coverage_only")
    ]
    paths = write_prelim_figures(
        fig_dir,
        embedding_points=emb_pts,
        embedding_labels=emb_y,
        embedding_title=f"MiniLM sentences, {emb_meta['dim']}-d PCA",
        cloud_points=mol_pts,
        cloud_labels=mol_labels,
        cloud_centres=mol_tower.levels[0].selected,
        cloud_title="Synthetic conformations, coarse relative centres",
        md_points=md_pts,
        md_labels=md_labels,
        md_title=md_title,
        radius_rows=radius_rows,
    )
    summary["figures"] = [str(p.relative_to(ROOT)) for p in paths]
    out = ROOT / "benchmarks" / "results" / "prelim_loop5.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps({"figures": summary["figures"], "md17": "ran" if md else "skipped",
                      "minilm_match_gudhi": summary["minilm"]["own_rips_matches_gudhi"],
                      "syn_A_radius_relative": summary["synthetic_embeddings"]["methods"]["relative"]["A_cover_radius"],
                      "syn_A_radius_kcenter": summary["synthetic_embeddings"]["methods"]["kcenter_same_budget"]["A_cover_radius"]}, indent=2))


if __name__ == "__main__":
    main()
