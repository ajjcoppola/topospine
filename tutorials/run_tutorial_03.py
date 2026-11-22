#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "applications" / "medical"))

from topospine.spines import build_cover_tower, tower_certificate
from pipeline import reduce_volume, synthetic_blob


def main() -> None:
    print("=== Tutorial 03: spines / towers / medical ===\n")
    pts = [(math.cos(2 * math.pi * k / 16), math.sin(2 * math.pi * k / 16)) for k in range(16)]
    tower = build_cover_tower(pts, base_scale=1.0, n_levels=2)
    cert = tower_certificate(tower)
    print("tower:", json.dumps({k: cert[k] for k in ("contract", "n_levels", "cover_sizes", "betti_per_level")}, indent=2))
    mask = synthetic_blob((6, 6, 6), 2.0)
    med = reduce_volume(mask, (6, 6, 6), mode="homotopy")
    print("medical synthetic [homotopy: cells deleted]:", med["cells_before"], "→", med["cells_after"])
    assert med["cells_after"] <= med["cells_before"]
    cov = reduce_volume(mask, (6, 6, 6), mode="covering")
    print("medical synthetic [covering: face insertion]:", cov["cells_before"], "→", cov["cells_after"],
          "| dim sum", cov["dim_sum_before"], "→", cov["dim_sum_after"])
    assert cov["cells_after"] == cov["cells_before"] > 0  # covering IR is never emptied
    print("\nTutorial 03 OK.")


if __name__ == "__main__":
    main()
