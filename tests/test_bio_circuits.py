"""Loop 3: bio-circuit AIG synthesis with don't-cares and CoverOptimality witnesses."""

from __future__ import annotations

from topospine.examples.bio_circuits import (
    gene_regulation_toy,
    local_care_sets,
    pathway_cascade,
    run_cascade,
    run_gene_toy,
)


def test_gene_toy_dc_beats_baselines_and_witnesses_hold():
    out = run_gene_toy()
    t = out["totals"]
    assert t["dc"] <= t["nodc"] < t["minterm"]
    for r in out["rows"]:
        assert r["witness_ok"] and r["trace_ok"]
        assert r["optimality"] == "ProvenMinimum" and r["audit_agrees"]
        assert r["gates_dc"] <= r["gates_nodc"]


def test_gene_toy_dc_come_from_stated_invariants():
    st = gene_regulation_toy()["CycE"]
    # 5 vars, invariants CycE->E2F, CycA->CycE leave 32 - |valid| DC minterms
    assert len(st.dc) == 16 and len(st.on) + len(st.dc) <= 32


def test_cascade_resynthesis_preserves_network_exactly():
    out = run_cascade(n_nodes=24, n_pi=6, seed=2026)
    assert out["global_mismatches"] == 0
    assert out["pi_assignments_checked"] == 64
    assert out["all_witnesses_ok"]
    assert out["totals"]["dc"] < out["totals"]["nodc"] < out["totals"]["minterm"]


def test_cascade_sdc_is_exact_not_sampled():
    net = pathway_cascade(n_nodes=8, n_pi=4, seed=5)
    care = local_care_sets(net)
    for i, (on, dc) in enumerate(care):
        k = len(net.fanins[i])
        assert not (on & dc) and on | dc <= set(range(1 << k))
        # every non-DC pattern truly occurs: reconstruct by brute force
        seen = set()
        for pi_idx in range(1 << net.n_pi):
            pi = tuple((pi_idx >> (net.n_pi - 1 - j)) & 1 for j in range(net.n_pi))
            sig = list(pi)
            for jn, fin in enumerate(net.fanins[: i + 1]):
                pat = tuple(sig[s] for s in fin)
                idx = sum(b << (len(pat) - 1 - j) for j, b in enumerate(pat))
                if jn == i:
                    seen.add(idx)
                sig.append((net.tables[jn] >> idx) & 1)
        assert seen == set(range(1 << k)) - dc
