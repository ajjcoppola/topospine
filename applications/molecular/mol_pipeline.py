"""Molecular conformation pipeline: relative SpineTower vs coverage-only spine.

Data sources
------------
* ``synthetic_conformations`` – always available (CI fallback): a 13-atom
  aryl-carboxyl-like skeleton (6-ring, 3-atom linker, 4-atom functional group A)
  sampled over K torsion/jitter conformations.  **Synthetic geometry**; it is not
  a quantum-chemical or MD trajectory.
* ``try_md17`` – loads an MD17/MD22 ``.npz`` (``R`` array: frames x atoms x 3)
  when ``TOPOSPINE_MD17_NPZ`` points to a local file.  No download is attempted
  (the files are 100MB+); without the variable the bench reports it as skipped.
"""

from __future__ import annotations

import math
import os
import random
import time
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))

from topospine.spines.relative_tower import (  # noqa: E402
    ablation_report,
    build_relative_tower,
    relative_tower_certificate,
)

Point = tuple[float, float, float]


def _rot_x(p: Point, th: float) -> Point:
    c, s = math.cos(th), math.sin(th)
    x, y, z = p
    return (x, c * y - s * z, s * y + c * z)


def synthetic_conformations(
    n_conf: int = 12, seed: int = 7, jitter: float = 0.08
) -> tuple[list[Point], list[int], dict[str, Any]]:
    """Return (points, A-indices, meta).  Atoms per conformation: 6 ring + 3 linker + 4 group."""
    rng = random.Random(seed)
    ring = [(1.4 * math.cos(math.pi / 3 * k), 1.4 * math.sin(math.pi / 3 * k), 0.0) for k in range(6)]
    anchor = ring[0]
    # chain/group built along +x from the anchor (local frame), then rotated about x
    chain = [(anchor[0] + 1.5 * (i + 1), 0.3 * (i % 2), 0.0) for i in range(3)]
    tip = chain[-1]
    group = [
        (tip[0] + 1.2, 0.0, 0.0),  # C
        (tip[0] + 1.9, 1.0, 0.0),  # O
        (tip[0] + 1.9, -1.0, 0.3),  # O
        (tip[0] + 2.8, 1.0, 0.0),  # H
    ]
    n_atoms = 6 + 3 + 4
    points: list[Point] = []
    A: list[int] = []
    for k in range(n_conf):
        th1 = 2 * math.pi * k / n_conf
        th2 = rng.uniform(-0.6, 0.6)
        for a, p in enumerate(ring + chain + group):
            q = p
            if a >= 6:
                q = _rot_x((p[0] - anchor[0], p[1], p[2]), th1 if a < 9 else th1 + th2)
                q = (q[0] + anchor[0], q[1], q[2])
            q = (
                q[0] + rng.gauss(0, jitter),
                q[1] + rng.gauss(0, jitter),
                q[2] + rng.gauss(0, jitter),
            )
            idx = len(points)
            points.append(q)
            if a >= 9:
                A.append(idx)
    return points, A, {"source": "synthetic", "n_conf": n_conf, "n_atoms": n_atoms, "seed": seed}


def try_md17(n_frames: int = 12, n_A: int = 4) -> dict[str, Any] | None:
    path = os.environ.get("TOPOSPINE_MD17_NPZ")
    if not path or not Path(path).exists():
        return None
    import numpy as np

    d = np.load(path)
    R = d["R"]
    sel = np.linspace(0, len(R) - 1, n_frames).astype(int)
    frames = R[sel]  # (K, atoms, 3)
    centroid = frames[0].mean(axis=0)
    dist0 = np.linalg.norm(frames[0] - centroid, axis=1)
    A_atoms = sorted(np.argsort(-dist0)[:n_A].tolist())  # proxy: most peripheral atoms
    n_at = frames.shape[1]
    pts = [tuple(float(x) for x in frames[k, a]) for k in range(len(sel)) for a in range(n_at)]
    A = [k * n_at + a for k in range(len(sel)) for a in A_atoms]
    return {
        "points": pts,
        "A": A,
        "meta": {"source": "md17", "file": Path(path).name, "n_frames": n_frames, "A_atoms": A_atoms,
                 "A_definition": "proxy: most peripheral atoms of frame 0"},
    }


def run_one(points: list[Point], A: list[int], base_scale: float, n_levels: int = 3) -> dict[str, Any]:
    t0 = time.perf_counter()
    rel = build_relative_tower(points, A, base_scale, n_levels, relative=True)
    t_rel = time.perf_counter() - t0
    t0 = time.perf_counter()
    cov = build_relative_tower(points, A, base_scale, n_levels, relative=False)
    t_cov = time.perf_counter() - t0
    return {
        "n_points": len(points),
        "n_A": len(A),
        "base_scale": base_scale,
        "relative": {**relative_tower_certificate(rel), "total_wall_time_s": t_rel},
        "coverage_only": {**relative_tower_certificate(cov), "total_wall_time_s": t_cov},
        "ablation": ablation_report(points, A, base_scale, n_levels),
    }


def run_benchmark() -> dict[str, Any]:
    pts, A, meta = synthetic_conformations()
    out: dict[str, Any] = {"synthetic": {"meta": meta, **run_one(pts, A, base_scale=2.4)}}
    md = try_md17()
    if md is None:
        out["md17"] = {"skipped": True, "reason": "TOPOSPINE_MD17_NPZ not set / file missing"}
    else:
        out["md17"] = {
            "meta": md["meta"],
            **run_one(md["points"], md["A"], base_scale=1.2),
        }
    return out


if __name__ == "__main__":
    import json

    print(json.dumps(run_benchmark(), indent=2, default=str))
