"""Medical volume pipeline: synthetic voxels (CI) + optional MedMNIST/CubicalRipser."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any

from topospine.cover.horn_chains import cubical_cohomology_betti_f2
from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.spines.dual import voxel_grid_complex
from topospine.synth import PassManager, SynthesisState
from topospine.synth.manager import PassManager as PM
from topospine.synth.passes import horn_retraction_closure


def synthetic_blob(shape: tuple[int, int, int] = (8, 8, 8), radius: float = 2.5) -> list[list[list[bool]]]:
    sx, sy, sz = shape
    cx, cy, cz = sx / 2, sy / 2, sz / 2
    mask = [[[False for _ in range(sz)] for _ in range(sy)] for _ in range(sx)]
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                if (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 <= radius**2:
                    mask[x][y][z] = True
    return mask


def _max_dim(state: SynthesisState) -> int:
    if state.size() == 0:
        return -1
    return max(int(c.dimension) for c in state.complex.top_cells)  # type: ignore[attr-defined]


def reduce_volume(
    mask: list[list[list[bool]]], shape: tuple[int, int, int], mode: str = "homotopy"
) -> dict[str, Any]:
    """``mode="homotopy"``: cells deleted by elementary collapse.
    ``mode="covering"``: Horn covering retraction (Paper E; non-vacuous on solid blobs).
    """
    cx = voxel_grid_complex(shape, mask)
    grades = {str(c): 1.0 for c in cx.top_cells}
    state = SynthesisState(complex=cx, grades=grades, meta={"source": "synthetic_blob"}, mode=mode)
    tracemalloc.start()
    t0 = time.perf_counter()
    if mode == "covering":
        pm = PM.covering_horn()
    else:
        pm = PassManager.default(mode=mode)
    out = pm.run(state)
    elapsed = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    horn_steps = sum(1 for e in out.log if e.get("pass") == "HornRetractionCollapse")
    return {
        "mode": mode,
        "shape": shape,
        "cells_before": state.size(),
        "cells_after": out.size(),
        "dim_sum_before": state.total_dimension(),
        "dim_sum_after": out.total_dimension(),
        "max_dim_before": _max_dim(state),
        "max_dim_after": _max_dim(out),
        "horn_steps": horn_steps,
        "wall_time_s": elapsed,
        "peak_rss_bytes": peak,
        "passes": [e.get("pass") for e in out.log],
        "baseline": "synthetic_internal",
        "gudhi": _gudhi_available(),
        "cripser": _cripser_available(),
        "advantage": "horn_covering" if horn_steps else ("verification_witnesses" if out.log else "size_reduction"),
        "export": pm.export(out),
    }


def reduce_2007_horn() -> dict[str, Any]:
    """Horn covering on Coppola–Weiss 2007 core with exact H*(F2) certificate."""
    cx = coppola_2007_boolean_complex()
    state = SynthesisState(complex=cx, mode="covering")
    betti_before = cubical_cohomology_betti_f2(list(cx.top_cells))
    t0 = time.perf_counter()
    out = horn_retraction_closure(state, max_steps=64)
    elapsed = time.perf_counter() - t0
    betti_after = cubical_cohomology_betti_f2(list(out.complex.top_cells))
    return {
        "mode": "covering_horn",
        "name": "coppola_2007",
        "cells_before": state.size(),
        "cells_after": out.size(),
        "dim_sum_before": state.total_dimension(),
        "dim_sum_after": out.total_dimension(),
        "max_dim_before": _max_dim(state),
        "max_dim_after": _max_dim(out),
        "horn_steps": len(out.log),
        "betti_before": betti_before,
        "betti_after": betti_after,
        "cohomology_preserved": betti_before == betti_after,
        "wall_time_s": elapsed,
        "L": (out.log[-1].get("L") if out.log else None),
        "U": (out.log[-1].get("U") if out.log else None),
    }


def _gudhi_available() -> bool:
    try:
        import gudhi  # noqa: F401

        return True
    except ImportError:
        return False


def _cripser_available() -> bool:
    try:
        import cripser  # noqa: F401

        return True
    except ImportError:
        return False


def try_medmnist_organmnist3d() -> dict[str, Any] | None:
    """Attempt MedMNIST 3D load; return None if unavailable (CI fallback)."""
    try:
        from medmnist import OrganMNIST3D  # type: ignore

        ds = OrganMNIST3D(split="train", download=True)
        import numpy as np

        img, _ = ds[0]
        arr = np.array(img)
        if arr.ndim == 4:
            arr = arr[0]
        mask = (arr > arr.mean()).tolist()
        shape = (len(mask), len(mask[0]), len(mask[0][0]))
        return reduce_volume(mask, shape, mode="covering")
    except Exception as e:
        return {"skipped": True, "reason": str(e)}


def run_benchmark() -> dict[str, Any]:
    mask = synthetic_blob()
    syn = reduce_volume(mask, (8, 8, 8), mode="homotopy")
    syn_cov = reduce_volume(mask, (8, 8, 8), mode="covering")
    core2007 = reduce_2007_horn()
    med = try_medmnist_organmnist3d()
    return {
        "synthetic": syn,
        "synthetic_covering": syn_cov,
        "coppola_2007_horn": core2007,
        "medmnist": med,
    }
