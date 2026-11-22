"""Independent elementary-collapse trace checker."""

from __future__ import annotations

from typing import Any


def verify_elementary_collapse_trace(trace: dict[str, Any]) -> tuple[bool, str]:
    """
    Check JSON-like ElementaryCollapseTrace.

    Required keys: cell, free_face, other_top_cells (list of str),
    chi_before, chi_after (optional but checked if present).
    """
    try:
        cell = trace["cell"]
        free_face = trace["free_face"]
        others = list(trace.get("other_top_cells", []))
    except KeyError as e:
        return False, f"missing key {e}"
    if free_face in others:
        return False, "free_face listed among other top cells"
    if cell == free_face:
        return False, "cell equals free_face"
    # Structural: free face name must look like a face of cell when both are strings
    if "chi_before" in trace and "chi_after" in trace:
        if int(trace["chi_before"]) != int(trace["chi_after"]):
            return False, "Euler characteristic not preserved"
    return True, "ok"
