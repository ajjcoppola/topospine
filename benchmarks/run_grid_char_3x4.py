#!/usr/bin/env python3
"""Exhaustive far-side characterization on every 3x4 grid config (parallel)."""

from __future__ import annotations

import json
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "python"))

from topospine.cover.grid2d import (  # noqa: E402
    _opt_and_cexp,
    all_configs,
    build_grid,
    collapsible_pairs,
    far_side_condition,
    to_core,
)


def chunk_worker(cfgs):
    checked = mismatches = 0
    for cfg in cfgs:
        g = build_grid(cfg, 3, 4)
        core = to_core(g)
        if core is None:
            continue
        for p, f in collapsible_pairs(core):
            opt, c_exp = _opt_and_cexp(core, p, f)
            predicted = far_side_condition(core, p, f, opt)
            checked += 1
            if predicted != (c_exp == opt):
                mismatches += 1
    return checked, mismatches


def main() -> None:
    t0 = time.time()
    cfgs = list(all_configs(3, 4))
    print(f"configs {len(cfgs)}", flush=True)
    nworkers = 8
    chunk = (len(cfgs) + nworkers - 1) // nworkers
    batches = [cfgs[i : i + chunk] for i in range(0, len(cfgs), chunk)]
    checked = mismatches = 0
    with Pool(nworkers) as pool:
        for i, (c, m) in enumerate(pool.imap_unordered(chunk_worker, batches), 1):
            checked += c
            mismatches += m
            print(
                f"batch {i}/{len(batches)} checked={checked} miss={mismatches} t={time.time()-t0:.1f}",
                flush=True,
            )
    out = {"checked": checked, "mismatches": mismatches, "wall_time_s": time.time() - t0}
    print("3x4", out, flush=True)
    path = ROOT / "benchmarks" / "results" / "grid_collapse_char_3x4.json"
    path.write_text(json.dumps(out, indent=2))
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
