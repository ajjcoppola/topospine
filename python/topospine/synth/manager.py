"""ABC-style pass manager: read → simplify → inspect → rewrite → check → export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from topospine.checkers.pass_trace import verify_pass_trace
from topospine.synth.ir import PassResult, SynthesisState
from topospine.synth.passes import (
    BoundedExactCorePass,
    CoveringAwareCollapsePass,
    ElementaryCubicalCollapsePass,
    FiltrationCompatibleCollapsePass,
    FlagEdgeCollapseAdapterPass,
    Pass,
    RelativeCollapsePass,
)


@dataclass
class PassManager:
    """Cost-based selection among valid transforms with checkpoint/rollback."""

    passes: list[Pass] = field(default_factory=list)
    max_iterations: int = 32
    prefer_size_reduction: bool = True
    mode: str = "homotopy"

    @classmethod
    def default(cls, mode: str = "homotopy") -> PassManager:
        """``mode="homotopy"`` (default): deletion-style elementary collapses.
        ``mode="covering"``: face-insertion collapse only; never empties the IR."""
        if mode == "covering":
            return cls.covering()
        if mode != "homotopy":
            raise ValueError(f"unknown mode {mode!r}")
        return cls(
            passes=[
                FiltrationCompatibleCollapsePass(),
                RelativeCollapsePass(),
                ElementaryCubicalCollapsePass(),
                BoundedExactCorePass(),
                FlagEdgeCollapseAdapterPass(),
            ]
        )

    @classmethod
    def covering(cls) -> PassManager:
        return cls(
            passes=[
                CoveringAwareCollapsePass(),
                BoundedExactCorePass(),
                FlagEdgeCollapseAdapterPass(),
            ],
            max_iterations=512,
            mode="covering",
        )

    def _progress(self, cert: dict[str, Any], before: SynthesisState, after: SynthesisState) -> float:
        if self.mode == "covering":
            if cert.get("pass") == "CoveringAwareCollapse":
                return float(before.total_dimension() - after.total_dimension())
            return 0.0
        return float(before.size() - after.size())

    def run(self, state: SynthesisState) -> SynthesisState:
        current = state.snapshot()
        current.mode = self.mode
        for _ in range(self.max_iterations):
            checkpoint = current.snapshot()
            candidates: list[tuple[float, PassResult]] = []
            for p in self.passes:
                result = p.try_apply(current)
                ok, reason = verify_pass_trace(result.certificate, result.state, checkpoint)
                if not result.accepted or not ok:
                    continue
                # Score: prefer smaller complexes; certification-only passes score neutral
                score = self._progress(result.certificate, checkpoint, result.state)
                if result.certificate.get("pass") == "BoundedExactCore":
                    score = 0.1  # weak preference to record certificate once
                candidates.append((score, result))
            if not candidates:
                break
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best = candidates[0]
            if best_score < 0:
                # Would grow — rollback
                current = checkpoint
                break
            # Accept mutation only if size reduced or exact-core cert
            if best_score > 0 or best.certificate.get("pass") == "BoundedExactCore":
                current = best.state
                if best.certificate.get("pass") == "BoundedExactCore":
                    # one-shot certification then stop simplify loop for this core
                    break
            else:
                current = checkpoint
                break
        return current

    def export(self, state: SynthesisState) -> dict[str, Any]:
        return {
            "name": state.complex.name,
            "size": state.size(),
            "cells": state.cell_names(),
            "grades": state.grades,
            "relative": sorted(state.relative),
            "log": state.log,
            "meta": state.meta,
        }
