"""Logic-synthesis passes on AIG / factor-diagram IR (ABC-style, certificate-carrying).

Pipeline for a single-output incompletely specified function f = (ON, DC):

    minterm SOP  --DontCareSpine-->  min-cube SOP  --FactorDiagramRewrite-->  factored AIG
                                                        --AbcBaseline--> (optional external ABC)

Every pass emits a ``LogicPassTrace`` certificate; :func:`verify_logic_trace`
(``topospine.checkers.logic_trace``) re-checks it by direct minterm evaluation,
independent of the passes.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from topospine.checkers.logic_trace import verify_logic_trace
from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import BooleanCube
from topospine.cover.auditor import _primes_from_minterms, audit_collapse_branch
from topospine.cover.minimize import minimize_cover
from topospine.synth.aig import (
    AIG,
    expr_literal_count,
    factored_aig,
    minterm_sop,
    sop_to_aig,
)


@dataclass
class LogicState:
    """Single-output incompletely specified function plus its current realization."""

    n: int
    on: frozenset[int]
    dc: frozenset[int] = frozenset()
    cubes: list[BooleanCube] = field(default_factory=list)
    aig: AIG | None = None
    out: int = 0
    log: list[dict[str, Any]] = field(default_factory=list)
    name: str = "f"

    @classmethod
    def from_minterms(cls, n: int, on: set[int] | frozenset[int], dc: set[int] | None = None, name: str = "f") -> LogicState:
        dc_f = frozenset(dc or ()) - frozenset(on)
        st = cls(n=n, on=frozenset(on), dc=dc_f, name=name)
        st.cubes = minterm_sop(n, on)
        st.aig, st.out = sop_to_aig(n, st.cubes)
        return st

    def gates(self) -> int:
        assert self.aig is not None
        return self.aig.gate_count([self.out])

    def depth(self) -> int:
        assert self.aig is not None
        return self.aig.depth([self.out])

    def literals(self) -> int:
        return sum(1 for c in self.cubes for b in c.bits if b is not None)

    def snapshot(self) -> LogicState:
        return LogicState(
            n=self.n,
            on=self.on,
            dc=self.dc,
            cubes=list(self.cubes),
            aig=self.aig,
            out=self.out,
            log=list(self.log),
            name=self.name,
        )


@dataclass
class LogicPassResult:
    accepted: bool
    state: LogicState
    certificate: dict[str, Any]
    reason: str = ""


class LogicPass(ABC):
    name = "LogicPass"
    contract = "CoverOptimality"

    @abstractmethod
    def try_apply(self, state: LogicState) -> LogicPassResult:
        ...


def _base_cert(p: LogicPass, old: LogicState, new: LogicState) -> dict[str, Any]:
    return {
        "type": "LogicPassTrace",
        "pass": p.name,
        "contract": p.contract,
        "n": old.n,
        "on": sorted(old.on),
        "dc": sorted(old.dc),
        "gates_before": old.gates(),
        "gates_after": new.gates(),
        "cubes_before": len(old.cubes),
        "cubes_after": len(new.cubes),
        "literals_before": old.literals(),
        "literals_after": new.literals(),
        "cubes": [str(c) for c in new.cubes],
    }


class DontCareSpinePass(LogicPass):
    """Min-cube SOP using don't-cares as free columns (never as rows).

    Rows = ON minterms (care).  Columns = primes of ON ∪ DC.  Exact B&B with the
    collapse-branch; the cyclic-core audit (exhaustive oracle) runs whenever the
    reduced table has ≤16 columns.
    """

    name = "DontCareSpine"
    contract = "CoverOptimality"

    OBJECTIVES = ("cubes", "literals", "cubes_then_literals")

    def __init__(self, depth_limit: int = 32, objective: str = "cubes") -> None:
        if objective not in self.OBJECTIVES:
            raise ValueError(f"objective must be one of {self.OBJECTIVES}")
        self.depth_limit = depth_limit
        self.objective = objective

    def _weight(self, prime: BooleanCube) -> float:
        lits = sum(1 for b in prime.bits if b is not None)
        if self.objective == "cubes":
            return 1.0
        if self.objective == "literals":
            return float(max(lits, 1))  # a constant-1 cube still costs something
        return 1000.0 + lits  # lexicographic: #cubes first, then literals (n <= 8)

    def build_table(self, state: LogicState) -> CoveringMatrix:
        n = state.n
        space = sorted(state.on | state.dc)

        def tup(m: int) -> tuple[int, ...]:
            return tuple((m >> (n - 1 - i)) & 1 for i in range(n))

        primes = sorted(_primes_from_minterms([tup(m) for m in space]), key=str)
        rows = [BooleanCube(tup(m)) for m in sorted(state.on)]
        return CoveringMatrix(
            rows=[str(r) for r in rows],
            cols=[str(p) for p in primes],
            matrix=[[r.is_face_of(p) for p in primes] for r in rows],
            weights=[self._weight(p) for p in primes],
            row_cubes=list(rows),
            col_cubes=list(primes),
        )

    def try_apply(self, state: LogicState) -> LogicPassResult:
        if not state.on:
            return LogicPassResult(False, state, {"type": "LogicPassTrace", "pass": self.name}, "empty ON-set")
        t0 = time.perf_counter()
        cm = self.build_table(state)
        # The returned cover always comes from plain B&B.  The collapse-branch is only an
        # audited comparator: Loop 4 found n=5 instances where it is suboptimal (claim C2).
        cover, cost, stats = minimize_cover(
            cm.copy(), use_collapse=False, depth_limit=self.depth_limit
        )
        cubes = [cm.col_cubes[j] for j in cover]
        new = state.snapshot()
        new.cubes = [c for c in cubes if c is not None]  # type: ignore[misc]
        new.aig, new.out = sop_to_aig(state.n, new.cubes)
        cert = _base_cert(self, state, new)
        audited = cm.n_cols() <= 16
        exact_ok = None
        collapse_agrees = None
        collapse_used = 0
        if audited:
            aud = audit_collapse_branch(cm, name=state.name, depth_limit=self.depth_limit)
            exact_ok = aud.exhaustive_cost == cost  # plain B&B vs exhaustive oracle
            collapse_agrees = aud.col_cost == cost
            collapse_used = aud.collapse_used
            cert["audit"] = aud.as_dict()
        cert.update(
            {
                "primes": cm.n_cols(),
                "care_rows": cm.n_rows(),
                "cost": cost,
                "collapse_used": collapse_used,
                "collapse_branch_agrees": collapse_agrees,
                "optimality": (
                    "ProvenMinimum" if audited and exact_ok else "Irredundant"
                ),
                "objective": self.objective,
                "optimality_scope": {
                    "cubes": "min #cubes over primes of ON∪DC covering ON",
                    "literals": "min total literals over primes of ON∪DC covering ON",
                    "cubes_then_literals": "min #cubes, then min literals, over primes of ON∪DC covering ON",
                }[self.objective],
                "wall_time_s": time.perf_counter() - t0,
            }
        )
        new.log.append(cert)
        return LogicPassResult(True, new, cert, "min-cube cover")


class FactorDiagramRewritePass(LogicPass):
    """Algebraic quick-factor of the current SOP into a shared AIG factor diagram."""

    name = "FactorDiagramRewrite"
    contract = "ChainEquivalence"  # functional (truth-table) equivalence; checked exhaustively

    def try_apply(self, state: LogicState) -> LogicPassResult:
        if not state.cubes:
            return LogicPassResult(False, state, {"type": "LogicPassTrace", "pass": self.name}, "no SOP")
        aig, out, expr = factored_aig(state.n, state.cubes)
        new = state.snapshot()
        new.aig, new.out = aig, out
        cert = _base_cert(self, state, new)
        cert["factored_literals"] = expr_literal_count(expr)
        cert["depth_after"] = new.depth()
        if new.gates() > state.gates():
            # fail-closed: do not accept a growing rewrite
            return LogicPassResult(False, state, cert, "rewrite would grow AIG")
        new.log.append(cert)
        return LogicPassResult(True, new, cert, "factored")


def parse_abc_and_count(text: str) -> int | None:
    """Parse the last ``and = N`` token from ABC ``print_stats`` output."""
    import re

    hits = re.findall(r"\band\s*=\s*(\d+)", text)
    return int(hits[-1]) if hits else None


# resyn2 expanded (the alias lives in abc.rc, which is not loaded in yosys-abc)
RESYN2 = (
    "balance; rewrite; refactor; balance; rewrite; rewrite -z; balance; "
    "refactor -z; rewrite -z; balance"
)


def find_abc() -> str | None:
    """``abc`` (Berkeley ABC) or ``yosys-abc`` (ABC bundled with Yosys, e.g. brew install yosys)."""
    return shutil.which("abc") or shutil.which("yosys-abc")


def abc_optimize(aig: AIG, out: int, script: str = RESYN2, timeout_s: int = 60) -> dict[str, Any]:
    """Run ABC on ``aig``: returns ``{available, binary, ands_initial, ands_final, ...}``."""
    return abc_optimize_blif_text(aig.to_blif(out), script, timeout_s)


def abc_optimize_blif_text(blif_text: str, script: str = RESYN2, timeout_s: int = 60) -> dict[str, Any]:
    """Run ABC on a (possibly multi-output) BLIF netlist given as text."""
    exe = find_abc()
    if exe is None:
        return {"available": False, "binary": None, "ands_initial": None, "ands_final": None}
    with tempfile.TemporaryDirectory() as td:
        blif = Path(td) / "f.blif"
        blif.write_text(blif_text)
        try:
            proc = subprocess.run(
                [exe, "-c", f"read_blif {blif}; strash; print_stats; {script}; print_stats"],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:  # pragma: no cover
            return {"available": True, "binary": exe, "ands_initial": None, "ands_final": None, "error": repr(exc)}
    import re

    hits = [int(x) for x in re.findall(r"\band\s*=\s*(\d+)", proc.stdout)]
    return {
        "available": True,
        "binary": Path(exe).name,
        "returncode": proc.returncode,
        "ands_initial": hits[0] if hits else None,
        "ands_final": hits[-1] if hits else None,
        "script": script,
    }


class AbcBaselineAdapterPass(LogicPass):
    """Berkeley ABC (Mishchenko) baseline adapter.

    If ``abc`` or ``yosys-abc`` is on PATH, writes the current AIG as BLIF and runs
    ``strash`` plus the expanded ``resyn2`` script to obtain a baseline AND count.  The
    pass never mutates the state (ABC's output is a competitor, not a certified
    rewrite); it records the comparison.  Without ABC it emits a no-op certificate.
    """

    name = "AbcBaselineAdapter"
    contract = "CoverOptimality"

    def __init__(self, script: str = RESYN2, timeout_s: int = 60) -> None:
        self.script = script
        self.timeout_s = timeout_s

    def try_apply(self, state: LogicState) -> LogicPassResult:
        exe = find_abc()
        cert: dict[str, Any] = {
            "type": "LogicPassTrace",
            "pass": self.name,
            "contract": self.contract,
            "n": state.n,
            "on": sorted(state.on),
            "dc": sorted(state.dc),
            "gates_before": state.gates(),
            "gates_after": state.gates(),
            "cubes_before": len(state.cubes),
            "cubes_after": len(state.cubes),
            "cubes": [str(c) for c in state.cubes],
            "abc_available": exe is not None,
            "action": "baseline_only_no_mutation",
        }
        if exe is None:
            cert["abc_ands"] = None
            return LogicPassResult(False, state, cert, "abc not on PATH (no-op certificate)")
        assert state.aig is not None
        res = abc_optimize(state.aig, state.out, self.script, self.timeout_s)
        cert["abc_ands"] = res.get("ands_final")
        cert["abc_ands_initial"] = res.get("ands_initial")
        cert["abc_binary"] = res.get("binary")
        cert["abc_returncode"] = res.get("returncode")
        return LogicPassResult(False, state, cert, "abc baseline recorded")


@dataclass
class LogicPassManager:
    passes: list[LogicPass] = field(
        default_factory=lambda: [
            DontCareSpinePass(),
            FactorDiagramRewritePass(),
            AbcBaselineAdapterPass(),
        ]
    )

    def run(self, state: LogicState) -> LogicState:
        """Run each pass once in order; verify independently; roll back on failure."""
        cur = state.snapshot()
        for p in self.passes:
            res = p.try_apply(cur)
            if not res.accepted:
                cur.log.append(res.certificate)
                continue
            ok, why = verify_logic_trace(res.certificate, res.state)
            if not ok:
                res.certificate["rolled_back"] = why
                cur.log.append(res.certificate)
                continue
            cur = res.state
        return cur
