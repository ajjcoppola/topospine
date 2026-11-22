"""Synthetic-bio / pathway circuits as AIG synthesis problems (Loop 3).

Two families, both *synthetic* (no wet-lab or curated-database claims):

1. ``gene_regulation_toy`` – next-state functions of a 5-gene toy network
   (CycD exogenous; Rb, E2F, CycE, CycA).  Don't-cares are *satisfiability*
   don't-cares from two stated invariants (CycE -> E2F, CycA -> CycE).
2. ``pathway_cascade`` – a seeded feed-forward Boolean cascade (default 24 gates
   over 6 primary inputs).  Local don't-cares are the **exact** satisfiability
   don't-cares: fan-in patterns that never occur over all 2^6 primary-input
   assignments.  Re-synthesizing every node on ON/DC therefore preserves every
   node value on every primary input (checked exhaustively).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable

from topospine.checkers.cover_witness import verify_cover_optimality_witness
from topospine.checkers.logic_trace import verify_logic_trace
from topospine.synth.logic_passes import (
    AbcBaselineAdapterPass,
    DontCareSpinePass,
    FactorDiagramRewritePass,
    LogicPassManager,
    LogicState,
    abc_optimize,
)


# --------------------------------------------------------------------- toy genes
GENES = ("CycD", "Rb", "E2F", "CycE", "CycA")  # variable order = bit order (MSB first)


def _bits(m: int, n: int = 5) -> tuple[int, ...]:
    return tuple((m >> (n - 1 - i)) & 1 for i in range(n))


def _invariant_ok(m: int) -> bool:
    cycd, rb, e2f, cyce, cyca = _bits(m)
    return (not cyce or e2f) and (not cyca or cyce)


# next-state rules (toy, Faure-style flavour; NOT the published model)
_RULES: dict[str, Callable[[int, int, int, int, int], int]] = {
    "Rb": lambda d, rb, e, ce, ca: int((not d and not ce and not ca) or (rb and not ca and not d)),
    "E2F": lambda d, rb, e, ce, ca: int((not rb and not ca) or (e and not rb)),
    "CycE": lambda d, rb, e, ce, ca: int(e and not rb),
    "CycA": lambda d, rb, e, ce, ca: int((e and not rb) or (ca and not rb)),
}


def gene_regulation_toy() -> dict[str, LogicState]:
    reachable = {m for m in range(32) if _invariant_ok(m)}
    dc = set(range(32)) - reachable
    out: dict[str, LogicState] = {}
    for gene, rule in _RULES.items():
        on = {m for m in reachable if rule(*_bits(m))}
        out[gene] = LogicState.from_minterms(5, on, dc, name=gene)
    return out


# --------------------------------------------------------------------- cascade
@dataclass
class BoolNetwork:
    n_pi: int
    fanins: list[tuple[int, ...]]  # node i (signal n_pi+i) -> signal indices
    tables: list[int]  # truth table as int over local minterms (MSB-first fan-in)

    @property
    def n_nodes(self) -> int:
        return len(self.fanins)

    def simulate(
        self, pi: tuple[int, ...], local: list[Callable[[tuple[int, ...]], int]] | None = None
    ) -> list[int]:
        sig = list(pi)
        for i, fin in enumerate(self.fanins):
            pat = tuple(sig[s] for s in fin)
            if local is None:
                idx = sum(b << (len(pat) - 1 - j) for j, b in enumerate(pat))
                sig.append((self.tables[i] >> idx) & 1)
            else:
                sig.append(local[i](pat))
        return sig[self.n_pi :]


def pathway_cascade(n_nodes: int = 24, n_pi: int = 6, fanin: int = 4, seed: int = 2026) -> BoolNetwork:
    rng = random.Random(seed)
    fanins, tables = [], []
    for i in range(n_nodes):
        avail = n_pi + i
        # bias toward recent signals so depth builds up (cascade-like)
        pool = list(range(max(0, avail - 10), avail))
        k = min(fanin, len(pool))
        fin = tuple(sorted(rng.sample(pool, k)))
        tt = 0
        for m in range(1 << k):
            if rng.random() < 0.45:
                tt |= 1 << m
        fanins.append(fin)
        tables.append(tt)
    return BoolNetwork(n_pi, fanins, tables)


def local_care_sets(net: BoolNetwork) -> list[tuple[set[int], set[int]]]:
    """Exact (ON, DC) per node: DC = fan-in patterns never reached by any PI assignment."""
    seen: list[set[int]] = [set() for _ in net.fanins]
    for pi_idx in range(1 << net.n_pi):
        pi = tuple((pi_idx >> (net.n_pi - 1 - i)) & 1 for i in range(net.n_pi))
        sig = list(pi)
        for i, fin in enumerate(net.fanins):
            pat = tuple(sig[s] for s in fin)
            idx = sum(b << (len(pat) - 1 - j) for j, b in enumerate(pat))
            seen[i].add(idx)
            sig.append((net.tables[i] >> idx) & 1)
    out = []
    for i, fin in enumerate(net.fanins):
        k = len(fin)
        on = {m for m in range(1 << k) if (net.tables[i] >> m) & 1}
        dc = set(range(1 << k)) - seen[i]
        out.append((on - dc, dc))
    return out


def _state_for_node(net: BoolNetwork, i: int, on: set[int], dc: set[int], use_dc: bool) -> LogicState:
    k = len(net.fanins[i])
    # With DC: ON restricted to reachable patterns (unreachable ON bits become free)
    if use_dc:
        return LogicState.from_minterms(k, on, dc, name=f"n{i}")
    full_on = {m for m in range(1 << k) if (net.tables[i] >> m) & 1}
    return LogicState.from_minterms(k, full_on, set(), name=f"n{i}")


def cover_witness_for(before: LogicState, cert: dict[str, Any]) -> dict[str, Any]:
    """CoverOptimalityWitness for a DontCareSpine certificate (decode_cover over its table)."""
    cm = DontCareSpinePass().build_table(before)
    idx = [cm.cols.index(s) for s in cert["cubes"]]
    return {"decode_cover": idx, "cost": float(len(idx)), "claimed_optimum": cert.get("optimality") == "ProvenMinimum"}


def synthesize_node(
    state: LogicState, objective: str = "cubes"
) -> tuple[LogicState, dict[str, Any]]:
    mgr = LogicPassManager(
        passes=[
            DontCareSpinePass(objective=objective),
            FactorDiagramRewritePass(),
            AbcBaselineAdapterPass(),
        ]
    )
    out = mgr.run(state)
    spine_cert = next(e for e in out.log if e.get("pass") == "DontCareSpine")
    cm = DontCareSpinePass().build_table(state)
    wit = cover_witness_for(state, spine_cert)
    ok_w, why_w = verify_cover_optimality_witness(cm, wit)
    ok_t, why_t = verify_logic_trace(spine_cert, _spine_state(out, spine_cert))
    exh = (spine_cert.get("audit") or {}).get("exhaustive_cost")
    return out, {
        "witness_ok": ok_w,
        "witness_why": why_w,
        "trace_ok": ok_t,
        "trace_why": why_t,
        "optimality": spine_cert.get("optimality"),
        "cubes": spine_cert["cubes_after"],
        "exhaustive_cost": exh,
        "audit_agrees": None if exh is None else float(exh) == wit["cost"],
    }


def _spine_state(final: LogicState, spine_cert: dict[str, Any]) -> LogicState:
    """Re-realize the DontCareSpine SOP as a state (the final state may be factored)."""
    from topospine.core.cubes import parse_boolean_cube
    from topospine.synth.aig import sop_to_aig

    st = LogicState(n=spine_cert["n"], on=frozenset(spine_cert["on"]), dc=frozenset(spine_cert["dc"]))
    st.cubes = [parse_boolean_cube(s) for s in spine_cert["cubes"]]
    st.aig, st.out = sop_to_aig(st.n, st.cubes)
    return st


def run_gene_toy() -> dict[str, Any]:
    rows = []
    for gene, st in gene_regulation_toy().items():
        no_dc = LogicState.from_minterms(st.n, set(st.on), set(), name=gene)
        res, info = synthesize_node(st)
        res_nodc, _ = synthesize_node(no_dc)
        rows.append(
            {
                "gene": gene,
                "on": len(st.on),
                "dc": len(st.dc),
                "gates_minterm": st.gates(),
                "gates_nodc": res_nodc.gates(),
                "gates_dc": res.gates(),
                "cubes_dc": len(res.cubes),
                "literals_dc": res.literals(),
                **info,
            }
        )
    return {
        "rows": rows,
        "totals": {
            "minterm": sum(r["gates_minterm"] for r in rows),
            "nodc": sum(r["gates_nodc"] for r in rows),
            "dc": sum(r["gates_dc"] for r in rows),
        },
    }


def run_cascade(
    n_nodes: int = 24,
    n_pi: int = 6,
    seed: int = 2026,
    objective: str = "cubes",
    with_abc: bool = False,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    net = pathway_cascade(n_nodes=n_nodes, n_pi=n_pi, seed=seed)
    care = local_care_sets(net)
    rows = []
    realized: list[LogicState] = []
    for i, (on, dc) in enumerate(care):
        st = _state_for_node(net, i, on, dc, use_dc=True)
        st_nodc = _state_for_node(net, i, on, dc, use_dc=False)
        res, info = synthesize_node(st, objective)
        res_nodc, _ = synthesize_node(st_nodc, objective)
        realized.append(res)
        abc_row: dict[str, Any] = {}
        if with_abc:
            # ABC sees what a standard flow sees: the care function with DC forced to 0
            a_min = abc_optimize(st_nodc.aig, st_nodc.out)  # type: ignore[arg-type]
            a_ours = abc_optimize(res.aig, res.out)  # type: ignore[arg-type]
            abc_row = {"abc_on_minterm": a_min["ands_final"], "abc_on_ours": a_ours["ands_final"]}
        rows.append(
            {
                "node": i,
                "fanin": len(net.fanins[i]),
                "on_full": len(st_nodc.on),
                "dc": len(dc),
                "gates_minterm": st_nodc.gates(),
                "gates_nodc": res_nodc.gates(),
                "gates_dc": res.gates(),
                **abc_row,
                **info,
            }
        )
    # global exhaustive verification of re-synthesized network on all PI assignments
    locals_ = [
        (lambda pat, r=r: r.aig.evaluate(r.out, list(pat)))  # type: ignore[union-attr]
        for r in realized
    ]
    mismatches = 0
    for pi_idx in range(1 << n_pi):
        pi = tuple((pi_idx >> (n_pi - 1 - j)) & 1 for j in range(n_pi))
        if net.simulate(pi) != net.simulate(pi, local=locals_):
            mismatches += 1
    totals = {
        "minterm": sum(r["gates_minterm"] for r in rows),
        "nodc": sum(r["gates_nodc"] for r in rows),
        "dc": sum(r["gates_dc"] for r in rows),
    }
    if with_abc and rows and rows[0].get("abc_on_minterm") is not None:
        totals["abc_on_minterm"] = sum(r["abc_on_minterm"] for r in rows)
        totals["abc_on_ours"] = sum(r["abc_on_ours"] for r in rows)
    return {
        "objective": objective,
        "n_nodes": n_nodes,
        "n_pi": n_pi,
        "seed": seed,
        "rows": rows,
        "totals": totals,
        "pi_assignments_checked": 1 << n_pi,
        "global_mismatches": mismatches,
        "all_witnesses_ok": all(r["witness_ok"] and r["trace_ok"] for r in rows),
        "wall_time_s": time.perf_counter() - t0,
    }
