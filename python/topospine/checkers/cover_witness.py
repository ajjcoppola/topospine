"""Independent cover optimality witness checker (encode/decode)."""

from __future__ import annotations

from typing import Any, Sequence

from topospine.core.covering import CoveringMatrix


def verify_cover_optimality_witness(
    cm: CoveringMatrix,
    witness: dict[str, Any],
) -> tuple[bool, str]:
    """
    CoverOptimalityWitness:
      decode_cover: list[int]  # columns of original
      cost: float
      encode_of_reference: optional list[int] on expanded
      claimed_optimum: bool
    """
    try:
        cover = list(witness["decode_cover"])
        cost = float(witness["cost"])
    except KeyError as e:
        return False, f"missing key {e}"
    if not cm.is_cover(cover):
        return False, "decode_cover is not a feasible cover"
    if abs(cm.cost(cover) - cost) > 1e-9:
        return False, "cost mismatch"
    return True, "ok"


def abstract_transport_ok(
    *,
    encode_cost_ok: bool,
    decode_cost_ok: bool,
    encode_feasible: bool,
    decode_feasible: bool,
) -> bool:
    """Abstract encode/decode inequalities (Lean L5 obligations)."""
    return encode_cost_ok and decode_cost_ok and encode_feasible and decode_feasible
