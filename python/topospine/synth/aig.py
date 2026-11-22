"""Minimal And-Inverter Graph (AIG) and factor-diagram IR.

Literals are AIGER-style integers: ``2*node + neg``.  Node 0 is constant FALSE
(literal 0 = false, literal 1 = true), nodes ``1..n`` are primary inputs, nodes
above are two-input ANDs.  Structural hashing and constant folding are applied
on construction, so shared sub-expressions in a factored form are shared gates.

Minterm index convention: variable ``i`` is bit ``n-1-i`` of the index, i.e. the
cube string ``"101"`` is minterm 5 (matches ``BooleanCube`` string order).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from topospine.core.cubes import BooleanCube

FALSE = 0
TRUE = 1


def lit_not(lit: int) -> int:
    return lit ^ 1


@dataclass
class AIG:
    n_inputs: int
    ands: list[tuple[int, int]] = field(default_factory=list)  # node n+1+k -> (lit, lit)
    _strash: dict[tuple[int, int], int] = field(default_factory=dict, repr=False)

    def input_lit(self, i: int) -> int:
        return 2 * (1 + i)

    def and_(self, a: int, b: int) -> int:
        if a == FALSE or b == FALSE:
            return FALSE
        if a == TRUE:
            return b
        if b == TRUE:
            return a
        if a == b:
            return a
        if a == lit_not(b):
            return FALSE
        if a > b:
            a, b = b, a
        key = (a, b)
        hit = self._strash.get(key)
        if hit is not None:
            return hit
        node = self.n_inputs + 1 + len(self.ands)
        self.ands.append(key)
        lit = 2 * node
        self._strash[key] = lit
        return lit

    def or_(self, a: int, b: int) -> int:
        return lit_not(self.and_(lit_not(a), lit_not(b)))

    def and_many(self, lits: Sequence[int]) -> int:
        return self._balanced(list(lits), self.and_, TRUE)

    def or_many(self, lits: Sequence[int]) -> int:
        return self._balanced(list(lits), self.or_, FALSE)

    @staticmethod
    def _balanced(lits: list[int], op, identity: int) -> int:  # type: ignore[no-untyped-def]
        if not lits:
            return identity
        while len(lits) > 1:
            nxt = [op(lits[i], lits[i + 1]) for i in range(0, len(lits) - 1, 2)]
            if len(lits) % 2:
                nxt.append(lits[-1])
            lits = nxt
        return lits[0]

    # -- analysis -------------------------------------------------------
    def reachable(self, outputs: Iterable[int]) -> set[int]:
        seen: set[int] = set()
        stack = [o >> 1 for o in outputs]
        while stack:
            node = stack.pop()
            if node in seen or node <= self.n_inputs:
                continue
            seen.add(node)
            a, b = self.ands[node - self.n_inputs - 1]
            stack.extend((a >> 1, b >> 1))
        return seen

    def gate_count(self, outputs: Iterable[int]) -> int:
        """Number of AND gates reachable from ``outputs`` (dangling gates ignored)."""
        return len(self.reachable(outputs))

    def depth(self, outputs: Iterable[int]) -> int:
        memo: dict[int, int] = {}

        def d(node: int) -> int:
            if node <= self.n_inputs:
                return 0
            if node in memo:
                return memo[node]
            a, b = self.ands[node - self.n_inputs - 1]
            memo[node] = 1 + max(d(a >> 1), d(b >> 1))
            return memo[node]

        return max((d(o >> 1) for o in outputs), default=0)

    def evaluate(self, lit: int, assignment: Sequence[int]) -> int:
        """Direct recursive evaluation (independent of bit-parallel simulation)."""
        memo: dict[int, int] = {}

        def val(node: int) -> int:
            if node == 0:
                return 0
            if node <= self.n_inputs:
                return int(assignment[node - 1])
            if node in memo:
                return memo[node]
            a, b = self.ands[node - self.n_inputs - 1]
            memo[node] = (val(a >> 1) ^ (a & 1)) & (val(b >> 1) ^ (b & 1))
            return memo[node]

        return val(lit >> 1) ^ (lit & 1)

    def truth_table(self, lit: int) -> int:
        """Bit-parallel truth table as an int; bit m = value on minterm m."""
        n = self.n_inputs
        full = (1 << (1 << n)) - 1
        tt: dict[int, int] = {0: 0}
        for i in range(n):
            mask = 0
            for m in range(1 << n):
                if (m >> (n - 1 - i)) & 1:
                    mask |= 1 << m
            tt[1 + i] = mask

        def node_tt(node: int) -> int:
            if node in tt:
                return tt[node]
            a, b = self.ands[node - n - 1]
            ta = node_tt(a >> 1) ^ (full if a & 1 else 0)
            tb = node_tt(b >> 1) ^ (full if b & 1 else 0)
            tt[node] = ta & tb
            return tt[node]

        t = node_tt(lit >> 1)
        return t ^ (full if lit & 1 else 0)

    # -- export ---------------------------------------------------------
    def to_blif(self, out_lit: int, model: str = "topospine") -> str:
        """Write a BLIF netlist (AND gates as .names) for external tools such as ABC."""
        n = self.n_inputs
        lines = [f".model {model}", ".inputs " + " ".join(f"x{i}" for i in range(n)), ".outputs f"]

        def name(node: int) -> str:
            return f"x{node - 1}" if 1 <= node <= n else f"n{node}"

        used = sorted(self.reachable([out_lit]))
        for node in used:
            a, b = self.ands[node - n - 1]
            lines.append(f".names {name(a >> 1)} {name(b >> 1)} {name(node)}")
            lines.append(f"{'0' if a & 1 else '1'}{'0' if b & 1 else '1'} 1")
        root = out_lit >> 1
        if root == 0:
            lines.append(".names f")
            if out_lit & 1:
                lines.append("1")
        else:
            lines.append(f".names {name(root)} f")
            lines.append(f"{'0' if out_lit & 1 else '1'} 1")
        lines.append(".end")
        return "\n".join(lines) + "\n"


# --- SOP / factored forms ----------------------------------------------------

Expr = tuple  # ("const", 0|1) | ("lit", var, val) | ("and", [Expr]) | ("or", [Expr])


def sop_to_aig(n: int, cubes: Sequence[BooleanCube]) -> tuple[AIG, int]:
    aig = AIG(n)
    terms = []
    for c in cubes:
        lits = [
            aig.input_lit(i) ^ (1 if b == 0 else 0)
            for i, b in enumerate(c.bits)
            if b is not None
        ]
        terms.append(aig.and_many(lits))
    return aig, aig.or_many(terms)


def minterm_sop(n: int, on: Iterable[int]) -> list[BooleanCube]:
    return [
        BooleanCube(tuple((m >> (n - 1 - i)) & 1 for i in range(n))) for m in sorted(on)
    ]


def quick_factor(cubes: Sequence[BooleanCube]) -> Expr:
    """Algebraic quick-factor: repeatedly pull out the most frequent literal."""
    cubes = list(dict.fromkeys(cubes))
    if not cubes:
        return ("const", 0)
    if any(all(b is None for b in c.bits) for c in cubes):
        return ("const", 1)
    if len(cubes) == 1:
        return _cube_expr(cubes[0])
    counts: dict[tuple[int, int], int] = {}
    for c in cubes:
        for i, b in enumerate(c.bits):
            if b is not None:
                counts[(i, b)] = counts.get((i, b), 0) + 1
    best = max(counts.items(), key=lambda kv: (kv[1], -kv[0][0], kv[0][1]), default=None)
    if best is None or best[1] < 2:
        return ("or", [_cube_expr(c) for c in cubes])
    (var, val), _ = best
    with_l, without = [], []
    for c in cubes:
        if c.bits[var] == val:
            bits = list(c.bits)
            bits[var] = None
            with_l.append(BooleanCube(tuple(bits)))
        else:
            without.append(c)
    head = ("and", [("lit", var, val), quick_factor(with_l)])
    if not without:
        return head
    return ("or", [head, quick_factor(without)])


def _cube_expr(c: BooleanCube) -> Expr:
    lits = [("lit", i, b) for i, b in enumerate(c.bits) if b is not None]
    if not lits:
        return ("const", 1)
    return lits[0] if len(lits) == 1 else ("and", lits)


def expr_to_aig(aig: AIG, e: Expr) -> int:
    tag = e[0]
    if tag == "const":
        return TRUE if e[1] else FALSE
    if tag == "lit":
        return aig.input_lit(e[1]) ^ (1 if e[2] == 0 else 0)
    parts = [expr_to_aig(aig, x) for x in e[1]]
    return aig.and_many(parts) if tag == "and" else aig.or_many(parts)


def expr_literal_count(e: Expr) -> int:
    if e[0] == "const":
        return 0
    if e[0] == "lit":
        return 1
    return sum(expr_literal_count(x) for x in e[1])


def shared_factored_gates(n: int, cube_lists: Sequence[Sequence[BooleanCube]]) -> dict:
    """Gate counts of factored AIGs, separate versus one structurally hashed graph.

    Sharing is only what algebraic factoring plus the AND hash happen to reuse.
    It is not a multi-level optimizer and it does not see the original netlist.
    """
    separate = 0
    aig = AIG(n)
    outs: list[int] = []
    for cubes in cube_lists:
        one, out, _expr = factored_aig(n, cubes)
        separate += one.gate_count([out])
        outs.append(expr_to_aig(aig, quick_factor(cubes)))
    return {
        "n_outputs": len(cube_lists),
        "gates_separate": separate,
        "gates_shared": aig.gate_count(outs),
        "ands_in_shared_graph": len(aig.ands),
    }


def factored_aig(n: int, cubes: Sequence[BooleanCube]) -> tuple[AIG, int, Expr]:
    aig = AIG(n)
    e = quick_factor(cubes)
    return aig, expr_to_aig(aig, e), e
