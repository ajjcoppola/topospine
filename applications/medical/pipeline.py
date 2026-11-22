"""Medical volume pipeline: synthetic voxels (CI) + optional MedMNIST/CubicalRipser."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any

from topospine.spines.dual import voxel_grid_complex
from topospine.synth import PassManager, SynthesisState


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


def reduce_volume(
    mask: list[list[list[bool]]], shape: tuple[int, int, int], mode: str = "homotopy"
) -> dict[str, Any]:
    """``mode="homotopy"``: cells deleted by elementary collapse (cell count shrinks, a
    contractible blob collapses to 1 cell).  ``mode="covering"``: free faces are inserted
    in place; column count is invariant, total dimension drops, the IR is never emptied."""
    cx = voxel_grid_complex(shape, mask)
    grades = {str(c): 1.0 for c in cx.top_cells}
    state = SynthesisState(complex=cx, grades=grades, meta={"source": "synthetic_blob"}, mode=mode)
    tracemalloc.start()
    t0 = time.perf_counter()
    pm = PassManager.default(mode=mode)
    out = pm.run(state)
    elapsed = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "mode": mode,
        "shape": shape,
        "cells_before": state.size(),
        "cells_after": out.size(),
        "dim_sum_before": state.total_dimension(),
        "dim_sum_after": out.total_dimension(),
        "wall_time_s": elapsed,
        "peak_rss_bytes": peak,
        "passes": [e.get("pass") for e in out.log],
        "baseline": "synthetic_internal",
        "gudhi": _gudhi_available(),
        "cripser": _cripser_available(),
        "advantage": "verification_witnesses" if out.log else "size_reduction",
        "export": pm.export(out),
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
        # Take first volume, threshold
        img, _ = ds[0]
        # img shape depends on version; coerce to 3D list
        import numpy as np

        arr = np.array(img)
        if arr.ndim == 4:
            arr = arr[0]
        mask = (arr > arr.mean()).tolist()
        shape = (len(mask), len(mask[0]), len(mask[0][0]))
        return reduce_volume(mask, shape)
    except Exception as e:
        return {"skipped": True, "reason": str(e)}


def run_benchmark() -> dict[str, Any]:
    mask = synthetic_blob()
    syn = reduce_volume(mask, (8, 8, 8), mode="homotopy")
    syn_cov = reduce_volume(mask, (8, 8, 8), mode="covering")
    med = try_medmnist_organmnist3d()
    return {"synthetic": syn, "synthetic_covering": syn_cov, "medmnist": med}
