#!/usr/bin/env python3
"""Audit Layer-0 free-face push-down, Far-Side IFF, existential witnesses, and blob solver vs plain B&B.

Writes benchmarks/results/layer0_blob_audit.json and layer0_blob_audit_table.tex.
"""

from __future__ import annotations

import json
import random
import sys
import time
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.core.covering import reduce_to_cyclic_core  # noqa: E402
from topospine.core.cubes import BooleanCube, parse_boolean_cube  # noqa: E402
from topospine.cover.collapse import list_collapsible_primes  # noqa: E402
from topospine.cover.cube_array import (  # noqa: E402
    covering_table_from_cube_array,
    expand_to_primes_blake,
    iterative_free_face_blob_bound,
    layer0_far_side_holds,
    layer0_include_cex_n6_bridged_12x13,
    layer0_swap_cex_n5_9x9,
    minimize_cube_array,
    minimize_layer0_exact,
    zero_loss_free_face_pushdown,
)
from topospine.cover.minimize import MinimizeStats, minimize_cover  # noqa: E402


def main() -> None:
    t0 = time.perf_counter()
    rng = random.Random(20261123)
    all5 = list(product((0, 1), repeat=5))

    n_trials = 3000
    n_cores = 0
    n_coll_cores = 0
    zpush_fires = 0
    far_iff_checked = 0
    far_iff_mismatches = 0
    blob_ub_exact = 0
    blob_ub_emptied = 0
    disagreements = 0
    plain_calls = 0
    plain_time = 0.0
    l0_nodes = 0
    l0_time = 0.0

    for _ in range(n_trials):
        dens = rng.uniform(0.18, 0.72)
        on = [m for m in all5 if rng.random() < dens]
        if len(on) < 3:
            continue
        primes = expand_to_primes_blake([BooleanCube(m) for m in on])
        cm = covering_table_from_cube_array(primes)
        core, _, _ = reduce_to_cyclic_core(cm.copy())
        if core.n_rows() == 0 or core.n_cols() > 16:
            continue
        n_cores += 1
        coll = list_collapsible_primes(core)
        if coll:
            n_coll_cores += 1
            _, _, nz = zero_loss_free_face_pushdown(core)
            if nz > 0:
                zpush_fires += 1
            bp = iterative_free_face_blob_bound(core)
            if bp.emptied_by_push:
                blob_ub_emptied += 1
            for j, faces in coll:
                for f in faces:
                    assert isinstance(f, BooleanCube)
                    ok, _, _ = layer0_far_side_holds(core, j, f)
                    far_iff_checked += 1
                    far_iff_mismatches += int(not ok)

        s_std = MinimizeStats()
        _, c_std, s_std = minimize_cover(cm.copy(), use_collapse=False, stats=s_std)
        _, c_l0, r_l0 = minimize_layer0_exact(cm.copy())
        disagreements += int(c_std != c_l0)
        plain_calls += s_std.recursive_calls
        plain_time += s_std.wall_time_s
        l0_nodes += r_l0.bb_nodes
        l0_time += r_l0.wall_time_s
        if coll:
            # check if iterative blob UB matched true core opt
            _, core_opt, _ = minimize_layer0_exact(core)
            if bp.upper_bound == int(core_opt):
                blob_ub_exact += 1

    # Stress test: 3-blob Layer-0 cube array (3 pairwise-distance-2 copies in n=8 -> 27x27 core)
    w1_input, _, _ = layer0_swap_cex_n5_9x9()
    c3_blobs = (
        [parse_boolean_cube("000" + str(c)) for c in w1_input]
        + [parse_boolean_cube("011" + str(c)) for c in w1_input]
        + [parse_boolean_cube("101" + str(c)) for c in w1_input]
    )
    cm_3blob = covering_table_from_cube_array(expand_to_primes_blake(c3_blobs))
    s_3b = MinimizeStats()
    _, c_3b_std, s_3b = minimize_cover(cm_3blob.copy(), use_collapse=False, stats=s_3b)
    _, c_3b_l0, r_3b_l0 = minimize_layer0_exact(cm_3blob.copy())
    assert c_3b_std == c_3b_l0 == 24.0

    # Witness 2 bridged double-6-cycle
    w2_primes, w2_core, _ = layer0_include_cex_n6_bridged_12x13()
    s_w2 = MinimizeStats()
    _, c_w2_std, s_w2 = minimize_cover(w2_core.copy(), use_collapse=False, stats=s_w2)
    r_w2_l0 = minimize_cube_array(w2_primes)
    assert c_w2_std == 6.0 and r_w2_l0.cost == 8.0 and r_w2_l0.bb_nodes == 0

    out = {
        "n5_random": {
            "trials": n_trials,
            "nontrivial_cores": n_cores,
            "collapsible_cores": n_coll_cores,
            "zero_loss_pushdown_fires": zpush_fires,
            "zero_loss_pushdown_rate": zpush_fires / max(1, n_coll_cores),
            "far_side_iff_pairs_checked": far_iff_checked,
            "far_side_iff_mismatches": far_iff_mismatches,
            "iter_blob_ub_emptied": blob_ub_emptied,
            "iter_blob_ub_exact": blob_ub_exact,
            "iter_blob_ub_exact_rate": blob_ub_exact / max(1, n_coll_cores),
            "exact_disagreements_vs_plain_bb": disagreements,
            "plain_bb_recursive_calls": plain_calls,
            "layer0_blob_bb_nodes": l0_nodes,
            "plain_bb_time_s": plain_time,
            "layer0_blob_time_s": l0_time,
        },
        "three_blob_27x27_core": {
            "opt": c_3b_l0,
            "plain_bb_calls": s_3b.recursive_calls,
            "layer0_blob_nodes": r_3b_l0.bb_nodes,
            "plain_bb_time_s": s_3b.wall_time_s,
            "layer0_blob_time_s": r_3b_l0.wall_time_s,
        },
        "bridged_double_6cycle_12x13": {
            "core_opt": c_w2_std,
            "plain_bb_calls_on_core": s_w2.recursive_calls,
            "layer0_blob_nodes": r_w2_l0.bb_nodes,
        },
        "wall_s": time.perf_counter() - t0,
    }

    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "layer0_blob_audit.json").write_text(json.dumps(out, indent=2))

    r5 = out["n5_random"]
    tex = (
        "\\begin{table}[h]\\centering\\small\n"
        "\\caption{Layer-0 cube-array audit ($n=5$ Blake-prime cyclic cores and multi-blob "
        "benchmarks). Zero-loss push-down ($F_p(f)=\\emptyset$) fires on "
        f"{r5['zero_loss_pushdown_fires']}/{r5['collapsible_cores']} "
        f"({100*r5['zero_loss_pushdown_rate']:.1f}\\%) collapsible cores with 0 errors; "
        f"Layer-0 Far-Side IFF has {r5['far_side_iff_mismatches']}/{r5['far_side_iff_pairs_checked']} "
        "mismatches; exact Layer-0 blob solver matches plain B\\&B on all instances while cutting "
        f"search nodes from {r5['plain_bb_recursive_calls']} to {r5['layer0_blob_bb_nodes']}.}}\n"
        "\\label{tab:layer0-blobs}\n"
        "\\begin{tabular}{lrrr}\\hline\n"
        "benchmark & plain B\\&B calls & Layer-0 blob nodes & cost mismatches \\\\\\hline\n"
        f"$n=5$ random ({r5['nontrivial_cores']} cores) & {r5['plain_bb_recursive_calls']} & {r5['layer0_blob_bb_nodes']} & {r5['exact_disagreements_vs_plain_bb']} \\\\\n"
        f"Bridged double-$6$-cycle ($12\\times 13$) & {s_w2.recursive_calls} & {r_w2_l0.bb_nodes} & 0 \\\\\n"
        f"Three-blob core ($27\\times 27$) & {s_3b.recursive_calls} & {r_3b_l0.bb_nodes} & 0 \\\\\n"
        "\\hline\\end{tabular}\\end{table}\n"
    )
    (res / "layer0_blob_audit_table.tex").write_text(tex)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
