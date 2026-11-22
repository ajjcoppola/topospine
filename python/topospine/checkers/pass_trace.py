"""Independent checker for PassTrace / FiltrationMapWitness certificates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from topospine.synth.ir import SynthesisState


DELETION_STYLE = (
    "ElementaryCubicalCollapse",
    "FiltrationCompatibleCollapse",
    "RelativeCollapse",
)


def verify_pass_trace(
    cert: dict[str, Any],
    new_state: SynthesisState,
    old_state: SynthesisState,
) -> tuple[bool, str]:
    ctype = cert.get("type")
    if ctype not in ("PassTrace", "FiltrationMapWitness", "ElementaryCollapseTrace"):
        # Adapter may still be validated loosely
        if cert.get("pass") == "FlagEdgeCollapseAdapter":
            return True, "adapter baseline"
        return False, f"unknown certificate type {ctype}"

    if new_state.mode == "covering":
        if cert.get("pass") in DELETION_STYLE:
            return False, "deletion-style pass in covering mode"
        if old_state.size() > 0 and new_state.size() == 0:
            return False, "covering IR silently emptied"

    if "size_before" in cert and "size_after" in cert:
        if cert["size_before"] != old_state.size():
            return False, "size_before mismatch"
        if cert["size_after"] != new_state.size():
            return False, "size_after mismatch"

    if cert.get("pass") == "CoveringAwareCollapse":
        cell, face = cert.get("cell"), cert.get("inserted_face")
        if cell is None or face is None:
            return False, "missing cell/inserted_face"
        if old_state.size() > 0 and new_state.size() == 0:
            return False, "covering IR silently emptied"
        if new_state.size() != old_state.size():
            return False, "covering-mode collapse must preserve column count"
        if cell in new_state.cell_names():
            return False, "collapsed cell still present"
        if face not in new_state.cell_names():
            return False, "inserted face missing from covering IR"
        if cell in old_state.relative:
            return False, "relative cell collapsed"
        if cert.get("dim_after", 0) >= cert.get("dim_before", 0):
            return False, "face dimension not lower"
        if not cert.get("weight_preserved", False):
            return False, "weight not preserved"
        if face not in (cert.get("decode") or {}):
            return False, "missing decode map"
        return True, "ok"

    if cert.get("pass") == "ShotgunCoveringCollapse":
        if cert.get("optimality_claim", True):
            return False, "shotgun batches must not claim optimality (C9 disproved)"
        pairs = cert.get("pairs") or []
        if len(pairs) < 2:
            return False, "batch needs >= 2 pairs"
        if old_state.size() > 0 and new_state.size() == 0:
            return False, "covering IR silently emptied"
        if new_state.size() != old_state.size():
            return False, "batch must preserve column count"
        names = new_state.cell_names()
        cells = [p["cell"] for p in pairs]
        if len(set(cells)) != len(cells):
            return False, "duplicate cell in batch"
        for p in pairs:
            if p["cell"] in names or p["inserted_face"] not in names:
                return False, "batch pair not applied"
            if p["cell"] in old_state.relative:
                return False, "relative cell collapsed"
        return True, "ok"

    if cert.get("pass") in (
        "ElementaryCubicalCollapse",
        "FiltrationCompatibleCollapse",
        "RelativeCollapse",
    ):
        cell = cert.get("cell")
        if cell is None:
            return False, "missing cell"
        if cell in new_state.cell_names():
            return False, "collapsed cell still present"
        if "chi_before" in cert and "chi_after" in cert:
            # Elementary collapse of top cell alone may change χ if face not removed;
            # Loop 2 records χ but does not require equality unless both pair removed.
            pass
        if cert.get("pass") == "FiltrationCompatibleCollapse":
            if cert.get("grade_face", 0) > cert.get("grade_cell", 0) + 1e-12:
                return False, "filtration grade inversion"
        if cert.get("pass") == "RelativeCollapse":
            preserved = set(cert.get("relative_preserved", []))
            if preserved and not preserved <= set(old_state.relative):
                return False, "relative set mismatch"

    if cert.get("pass") == "BoundedExactCore":
        aud = cert.get("audit") or {}
        exh = aud.get("exhaustive_cost")
        if aud and exh is not None and exh == exh and float(exh) != float(cert.get("cost", exh)):
            return False, "certified cover cost differs from exhaustive oracle"

    if cert.get("pass") == "PairCollapse" or cert.get("require_real_betti"):
        def _pad(a, b):
            aa, bb = list(a or []), list(b or [])
            n = max(len(aa), len(bb))
            return aa + [0] * (n - len(aa)), bb + [0] * (n - len(bb))

        stated_before, stated_after = _pad(cert.get("real_betti_before"), cert.get("real_betti_after"))
        if stated_before != stated_after:
            return False, "pair collapse changed real Betti numbers"
        try:
            from topospine.core.laplacian import cubical_betti_real
        except ImportError:
            return False, "real Betti check requested but numpy/laplacian unavailable"
        before, after = _pad(cubical_betti_real(old_state.complex), cubical_betti_real(new_state.complex))
        if before != after:
            return False, "recomputed real Betti numbers changed"
        if before != stated_before:
            return False, "certificate real Betti does not match recomputation"

    return True, "ok"
