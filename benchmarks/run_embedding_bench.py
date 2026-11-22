#!/usr/bin/env python3
"""Loop 5 embedding spines: synthetic blobs and the local MiniLM npz if present.

No download.  The MiniLM file is data/embeddings_minilm_tiny.npz, or whatever
TOPOSPINE_EMB_NPZ points at.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.embeddings.clouds import (  # noqa: E402
    indices_with_label,
    load_embedding_npz,
    suggest_base_scale,
    synthetic_embedding_cloud,
)
from topospine.spines.relative_tower import ablation_report  # noqa: E402


def _block(points, labels, base_scale, source: str) -> dict:
    A = indices_with_label(labels, 0)
    rep = ablation_report(points, A, base_scale, n_levels=3)
    return {
        "source": source,
        "n": len(points),
        "n_A": len(A),
        "base_scale": base_scale,
        "own_rips_matches_gudhi": rep["own_rips_matches_gudhi"],
        "gudhi_available": rep["gudhi_available"],
        "methods": rep["methods"],
    }


def write_tex(blocks: list[dict], path: Path) -> None:
    rows = ""
    for block in blocks:
        for key in ("relative", "kcenter_same_budget", "random_same_budget", "coverage_only"):
            m = block["methods"][key]
            rows += (
                f"{block['source'].replace('_', ' ')} & {key.replace('_', ' ')} & "
                + " / ".join(str(x) for x in m["cover_sizes"])
                + " & "
                + " / ".join(f"{x:.3f}" for x in m["A_cover_radius"])
                + " & "
                + " / ".join(f"{x:.2f}" for x in m["nn_recall_A"])
                + " \\\\\n"
            )
    gudhi = "matched our F$_2$ Rips" if blocks[0]["own_rips_matches_gudhi"] == [True, True, True] else "see JSON"
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Embedding spines. $A$ is label 0. "
        "Recall is the fraction of $A$-points whose nearest other $A$-point "
        "lands in the same selected piece (1 is automatic when a single piece covers $A$). "
        f"GUDHI Rips on $A$ {gudhi}.}}\n"
        "\\label{tab:embed}\n\\resizebox{\\linewidth}{!}{\\begin{tabular}{llccc}\n\\hline\n"
        "cloud & method & cover sizes & $r_A$ & NN recall \\\\\n\\hline\n"
        + rows
        + "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )


def main() -> None:
    pts, labels, _meta = synthetic_embedding_cloud(n_per=12, n_bridge=4, seed=1)
    blocks = [_block(pts, labels, suggest_base_scale(pts), "synthetic")]
    env = os.environ.get("TOPOSPINE_EMB_NPZ")
    tiny = Path(env) if env else ROOT / "data" / "embeddings_minilm_tiny.npz"
    if tiny.exists():
        epts, elab, emeta = load_embedding_npz(tiny)
        blocks.append(_block(epts, elab, suggest_base_scale(epts, knn=3), emeta["file"]))
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "embedding_loop5.json").write_text(json.dumps({"blocks": blocks}, indent=2, default=str))
    write_tex(blocks, res / "embedding_ablation_table.tex")
    print(json.dumps({
        b["source"]: {
            "rA_relative": b["methods"]["relative"]["A_cover_radius"],
            "rA_kcenter": b["methods"]["kcenter_same_budget"]["A_cover_radius"],
            "recall_relative": b["methods"]["relative"]["nn_recall_A"],
            "gudhi": b["own_rips_matches_gudhi"],
        }
        for b in blocks
    }, indent=2))


if __name__ == "__main__":
    main()
