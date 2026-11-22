"""Independent checker for LogicPassTrace certificates.

Re-derives correctness by direct evaluation of the realized AIG on every care
minterm (no bit-parallel simulation, no minimizer code).
"""

from __future__ import annotations

from typing import Any

from topospine.core.cubes import parse_boolean_cube


def verify_logic_trace(cert: dict[str, Any], state: Any) -> tuple[bool, str]:
    if cert.get("type") != "LogicPassTrace":
        return False, f"unknown certificate type {cert.get('type')}"
    if "on" not in cert:
        return False, "missing on-set"
    n = cert["n"]
    on = set(cert["on"])
    dc = set(cert["dc"])
    if on != set(state.on) or dc != set(state.dc):
        return False, "specification mismatch"
    aig = state.aig
    if aig is None:
        return False, "no AIG"
    for m in range(1 << n):
        assign = [(m >> (n - 1 - i)) & 1 for i in range(n)]
        v = aig.evaluate(state.out, assign)
        if m in on and v != 1:
            return False, f"ON minterm {m} evaluates to 0"
        if m not in on and m not in dc and v != 0:
            return False, f"OFF minterm {m} evaluates to 1"
    if "gates_after" in cert and cert["gates_after"] != aig.gate_count([state.out]):
        return False, "gates_after mismatch"
    if cert.get("pass") == "DontCareSpine":
        cubes = [parse_boolean_cube(s) for s in cert.get("cubes", [])]
        # every ON minterm must lie in a cube; every cube minterm must be ON or DC
        for m in on:
            bits = tuple((m >> (n - 1 - i)) & 1 for i in range(n))
            if not any(all(b is None or b == x for b, x in zip(c.bits, bits)) for c in cubes):
                return False, f"ON minterm {m} uncovered by certified cubes"
        for c in cubes:
            for v in c.vertices():
                idx = sum(b << (n - 1 - i) for i, b in enumerate(v))
                if idx not in on and idx not in dc:
                    return False, f"cube {c} hits OFF minterm {idx}"
    return True, "ok"
