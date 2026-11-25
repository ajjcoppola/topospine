"""Rewrite passes emitting JSON certificates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from topospine.core.cubical import CubicalComplex
from topospine.cover.auditor import audit_collapse_branch
from topospine.cover.minimize import minimize_cover
from topospine.core.covering import graded_table_from_cubical
from topospine.synth.ir import PassResult, SynthesisState


class Pass(ABC):
    name: str = "Pass"
    contract: str = "ElementaryCollapse"

    @abstractmethod
    def try_apply(self, state: SynthesisState) -> PassResult:
        ...


class ElementaryCubicalCollapsePass(Pass):
    name = "ElementaryCubicalCollapse"
    contract = "ElementaryCollapse"

    def try_apply(self, state: SynthesisState) -> PassResult:
        if state.mode == "covering":
            return PassResult(
                False,
                state,
                {"type": "PassTrace", "pass": self.name, "blocked": "covering-mode"},
                "deletion-style collapse forbidden in covering mode",
            )
        coll = state.complex.collapsible_cells()
        if not coll:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, "no free faces")
        cell, faces = coll[0]
        face = faces[0]
        # Refuse if cell is in relative subcomplex A (must use RelativeCollapsePass)
        if str(cell) in state.relative:
            return PassResult(
                False,
                state,
                {"type": "PassTrace", "pass": self.name, "blocked": "relative"},
                "cell in designated relative subcomplex",
            )
        new_tops = [c for c in state.complex.top_cells if c != cell]
        # Insert free face as a top cell only if it is not already present
        if face not in new_tops and all(str(face) != str(c) for c in new_tops):
            # Keep dimension: free face is lower-dim; for covering synthesis we
            # remove the collapsible top cell (simple-homotopy elementary collapse).
            pass
        new_state = state.snapshot()
        new_state.complex = CubicalComplex(top_cells=new_tops, name=state.complex.name)
        # Drop grade for removed cell; keep others
        new_state.grades.pop(str(cell), None)
        cert = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "cell": str(cell),
            "free_face": str(face),
            "other_top_cells": [str(c) for c in state.complex.top_cells if c != cell],
            "chi_before": state.complex.euler_characteristic(),
            "chi_after": new_state.complex.euler_characteristic(),
            "size_before": state.size(),
            "size_after": new_state.size(),
        }
        new_state.log.append(cert)
        return PassResult(True, new_state, cert, "collapsed")


class CoveringAwareCollapsePass(Pass):
    """
    Covering-mode collapse (face insertion).

    Replaces a top cell c with one of its free faces f *in place*, so the
    covering IR keeps a column for the region instead of dropping it.  This is
    the IR-level image of the collapse-branch of the 2007 algorithm: the parent
    column is replaced by F(p) with the same weight, and the certificate stores
    a decode map ``f -> c`` so any cover of the reduced IR transports back
    (Lean: ``TopoSpine.CoveringCollapse.size_preserved``/``transport_optimum``).

    Guards (fail-closed):
      * the cell is not in the designated relative subcomplex;
      * ``cover_admissible_free_face`` holds on the typed graded table;
      * the free face is not already present.
    Unlike :class:`ElementaryCubicalCollapsePass` it never reduces the number of
    columns, hence can never silently empty a covering IR.
    """

    name = "CoveringAwareCollapse"
    contract = "CoverOptimality"

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes

        def reject(reason: str) -> PassResult:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, reason)

        if state.size() == 0:
            return reject("empty")
        cm = graded_table_from_cubical(state.complex, include_faces_down_to=0)
        names_present = set(state.cell_names())
        for col_j, faces in list_collapsible_primes(cm):
            cell = cm.col_cubes[col_j]
            if cell is None or str(cell) in state.relative:
                continue
            for face in faces:
                if str(face) in names_present:
                    continue
                if not cover_admissible_free_face(cm, col_j, face):
                    continue
                new_tops = [face if c == cell else c for c in state.complex.top_cells]
                new_state = state.snapshot()
                new_state.complex = CubicalComplex(top_cells=new_tops, name=state.complex.name)
                g = new_state.grades.pop(str(cell), None)
                if g is not None:
                    new_state.grades.setdefault(str(face), g)
                decode = dict(new_state.meta.get("decode", {}))
                decode[str(face)] = decode.pop(str(cell), str(cell))
                new_state.meta["decode"] = decode
                cert = {
                    "type": "PassTrace",
                    "pass": self.name,
                    "contract": self.contract,
                    "cell": str(cell),
                    "inserted_face": str(face),
                    "decode": {str(face): decode[str(face)]},
                    "weight_preserved": True,
                    "size_before": state.size(),
                    "size_after": new_state.size(),
                    "dim_before": int(cell.dimension),  # type: ignore[attr-defined]
                    "dim_after": int(face.dimension),  # type: ignore[attr-defined]
                }
                new_state.log.append(cert)
                return PassResult(True, new_state, cert, "face inserted")
        return reject("no admissible free face")


class HornRetractionCollapsePass(Pass):
    """Covering-mode Horn retraction (Theorem H1): replace ``f_top`` by ``∂f_top \\ {f}``.

    Unlike :class:`CoveringAwareCollapsePass` (single-face swap, vacuous on the 2007
    core and solid voxel blobs), this pass inserts the full active horn
    ``Λ_f(f_top) = ∂f_top \\ {f}``, preserving residual care coverage and exact
    cubical cohomology ``H*(K; F2)``.  Applicable whenever ``f`` is a free face of
    a top cube with ``dim >= 2``, or a cyclic-core non-essential edge (``dim = 1``).

    Certificate records the multi-face ``horn -> parent`` decode map, Betti numbers
    before/after, and a cost-window ``(L, U)``.
    """

    name = "HornRetractionCollapse"
    contract = "CoverOptimality"

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.cover.horn_chains import cubical_cohomology_betti_f2, horn_faces
        from topospine.cover.cube_array import _masks_from_cm, _mis_lower_bound
        from topospine.core.cubes import BooleanCube, GridCube

        def reject(reason: str) -> PassResult:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, reason)

        if state.size() == 0:
            return reject("empty")

        present = set(state.cell_names())
        # Prefer complex.collapsible_cells (O(tops)) over graded tables on large voxel blobs
        use_fast = state.size() > 16 or any(isinstance(c, GridCube) for c in state.complex.top_cells)
        candidates: list[tuple[int, Any, Any]] = []
        cm = None
        col_j = -1
        if use_fast:
            for cell, faces in state.complex.collapsible_cells():
                if str(cell) in state.relative:
                    continue
                dim = int(cell.dimension)  # type: ignore[attr-defined]
                if dim < 1:
                    continue
                for face in faces:
                    candidates.append((dim, cell, face))
        else:
            from topospine.cover.collapse import list_collapsible_primes

            cm = graded_table_from_cubical(state.complex, include_faces_down_to=0)
            for j, faces in list_collapsible_primes(cm):
                cell = cm.col_cubes[j]
                if cell is None or str(cell) in state.relative:
                    continue
                dim = int(cell.dimension)  # type: ignore[attr-defined]
                if dim < 1:
                    continue
                for face in faces:
                    candidates.append((dim, cell, face))

        if not candidates:
            return reject("no free face for horn retraction")

        candidates.sort(key=lambda t: (-t[0], str(t[1]), str(t[2])))
        _, cell, face = candidates[0]
        if cm is not None:
            col_j = next(j for j, c in enumerate(cm.col_cubes) if c == cell or str(c) == str(cell))
        horn = horn_faces(cell, face)
        # Active horn faces (all for geometric GridCube; residual-row filter for Boolean tables)
        active: list[Any] = []
        if cm is None or any(rc is None for rc in cm.row_cubes):
            active = list(horn)
        else:
            for h in horn:
                if str(h) in present and str(h) != str(cell):
                    active.append(h)
                    continue
                covers_row = any(
                    cm.matrix[i][col_j] and rc is not None and rc.is_face_of(h)  # type: ignore[attr-defined]
                    for i, rc in enumerate(cm.row_cubes)
                )
                if covers_row:
                    active.append(h)
            if not active:
                active = list(horn)

        # Replace cell by horn faces not already present as other tops
        new_tops: list[Any] = []
        inserted: list[str] = []
        for c in state.complex.top_cells:
            if c == cell or str(c) == str(cell):
                continue
            new_tops.append(c)
        for h in active:
            if any(str(t) == str(h) for t in new_tops):
                continue
            new_tops.append(h)
            inserted.append(str(h))
        if not inserted and all(any(str(t) == str(h) for t in state.complex.top_cells if str(t) != str(cell)) for h in active):
            return reject("horn faces already present; nothing to insert")

        new_state = state.snapshot()
        new_state.complex = CubicalComplex(top_cells=new_tops, name=state.complex.name)
        g = new_state.grades.pop(str(cell), None)
        decode = dict(new_state.meta.get("decode", {}))
        parent = decode.pop(str(cell), str(cell))
        horn_decode: dict[str, str] = {}
        for h in active:
            hs = str(h)
            decode[hs] = parent
            horn_decode[hs] = parent
            if g is not None:
                new_state.grades.setdefault(hs, g)
        new_state.meta["decode"] = decode

        # Exact H* is O(face-closure); skip on large GridCube volumes (bench computes once).
        from topospine.core.cubes import BooleanCube

        tops_small = state.size() <= 12 and all(
            isinstance(c, BooleanCube) for c in state.complex.top_cells
        )
        if tops_small:
            betti_before = cubical_cohomology_betti_f2(list(state.complex.top_cells))
            betti_after = cubical_cohomology_betti_f2(list(new_state.complex.top_cells))
            cohom_ok: bool | None = betti_before == betti_after
        else:
            betti_before, betti_after, cohom_ok = None, None, None

        # Cost window: cheap bounds; skip full rematrix on huge / fast-path volumes
        if cm is not None and cm.n_rows() <= 64 and cm.n_cols() <= 32:
            try:
                cm_after = graded_table_from_cubical(new_state.complex, include_faces_down_to=0)
                masks_a, univ_a = _masks_from_cm(cm_after)
                Ca = cm_after.n_cols()
                rc_a = [
                    sum((1 << j) for j in range(Ca) if (masks_a[j] >> r) & 1)
                    for r in range(cm_after.n_rows())
                ]
                L = _mis_lower_bound(rc_a, univ_a) if univ_a else 0
                U = cm_after.n_cols()
            except Exception:
                L, U = 0, new_state.size()
        else:
            L, U = 0, new_state.size()

        max_dim_before = max((int(c.dimension) for c in state.complex.top_cells), default=-1)  # type: ignore[attr-defined]
        max_dim_after = max((int(c.dimension) for c in new_state.complex.top_cells), default=-1)  # type: ignore[attr-defined]
        cert = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "cell": str(cell),
            "free_face": str(face),
            "inserted_horn": inserted,
            "horn_faces": [str(h) for h in active],
            "decode": horn_decode,
            "weight_preserved": True,
            "size_before": state.size(),
            "size_after": new_state.size(),
            "dim_before": int(cell.dimension),  # type: ignore[attr-defined]
            "dim_after": int(face.dimension),  # type: ignore[attr-defined]
            "max_dim_before": max_dim_before,
            "max_dim_after": max_dim_after,
            "betti_before": betti_before,
            "betti_after": betti_after,
            "cohomology_preserved": cohom_ok,
            "L": L,
            "U": U,
        }
        new_state.log.append(cert)
        return PassResult(True, new_state, cert, "horn retraction")


def horn_retraction_closure(
    state: SynthesisState, max_steps: int = 256
) -> SynthesisState:
    """Apply HornRetractionCollapse until no free-face horn step remains."""
    from topospine.checkers.pass_trace import verify_pass_trace

    cur = state.snapshot()
    p = HornRetractionCollapsePass()
    for _ in range(max_steps):
        res = p.try_apply(cur)
        if not res.accepted:
            break
        ok, why = verify_pass_trace(res.certificate, res.state, cur)
        if not ok:
            raise RuntimeError(f"HornRetractionCollapse failed independent check: {why}")
        cur = res.state
    return cur


class FiltrationCompatibleHornPass(Pass):
    """Homotopy-mode Horn retraction restricted to ``birth(f) == birth(f_top)``.

    Uses ``filtration_compatible_spine`` (H4) on the graded top cells; records cell
    compression and equal persistent-cohomology Betti curves when cheap to compute.
    """

    name = "FiltrationCompatibleHorn"
    contract = "PersistentEquivalence"

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.cover.horn_chains import (
            cubical_persistent_cohomology_betti_f2,
            filtration_compatible_spine,
            horn_faces,
        )
        from topospine.core.cubes import BooleanCube

        def reject(reason: str) -> PassResult:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, reason)

        if state.mode == "covering":
            return reject("use HornRetractionCollapse in covering mode")
        if state.size() == 0:
            return reject("empty")
        # Build birth map on face-closed Boolean tops when grades exist
        tops = list(state.complex.top_cells)
        if not tops or not all(isinstance(c, BooleanCube) for c in tops):
            return reject("filtration horn requires BooleanCube tops")
        births: dict[Any, float] = {}
        for c in tops:
            g = state.grades.get(str(c), 0.0)
            births[c] = g
            for f in c.faces():
                births.setdefault(f, state.grades.get(str(f), g))

        rem, steps = filtration_compatible_spine(births)
        if not steps:
            return reject("no filtration-compatible horn step")
        # Apply first step only (pass manager iterates)
        f, gcell = steps[0]
        if str(gcell) in state.relative:
            return reject("relative cell")
        if gcell not in tops:
            return reject("collapsed cell not a top")
        horn = horn_faces(gcell, f)
        new_tops = [c for c in tops if c != gcell]
        inserted = []
        for h in horn:
            if h not in new_tops and all(str(t) != str(h) for t in new_tops):
                new_tops.append(h)
                inserted.append(str(h))
        if not inserted:
            # Pure deletion of {f,g} from face-closed view: remove gcell only if horn already present
            new_tops = [c for c in tops if c != gcell]

        thresholds = sorted({births[c] for c in births})
        before_curves = cubical_persistent_cohomology_betti_f2(births, thresholds)
        new_births = {c: births[c] for c in rem}
        after_curves = cubical_persistent_cohomology_betti_f2(new_births, thresholds)

        new_state = state.snapshot()
        new_state.complex = CubicalComplex(top_cells=new_tops, name=state.complex.name)
        new_state.grades.pop(str(gcell), None)
        for h in inserted:
            new_state.grades.setdefault(h, state.grades.get(str(gcell), 0.0))
        cert = {
            "type": "FiltrationMapWitness",
            "pass": self.name,
            "contract": self.contract,
            "cell": str(gcell),
            "free_face": str(f),
            "inserted_horn": inserted,
            "size_before": state.size(),
            "size_after": new_state.size(),
            "dim_before": int(gcell.dimension),
            "dim_after": int(f.dimension),
            "cells_before_closure": len(births),
            "cells_after_closure": len(rem),
            "compression": 1.0 - (len(rem) / max(1, len(births))),
            "persistent_betti_before": before_curves,
            "persistent_betti_after": after_curves,
            "persistence_preserved": before_curves == after_curves,
            "weight_preserved": True,
            "L": 0,
            "U": new_state.size(),
        }
        new_state.log.append(cert)
        if before_curves != after_curves:
            return reject("persistent Betti curves changed")
        return PassResult(True, new_state, cert, "filtration-compatible horn")


class ShotgunCoveringCollapsePass(Pass):
    """Batch (simultaneous) covering-mode collapse -- EXPERIMENTAL, no optimality claim.

    Replaces several admissible cells by their free faces in one step when the faces'
    closures are pairwise disjoint.  The Loop 4 audit (docs/claim-ledger C9) found that
    batching can lose cover optimality even when every single step is admissible, so this
    pass is *not* in any default manager and its certificate carries
    ``optimality_claim = False``; contract ``Coverage`` only.
    """

    name = "ShotgunCoveringCollapse"
    contract = "Coverage"

    def __init__(self, max_batch: int = 8) -> None:
        self.max_batch = max_batch

    @staticmethod
    def _closure(cell: Any) -> set[str]:
        seen: set[str] = set()
        stack = [cell]
        while stack:
            c = stack.pop()
            if str(c) in seen:
                continue
            seen.add(str(c))
            stack.extend(c.faces())
        return seen

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes

        def reject(reason: str) -> PassResult:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, reason)

        if state.size() == 0:
            return reject("empty")
        cm = graded_table_from_cubical(state.complex, include_faces_down_to=0)
        present = set(state.cell_names())
        used: set[str] = set()
        pairs: list[tuple[Any, Any]] = []
        for col_j, faces in list_collapsible_primes(cm):
            cell = cm.col_cubes[col_j]
            if cell is None or str(cell) in state.relative:
                continue
            for face in faces:
                if str(face) in present or not cover_admissible_free_face(cm, col_j, face):
                    continue
                cl = self._closure(face)
                if cl & used:
                    continue
                used |= cl
                pairs.append((cell, face))
                break
            if len(pairs) >= self.max_batch:
                break
        if len(pairs) < 2:
            return reject("fewer than two independent admissible faces")
        swap = {str(c): f for c, f in pairs}
        new_tops = [swap.get(str(c), c) for c in state.complex.top_cells]
        new_state = state.snapshot()
        new_state.complex = CubicalComplex(top_cells=new_tops, name=state.complex.name)
        decode = dict(new_state.meta.get("decode", {}))
        for c, f in pairs:
            decode[str(f)] = decode.pop(str(c), str(c))
            g = new_state.grades.pop(str(c), None)
            if g is not None:
                new_state.grades.setdefault(str(f), g)
        new_state.meta["decode"] = decode
        cert = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "optimality_claim": False,
            "pairs": [{"cell": str(c), "inserted_face": str(f)} for c, f in pairs],
            "size_before": state.size(),
            "size_after": new_state.size(),
        }
        new_state.log.append(cert)
        return PassResult(True, new_state, cert, "batch face insertion")


def covering_collapse_closure(
    state: SynthesisState, max_steps: int = 256
) -> SynthesisState:
    """Apply CoveringAwareCollapse until no admissible free face remains."""
    from topospine.checkers.pass_trace import verify_pass_trace

    cur = state.snapshot()
    p = CoveringAwareCollapsePass()
    for _ in range(max_steps):
        res = p.try_apply(cur)
        if not res.accepted:
            break
        ok, why = verify_pass_trace(res.certificate, res.state, cur)
        if not ok:
            raise RuntimeError(f"CoveringAwareCollapse failed independent check: {why}")
        cur = res.state
    return cur


class FiltrationCompatibleCollapsePass(Pass):
    name = "FiltrationCompatibleCollapse"
    contract = "PersistentEquivalence"

    def try_apply(self, state: SynthesisState) -> PassResult:
        if not state.grades:
            # No filtration: defer to elementary
            return ElementaryCubicalCollapsePass().try_apply(state)
        coll = state.complex.collapsible_cells()
        for cell, faces in coll:
            if str(cell) in state.relative:
                continue
            face = faces[0]
            g_cell = state.grades.get(str(cell), 0.0)
            g_face = state.grades.get(str(face), g_cell)
            # Filtration compatibility: face appears no later than cell
            if g_face > g_cell + 1e-12:
                continue
            # Also: removing cell must not invert any remaining inclusion grades
            ok = True
            for other in state.complex.top_cells:
                if other == cell:
                    continue
                # If other is a face of cell in the complex sense, skip (rare for tops)
                go = state.grades.get(str(other), 0.0)
                if go < g_face - 1e-12 and str(other) == str(face):
                    ok = False
            if not ok:
                continue
            base = ElementaryCubicalCollapsePass().try_apply(state)
            if not base.accepted:
                continue
            cert = dict(base.certificate)
            cert["pass"] = self.name
            cert["contract"] = self.contract
            cert["type"] = "FiltrationMapWitness"
            cert["grade_cell"] = g_cell
            cert["grade_face"] = g_face
            base.state.log[-1] = cert
            return PassResult(True, base.state, cert, "filtration-compatible collapse")
        return PassResult(
            False,
            state,
            {"type": "PassTrace", "pass": self.name},
            "no filtration-compatible free face",
        )


class RelativeCollapsePass(Pass):
    name = "RelativeCollapse"
    contract = "RelativeEquivalence"

    def try_apply(self, state: SynthesisState) -> PassResult:
        """Collapse only cells outside A; never remove cells in relative subcomplex."""
        coll = state.complex.collapsible_cells()
        for cell, faces in coll:
            if str(cell) in state.relative:
                continue
            # Free face must not be required solely by A in a way that deletes A cells
            face = faces[0]
            if str(face) in state.relative and str(cell) not in state.relative:
                # collapsing cell outside A onto a face in A is OK for relative homology
                # of (K,A) only if we don't remove A; we don't remove face-as-top unless it was top
                pass
            # Build temporary state without relative block for elementary attempt
            tmp = state.snapshot()
            # Elementary pass blocks relative cells; this loop already skips them
            res = ElementaryCubicalCollapsePass().try_apply(tmp)
            if not res.accepted:
                continue
            # Ensure A cells still present
            remaining = set(res.state.cell_names())
            if not state.relative <= remaining | {str(faces[0])}:
                # If an A cell was removed, reject
                removed_a = state.relative - remaining
                if removed_a:
                    continue
            cert = dict(res.certificate)
            cert["pass"] = self.name
            cert["contract"] = self.contract
            cert["relative_preserved"] = sorted(state.relative)
            res.state.log[-1] = cert
            return PassResult(True, res.state, cert, "relative-safe collapse")
        return PassResult(
            False,
            state,
            {"type": "PassTrace", "pass": self.name},
            "no relative-safe collapse",
        )


def _cubical_graph(cx: CubicalComplex) -> tuple[int, list[tuple[int, int]]]:
    """Vertices and edges of the 1-skeleton.  Vertex ids are dense and local."""
    faces: dict[str, Any] = {}

    def add(cell: Any) -> None:
        key = str(cell)
        if key in faces:
            return
        faces[key] = cell
        for face in cell.faces():
            add(face)

    for cell in cx.top_cells:
        add(cell)
    verts = sorted(key for key, cell in faces.items() if cell.dimension == 0)
    index = {key: i for i, key in enumerate(verts)}
    edges: list[tuple[int, int]] = []
    for cell in faces.values():
        if cell.dimension != 1:
            continue
        ends = [index[str(face)] for face in cell.faces() if face.dimension == 0]
        if len(ends) == 2 and ends[0] != ends[1]:
            a, b = ends
            edges.append((min(a, b), max(a, b)))
    return len(verts), edges


class FlagEdgeCollapseAdapterPass(Pass):
    """GUDHI edge-collapse baseline on the cubical 1-skeleton.

    Runs ``SimplexTree.collapse_edges`` when GUDHI is installed and records
    edge counts and F2 Betti of the flag 2-skeleton before and after.  The
    synthesis state is never mutated: this is a baseline, not a rewrite.
    Graphs with more than ``max_vertices`` vertices are skipped and labelled.
    """

    name = "FlagEdgeCollapseAdapter"
    contract = "PersistentEquivalence"

    def __init__(self, max_vertices: int = 400, iterations: int = 4) -> None:
        self.max_vertices = max_vertices
        self.iterations = iterations

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.spines.gudhi_baseline import collapse_graph_edges, gudhi_available

        available = gudhi_available()
        cert: dict[str, Any] = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "gudhi_available": available,
            "action": "baseline_only_no_mutation",
            "size_before": state.size(),
            "size_after": state.size(),
        }
        if not available or state.size() == 0:
            return PassResult(False, state, cert, "adapter does not mutate (baseline)")
        n_verts, edges = _cubical_graph(state.complex)
        cert["vertices"] = n_verts
        cert["edges_before"] = len(edges)
        if n_verts == 0 or n_verts > self.max_vertices:
            cert["action"] = "skipped_size"
            return PassResult(False, state, cert, "adapter does not mutate (baseline)")
        stats = collapse_graph_edges(n_verts, edges, iterations=self.iterations)
        cert.update(
            {
                "action": "gudhi_edge_collapse_baseline",
                "edges_after": stats["edges_after"],
                "betti_before": stats["betti_before"],
                "betti_after": stats["betti_after"],
                "betti_preserved": stats["betti_preserved"],
            }
        )
        return PassResult(False, state, cert, "adapter does not mutate (baseline)")


class BoundedExactCorePass(Pass):
    name = "BoundedExactCore"
    contract = "CoverOptimality"

    def __init__(self, max_cols: int = 12, depth_limit: int = 24) -> None:
        self.max_cols = max_cols
        self.depth_limit = depth_limit

    def try_apply(self, state: SynthesisState) -> PassResult:
        if state.size() == 0:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, "empty")
        cm = graded_table_from_cubical(state.complex, include_faces_down_to=0)
        if cm.n_cols() > self.max_cols:
            return PassResult(
                False,
                state,
                {"type": "PassTrace", "pass": self.name, "ncols": cm.n_cols()},
                "residue too large",
            )
        aud = audit_collapse_branch(cm, name="bounded_core", depth_limit=self.depth_limit)
        # certified cover = plain B&B; collapse-branch only audited (C2 has n=5 counterexamples)
        cover, cost, stats = minimize_cover(cm.copy(), use_collapse=False, depth_limit=self.depth_limit)
        cert = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "audit": aud.as_dict(),
            "cover_indices": cover,
            "cost": cost,
            "collapse_used": aud.collapse_used,
            "collapse_branch_agrees": aud.col_cost == cost,
            "size_before": state.size(),
            "size_after": state.size(),  # exact core pass certifies; does not delete tops here
        }
        new_state = state.snapshot()
        new_state.meta["last_exact_cover"] = {
            "cols": [cm.cols[i] for i in cover],
            "cost": cost,
        }
        new_state.log.append(cert)
        # Accepted as certification even without mutation
        return PassResult(True, new_state, cert, "exact core certified")


class PairCollapsePass(Pass):
    """One elementary collapse of a free face and its coface.  Not in the default manager.

    Unlike ``ElementaryCubicalCollapsePass`` (which drops a top cell and every face
    exclusive to it), this keeps the other faces of the coface.  The certificate
    asks the checker to recompute real Betti numbers.
    """

    name = "PairCollapse"
    contract = "ElementaryCollapse"

    def try_apply(self, state: SynthesisState) -> PassResult:
        from topospine.core.laplacian import cubical_betti_real, cubical_spectrum, pair_collapse_cubical

        collapsed = pair_collapse_cubical(state.complex)
        if collapsed is None:
            return PassResult(False, state, {"type": "PassTrace", "pass": self.name}, "no free face")
        before = cubical_spectrum(state.complex)
        after = cubical_spectrum(collapsed)
        new_state = state.snapshot()
        new_state.complex = collapsed
        cert = {
            "type": "PassTrace",
            "pass": self.name,
            "contract": self.contract,
            "require_real_betti": True,
            "real_betti_before": before["betti_real"],
            "real_betti_after": after["betti_real"],
            "spectral_gap_before": before["spectral_gaps"],
            "spectral_gap_after": after["spectral_gaps"],
            "cells_before": before["n_cells"],
            "cells_after": after["n_cells"],
            "size_before": state.size(),
            "size_after": collapsed.size() if hasattr(collapsed, "size") else len(collapsed.top_cells),
        }
        # size_after must match new_state.size(); CubicalComplex has no size(), SynthesisState does
        cert["size_after"] = new_state.size()
        new_state.log.append(cert)
        return PassResult(True, new_state, cert, "pair collapse")
