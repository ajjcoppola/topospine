"""2D grid complexes — Layer 1 *geometric sandbox* (not Layer-0 cyclic cores).

See ``docs/definitions-cube-array.md``.  An array-of-cubes absolute-min problem
has minterm rows; this module builds Filled/Hollow/Absent unit-square complexes
and covering tables whose rows are **vertices** or **faces** of the grid.  A
residual after ``reduce_to_cyclic_core`` on those tables is a
**grid-surrogate core**, not a cyclic core in Alan's Layer-0 sense.

Every unit square of an ``a x b`` grid is filled (top cell of dim 2), hollow
(boundary edges only) or absent.  Vertex-row covering: rows = vertices; columns =
top cells; unit weights.  Face-row covering: rows = all proper faces.

The free-face transform ``T`` replaces a filled square ``p`` by a free face ``f``.
Decode swaps ``f`` back to ``p``.  Put-back then drops every chosen cube the rest of
the cover already covers (minimum sub-cover).  The far side of ``p`` is
``F_p = (V(p) ∩ R) \\ V(f)``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from itertools import combinations, product
from typing import Iterable, Literal, Sequence

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core

FILLED, HOLLOW, ABSENT = "F", "H", "."
CellState = Literal["F", "H", "."]


# ----------------------------------------------------------------- geometry
def square_verts(i: int, j: int) -> list[tuple[int, int]]:
    return [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]


def square_edges(i: int, j: int) -> list[tuple]:
    return [("h", i, j), ("v", i + 1, j), ("h", i, j + 1), ("v", i, j)]


def edge_verts(e: tuple) -> tuple[tuple[int, int], tuple[int, int]]:
    kind, x, y = e
    return ((x, y), (x + 1, y)) if kind == "h" else ((x, y), (x, y + 1))


def faces_of(cell: tuple) -> list[tuple]:
    if cell[0] == "sq":
        _, i, j = cell
        return [("ed",) + e for e in square_edges(i, j)]
    if cell[0] == "ed":
        a, b = edge_verts(cell[1:])
        return [("vx",) + a, ("vx",) + b]
    return []


def contains(big: tuple, small: tuple) -> bool:
    if big == small:
        return True
    if big[0] == "sq":
        _, i, j = big
        if small[0] == "ed":
            return small[1:] in square_edges(i, j)
        if small[0] == "vx":
            return small[1:] in square_verts(i, j)
        return False
    if big[0] == "ed" and small[0] == "vx":
        return small[1:] in edge_verts(big[1:])
    return False


def cell_verts(cell: tuple) -> frozenset[tuple[int, int]]:
    if cell[0] == "sq":
        return frozenset(square_verts(cell[1], cell[2]))
    if cell[0] == "ed":
        return frozenset(edge_verts(cell[1:]))
    return frozenset([cell[1:]])


def free_faces(cell: tuple, others: Sequence[tuple]) -> list[tuple]:
    return [f for f in faces_of(cell) if not any(contains(o, f) for o in others)]


def opposite_edge(p_cell: tuple, f: tuple) -> tuple:
    edges = faces_of(p_cell)
    k = edges.index(f)
    return edges[(k + 2) % 4]


# ----------------------------------------------------------------- build
@dataclass(frozen=True)
class GridColumn:
    name: str
    dim: int
    verts: frozenset[tuple[int, int]]
    cell: tuple


@dataclass
class GridComplex:
    a: int
    b: int
    config: dict[tuple[int, int], CellState]
    columns: list[GridColumn]
    vertices: list[tuple[int, int]]

    def draw(self) -> str:
        lines = []
        for j in reversed(range(self.b)):
            lines.append(" ".join(self.config[(i, j)] for i in range(self.a)))
        return "\n".join(lines)


def build_grid(config: dict[tuple[int, int], CellState], a: int, b: int) -> GridComplex:
    filled = [(i, j) for (i, j), s in config.items() if s == FILLED]
    hollow = [(i, j) for (i, j), s in config.items() if s == HOLLOW]
    filled_edges: set[tuple] = set()
    for i, j in filled:
        filled_edges |= set(square_edges(i, j))
    cols: list[GridColumn] = []
    for i, j in filled:
        v = frozenset(square_verts(i, j))
        cols.append(GridColumn(f"S{i}{j}", 2, v, ("sq", i, j)))
    top_edges: set[tuple] = set()
    for i, j in hollow:
        for e in square_edges(i, j):
            if e not in filled_edges:
                top_edges.add(e)
    for e in sorted(top_edges):
        cols.append(GridColumn(f"E{e[0]}{e[1]}{e[2]}", 1, frozenset(edge_verts(e)), ("ed",) + e))
    verts = sorted({v for c in cols for v in c.verts})
    return GridComplex(a=a, b=b, config=dict(config), columns=cols, vertices=verts)


def all_configs(a: int, b: int) -> Iterable[dict[tuple[int, int], CellState]]:
    cells = [(i, j) for i in range(a) for j in range(b)]
    for states in product((FILLED, HOLLOW, ABSENT), repeat=len(cells)):
        if FILLED not in states:
            continue
        yield dict(zip(cells, states))


# ----------------------------------------------------------------- covering tables
def vertex_row_table(g: GridComplex) -> CoveringMatrix:
    rows = [str(v) for v in g.vertices]
    cols = [c.name for c in g.columns]
    matrix = [[v in c.verts for c in g.columns] for v in g.vertices]
    return CoveringMatrix(rows=rows, cols=cols, matrix=matrix, weights=[1.0] * len(cols))


def face_row_table(g: GridComplex) -> CoveringMatrix:
    tops = [c.cell for c in g.columns]
    faces: set[tuple] = set()
    for t in tops:
        for f in faces_of(t):
            faces.add(f)
            for ff in faces_of(f):
                faces.add(ff)
    faces -= set(tops)
    rows_cells = sorted(faces, key=str)
    matrix = [[contains(t, r) for t in tops] for r in rows_cells]
    return CoveringMatrix(
        rows=[str(r) for r in rows_cells],
        cols=[c.name for c in g.columns],
        matrix=matrix,
        weights=[1.0] * len(g.columns),
    )


# ----------------------------------------------------------------- bitmask exact cover
def exact_min_cost(row_masks: list[int], n_cols: int, universe: int) -> tuple[float, list[int]]:
    """Exact unit-cost cover.  Try small-cardinality search first; else bit-DP on rows."""
    if universe == 0:
        return 0.0, []
    bits = [i for i in range(universe.bit_length()) if universe & (1 << i)]
    r = len(bits)
    # Prefer DP when the state space is smaller than a mid-size combination sweep
    use_dp_first = r <= 18 or n_cols > 14
    if not use_dp_first:
        for k in range(1, min(n_cols, 8) + 1):
            for combo in combinations(range(n_cols), k):
                cov = 0
                for j in combo:
                    cov |= row_masks[j]
                if cov & universe == universe:
                    return float(k), list(combo)
    if r <= 22 and n_cols <= 64:
        remap = {b: i for i, b in enumerate(bits)}
        full = (1 << r) - 1

        def pack(m: int) -> int:
            out = 0
            for b, i in remap.items():
                if m & (1 << b):
                    out |= 1 << i
            return out

        packed = [pack(m) for m in row_masks]
        inf = n_cols + 1
        best = [inf] * (1 << r)
        prev: list[tuple[int, int]] = [(-1, -1)] * (1 << r)
        best[0] = 0
        for state in range(1 << r):
            cur = best[state]
            if cur >= inf:
                continue
            for j, m in enumerate(packed):
                nxt = state | m
                if cur + 1 < best[nxt]:
                    best[nxt] = cur + 1
                    prev[nxt] = (state, j)
        if best[full] >= inf:
            return float("inf"), []
        pick: list[int] = []
        state = full
        while state:
            pstate, j = prev[state]
            pick.append(j)
            state = pstate
        pick.reverse()
        return float(len(pick)), pick
    for k in range(9, n_cols + 1):
        for combo in combinations(range(n_cols), k):
            cov = 0
            for j in combo:
                cov |= row_masks[j]
            if cov & universe == universe:
                return float(k), list(combo)
    return float("inf"), []


def min_subcover_masks(universe: int, chosen: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Smallest sub-family of chosen (name, mask) pairs still covering universe."""
    for k in range(0, len(chosen) + 1):
        for combo in combinations(chosen, k):
            cov = 0
            for _, m in combo:
                cov |= m
            if cov & universe == universe:
                return list(combo)
    return list(chosen)


def greedy_reduce_masks(universe: int, chosen: list[tuple[str, int]]) -> list[tuple[str, int]]:
    keep = list(chosen)
    for item in list(keep):
        trial = [x for x in keep if x is not item]
        cov = 0
        for _, m in trial:
            cov |= m
        if cov & universe == universe:
            keep = trial
    return keep


# ----------------------------------------------------------------- grid-surrogate core + transform
@dataclass
class CoreInstance:
    """Vertex-row residual after ``reduce_to_cyclic_core`` on a grid table.

    This is a *grid-surrogate core* (Layer 1), not a Layer-0 cyclic core of a
    minterm×cube array.  See ``docs/definitions-cube-array.md``.
    """

    grid: GridComplex
    core_cols: list[GridColumn]
    core_rows: frozenset[tuple[int, int]]
    essentials: list[str]
    row_index: dict[tuple[int, int], int]
    col_masks: list[int]
    universe: int


def to_core(g: GridComplex) -> CoreInstance | None:
    """Reduce the vertex-row table; return a grid-surrogate core or None if empty."""
    cm = vertex_row_table(g)
    sub, _, ess = reduce_to_cyclic_core(cm.copy())
    if sub.n_rows() == 0:
        return None
    by = {c.name: c for c in g.columns}
    core_cols = [by[n] for n in sub.cols]
    core_rows = frozenset(ast.literal_eval(r) for r in sub.rows)
    row_index = {v: i for i, v in enumerate(sorted(core_rows))}
    universe = (1 << len(core_rows)) - 1
    col_masks = []
    for c in core_cols:
        m = 0
        for v in c.verts & core_rows:
            m |= 1 << row_index[v]
        col_masks.append(m)
    return CoreInstance(g, core_cols, core_rows, ess, row_index, col_masks, universe)


def far_rows(p: GridColumn, f: tuple, core_rows: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return (p.verts & core_rows) - cell_verts(f)


def collapsible_pairs(core: CoreInstance) -> list[tuple[GridColumn, tuple]]:
    out: list[tuple[GridColumn, tuple]] = []
    for p in core.core_cols:
        if p.dim != 2:
            continue
        others = [o.cell for o in core.core_cols if o is not p]
        for f in free_faces(p.cell, others):
            out.append((p, f))
    return out


@dataclass
class TransformResult:
    opt: float
    c_exp: float
    c_in: float
    decoded_raw: float
    decoded_putback: float
    agrees: bool
    far_empty: bool
    far_coverable_without_p: bool
    p_name: str
    free_face: tuple
    grid_draw: str


def apply_transform(core: CoreInstance, p: GridColumn, f: tuple) -> TransformResult:
    """Replace p by f, solve, decode+put-back; also record C_in and far-side facts."""
    idx_p = core.core_cols.index(p)
    others = [c for k, c in enumerate(core.core_cols) if k != idx_p]
    other_masks = [core.col_masks[k] for k in range(len(core.core_cols)) if k != idx_p]
    f_mask = 0
    for v in cell_verts(f) & core.core_rows:
        f_mask |= 1 << core.row_index[v]
    exp_masks = other_masks + [f_mask]
    exp_names = [c.name for c in others] + ["f"]
    opt, _ = exact_min_cost(core.col_masks, len(core.col_masks), core.universe)
    c_exp, pick = exact_min_cost(exp_masks, len(exp_masks), core.universe)
    # C_in: force p
    rest = 0
    for v in core.core_rows - p.verts:
        rest |= 1 << core.row_index[v]
    if rest == 0:
        c_in = 1.0
    else:
        c_in = 1.0 + exact_min_cost(other_masks, len(other_masks), rest)[0]
    chosen = [(exp_names[k], exp_masks[k]) for k in pick]
    if any(n == "f" for n, _ in chosen):
        back = [(n, m) for n, m in chosen if n != "f"] + [(p.name, core.col_masks[idx_p])]
    else:
        back = chosen
    raw = float(len(back))
    put = float(len(min_subcover_masks(core.universe, back)))
    F = far_rows(p, f, core.core_rows)
    far_ok = far_side_condition(core, p, f, opt)
    return TransformResult(
        opt=opt,
        c_exp=c_exp,
        c_in=c_in,
        decoded_raw=raw,
        decoded_putback=put,
        agrees=put == opt,
        far_empty=len(F) == 0,
        far_coverable_without_p=far_ok,
        p_name=p.name,
        free_face=f,
        grid_draw=core.grid.draw(),
    )


def far_side_condition(core: CoreInstance, p: GridColumn, f: tuple, opt: float) -> bool:
    """True iff some optimal cover of P excludes p, or covers F_p without p.

    Equivalently: exists an optimal cover S with either p ∉ S, or (S \\ {p}) ⊇ F_p.
    """
    idx_p = core.core_cols.index(p)
    others_masks = [core.col_masks[k] for k in range(len(core.core_cols)) if k != idx_p]
    F = far_rows(p, f, core.core_rows)
    far_mask = 0
    for v in F:
        far_mask |= 1 << core.row_index[v]
    c_out, _ = exact_min_cost(others_masks, len(others_masks), core.universe)
    if c_out == opt:
        return True
    if far_mask == 0:
        return True
    # Others must cover every row p does not, and also all of F_p.
    p_mask = core.col_masks[idx_p]
    need = (core.universe & ~p_mask) | far_mask
    c_rest, _ = exact_min_cost(others_masks, len(others_masks), need)
    return c_rest <= opt - 1


def characterization_holds(core: CoreInstance, p: GridColumn, f: tuple, res: TransformResult) -> bool:
    """opt(P') == opt(P)  iff  the far-side condition holds."""
    predicted = far_side_condition(core, p, f, res.opt)
    actual = res.c_exp == res.opt
    return predicted == actual


# ----------------------------------------------------------------- window profile check
def window_radius1_cells(p: GridColumn, a: int, b: int) -> list[tuple[int, int]]:
    """Squares within Chebyshev distance 1 of p's square."""
    _, i, j = p.cell
    out = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = i + di, j + dj
            if 0 <= ii < a and 0 <= jj < b:
                out.append((ii, jj))
    return out


def window_profile_agrees(core: CoreInstance, p: GridColumn, f: tuple, radius: int = 1) -> bool:
    """Local check: for every coverage pattern of rows outside the window by external columns,
    the local optimum with f equals the local optimum with p.  Sufficient by construction.
    """
    a, b = core.grid.a, core.grid.b
    if radius == 1:
        win_sq = set(window_radius1_cells(p, a, b))
    else:
        _, i0, j0 = p.cell
        win_sq = {
            (i, j)
            for i in range(a)
            for j in range(b)
            if max(abs(i - i0), abs(j - j0)) <= radius
        }
    win_verts: set[tuple[int, int]] = set()
    for i, j in win_sq:
        win_verts |= set(square_verts(i, j))
    win_rows = frozenset(win_verts & core.core_rows)
    if not win_rows:
        return True
    boundary = set()
    for v in win_rows:
        # a boundary row is also in some column outside the window
        for c in core.core_cols:
            if c.name == p.name:
                continue
            if c.dim == 2:
                _, ci, cj = c.cell
                if (ci, cj) not in win_sq and v in c.verts:
                    boundary.add(v)
            elif c.dim == 1 and v in c.verts:
                # edge columns: treat as external if not entirely in window
                if not c.verts <= win_verts:
                    boundary.add(v)
    # External columns: those not p and not a filled square inside the window
    ext = []
    for c in core.core_cols:
        if c.name == p.name:
            continue
        if c.dim == 2:
            _, ci, cj = c.cell
            if (ci, cj) in win_sq:
                continue
        ext.append(c)
    # Local columns with p: p plus filled squares / edges inside window (except p)
    local_with_p = [p]
    local_with_f_cells = []
    for c in core.core_cols:
        if c.name == p.name:
            continue
        if c.dim == 2:
            _, ci, cj = c.cell
            if (ci, cj) in win_sq:
                local_with_p.append(c)
                local_with_f_cells.append(c)
        elif c.dim == 1 and c.verts <= win_verts:
            local_with_p.append(c)
            local_with_f_cells.append(c)
    # Build masks on win_rows
    wr = sorted(win_rows)
    wi = {v: i for i, v in enumerate(wr)}
    uni = (1 << len(wr)) - 1
    # Boundary indices
    b_idx = [wi[v] for v in sorted(boundary) if v in wi]
    # External coverage patterns on boundary: each subset of external cols that
    # can cover some pattern.  Enumerate 2^|boundary| patterns that are realizable.
    # For small windows |boundary| <= 8 typically.
    if len(b_idx) > 10:
        return False  # refuse large windows
    def mask_of(cols: list[GridColumn]) -> list[int]:
        out = []
        for c in cols:
            m = 0
            for v in c.verts & win_rows:
                m |= 1 << wi[v]
            out.append(m)
        return out

    p_masks = mask_of(local_with_p)
    f_only = 0
    for v in cell_verts(f) & win_rows:
        f_only |= 1 << wi[v]
    f_masks = mask_of(local_with_f_cells) + [f_only]
    # For every subset of boundary rows "precovered", compare local opts
    # Precover mask: bits of win_rows already covered from outside
    for bits in range(1 << len(b_idx)):
        pre = 0
        for t, bi in enumerate(b_idx):
            if bits & (1 << t):
                pre |= 1 << bi
        need = uni & ~pre
        if need == 0:
            continue
        opt_p, _ = exact_min_cost(p_masks, len(p_masks), need)
        opt_f, _ = exact_min_cost(f_masks, len(f_masks), need)
        if opt_p != opt_f:
            return False
    return True


# ----------------------------------------------------------------- audits
def dichotomy_counts(a: int = 3, b: int = 3) -> dict:
    """Face rows: no grid-surrogate core keeps a collapsible square; vertex rows: many do."""
    v_cores = v_with = f_cores = f_with = 0
    for cfg in all_configs(a, b):
        g = build_grid(cfg, a, b)
        # vertex
        cm = vertex_row_table(g)
        sub, _, _ = reduce_to_cyclic_core(cm.copy())
        if sub.n_rows() > 0:
            v_cores += 1
            by = {c.name: c for c in g.columns}
            left = [by[n] for n in sub.cols]
            if any(
                c.dim == 2 and free_faces(c.cell, [o.cell for o in left if o is not c])
                for c in left
            ):
                v_with += 1
        # face
        cmf = face_row_table(g)
        subf, _, _ = reduce_to_cyclic_core(cmf.copy())
        if subf.n_rows() > 0:
            f_cores += 1
            by = {c.name: c for c in g.columns}
            left = [by[n] for n in subf.cols]
            if any(
                c.dim == 2 and free_faces(c.cell, [o.cell for o in left if o is not c])
                for c in left
            ):
                f_with += 1
    return {
        "vertex_cores": v_cores,
        "vertex_with_collapsible_square": v_with,
        "face_cores": f_cores,
        "face_with_collapsible_square": f_with,
    }


def smallest_vertex_counterexample() -> TransformResult | None:
    """First (smallest grid) case where put-back decode disagrees with opt."""
    for a, b in ((2, 2), (2, 3), (3, 3)):
        for cfg in all_configs(a, b):
            g = build_grid(cfg, a, b)
            core = to_core(g)
            if core is None:
                continue
            for p, f in collapsible_pairs(core):
                res = apply_transform(core, p, f)
                if not res.agrees:
                    return res
    return None


def _opt_and_cexp(core: CoreInstance, p: GridColumn, f: tuple) -> tuple[float, float]:
    """opt(P) and opt(P') only — no put-back / C_in."""
    idx_p = core.core_cols.index(p)
    other_masks = [core.col_masks[k] for k in range(len(core.core_cols)) if k != idx_p]
    f_mask = 0
    for v in cell_verts(f) & core.core_rows:
        f_mask |= 1 << core.row_index[v]
    exp_masks = other_masks + [f_mask]
    opt, _ = exact_min_cost(core.col_masks, len(core.col_masks), core.universe)
    c_exp, _ = exact_min_cost(exp_masks, len(exp_masks), core.universe)
    return opt, c_exp


def verify_characterization(a: int = 3, b: int = 3, sample: int | None = None) -> dict:
    """Check opt(P')=opt(P) <=> far-side condition on every (core, p, f)."""
    checked = mismatches = 0
    n = 0
    for cfg in all_configs(a, b):
        n += 1
        if sample is not None and n > sample:
            break
        g = build_grid(cfg, a, b)
        core = to_core(g)
        if core is None:
            continue
        for p, f in collapsible_pairs(core):
            opt, c_exp = _opt_and_cexp(core, p, f)
            predicted = far_side_condition(core, p, f, opt)
            actual = c_exp == opt
            checked += 1
            if predicted != actual:
                mismatches += 1
    return {"checked": checked, "mismatches": mismatches}


# ----------------------------------------------------------------- sufficient-condition candidates
def candidate_far_empty(core: CoreInstance, p: GridColumn, f: tuple) -> bool:
    return len(far_rows(p, f, core.core_rows)) == 0


def candidate_far1_face1(core: CoreInstance, p: GridColumn, f: tuple) -> bool:
    F = far_rows(p, f, core.core_rows)
    near = cell_verts(f) & core.core_rows
    return len(F) == 1 and len(near) == 1


def candidate_far_dominated(core: CoreInstance, p: GridColumn, f: tuple) -> bool:
    """Every far row lies in a column (≠ p) that covers the whole far side F_p."""
    F = far_rows(p, f, core.core_rows)
    if not F:
        return True
    idx_p = core.core_cols.index(p)
    for v in F:
        if not any(
            k != idx_p and v in core.core_cols[k].verts and F <= core.core_cols[k].verts
            for k in range(len(core.core_cols))
        ):
            return False
    return True


def candidate_window(core: CoreInstance, p: GridColumn, f: tuple, radius: int) -> bool:
    return window_profile_agrees(core, p, f, radius=radius)


def audit_sufficient_candidate(
    name: str,
    predicate,
    a: int = 3,
    b: int = 3,
    sample: int | None = None,
) -> dict:
    """Count fires / failures of a sufficient-condition candidate.

    A failure is: predicate true but opt(P') != opt(P).
    """
    fires = fails = total = 0
    n = 0
    for cfg in all_configs(a, b):
        n += 1
        if sample is not None and n > sample:
            break
        g = build_grid(cfg, a, b)
        core = to_core(g)
        if core is None:
            continue
        for p, f in collapsible_pairs(core):
            total += 1
            if not predicate(core, p, f):
                continue
            fires += 1
            res = apply_transform(core, p, f)
            if res.c_exp != res.opt:
                fails += 1
    rate = (fires / total) if total else 0.0
    return {
        "name": name,
        "total": total,
        "fires": fires,
        "failures": fails,
        "fire_rate": rate,
        "pass": fails == 0 and rate >= 0.05,
        "trivial_ok": fails == 0,
    }


# ----------------------------------------------------------------- star / link Out
def star_of_free_face(p_cell: tuple, f: tuple) -> frozenset[tuple]:
    """Closed star ``st(f) = {τ | f ≤ τ}`` in the carrier square: ``{f, p}`` plus faces of ``f``."""
    cells: set[tuple] = {f, p_cell}
    for ff in faces_of(f):
        cells.add(ff)
    return frozenset(cells)


def link_vertices(
    core: CoreInstance,
    opp: tuple,
    *,
    exclude_col: str | None = None,
) -> frozenset[tuple[int, int]]:
    """Combinatorial link vertices of edge ``opp`` in the residual complex.

    A residual vertex ``v ∉ V(opp)`` lies in ``lk(opp)`` if some residual top cell
    (other than ``exclude_col``) meets both ``v`` and at least one vertex of ``opp``.
    """
    R = core.core_rows
    Vopp = cell_verts(opp) & R
    adj: set[tuple[int, int]] = set()
    for c in core.core_cols:
        if exclude_col is not None and c.name == exclude_col:
            continue
        if c.verts & Vopp:
            adj |= (c.verts & R) - Vopp
    return frozenset(adj)


@dataclass
class LinkOutInstance:
    """Vertex-row Out_link(p, f): link of opp(f) plus collar V(opp)."""

    p_name: str
    free_face: tuple
    opp: tuple
    out_rows: frozenset[tuple[int, int]]
    out_col_names: list[str]
    out_masks: list[int]
    out_universe: int
    L: float
    U: float
    opt: float
    stitch_names: list[str]
    exact_stitch: bool


def _solve_rows(
    core: CoreInstance,
    keep_rows: frozenset[tuple[int, int]],
    drop_cols: set[str],
) -> tuple[float, list[str]]:
    keep = sorted(keep_rows)
    if not keep:
        return 0.0, []
    ri = {v: i for i, v in enumerate(keep)}
    uni = (1 << len(keep)) - 1
    names: list[str] = []
    masks: list[int] = []
    for c in core.core_cols:
        if c.name in drop_cols:
            continue
        m = 0
        for v in c.verts & set(keep):
            m |= 1 << ri[v]
        if m:
            names.append(c.name)
            masks.append(m)
    if uni and not masks:
        return float("inf"), []
    cost, pick = exact_min_cost(masks, len(masks), uni)
    return cost, [names[i] for i in pick]


def link_out_complex(core: CoreInstance, p: GridColumn, f: tuple) -> LinkOutInstance:
    """Build ``Out_link(p,f)``, solve ``L = MinCov(Out)``, stitch ``U = |Reduced(M∪{p})|``."""
    opp = opposite_edge(p.cell, f)
    R = core.core_rows
    Vopp = cell_verts(opp) & R
    lk = link_vertices(core, opp, exclude_col=p.name)
    out_rows = frozenset(lk | Vopp)
    L, mout_names = _solve_rows(core, out_rows, {p.name})
    opt, _ = exact_min_cost(core.col_masks, len(core.col_masks), core.universe)
    if L == float("inf"):
        U = float("inf")
        stitch_names: list[str] = []
    else:
        mmap = {c.name: m for c, m in zip(core.core_cols, core.col_masks)}
        chosen = [(n, mmap[n]) for n in mout_names if n in mmap] + [(p.name, mmap[p.name])]
        sub = min_subcover_masks(core.universe, chosen)
        # Feasibility: Reduced(M∪{p}) must cover all residual rows
        cov = 0
        for _, m in sub:
            cov |= m
        if cov & core.universe != core.universe:
            # M may not extend; still form U from forced p + cover of R\V(p)
            rest = R - p.verts
            c_rest, rest_names = _solve_rows(core, rest, {p.name})
            if c_rest == float("inf"):
                U = float("inf")
                stitch_names = []
            else:
                chosen2 = [(n, mmap[n]) for n in rest_names] + [(p.name, mmap[p.name])]
                sub2 = min_subcover_masks(core.universe, chosen2)
                U = float(len(sub2))
                stitch_names = [n for n, _ in sub2]
        else:
            U = float(len(sub))
            stitch_names = [n for n, _ in sub]
    out_names = [c.name for c in core.core_cols if c.name != p.name and (c.verts & out_rows)]
    out_masks = []
    orows = sorted(out_rows)
    oi = {v: i for i, v in enumerate(orows)}
    uni = (1 << len(orows)) - 1 if orows else 0
    for c in core.core_cols:
        if c.name == p.name or not (c.verts & out_rows):
            continue
        m = 0
        for v in c.verts & out_rows:
            m |= 1 << oi[v]
        out_masks.append(m)
    return LinkOutInstance(
        p_name=p.name,
        free_face=f,
        opp=opp,
        out_rows=out_rows,
        out_col_names=out_names,
        out_masks=out_masks,
        out_universe=uni,
        L=L if out_rows else 0.0,
        U=U,
        opt=opt,
        stitch_names=stitch_names,
        exact_stitch=(U == opt),
    )


def _covering_opt(cm: CoveringMatrix) -> float:
    """Exact cover cost; bitmasks for small width, else B&B."""
    if cm.n_rows() == 0:
        return 0.0
    if cm.n_cols() == 0:
        return float("inf")
    if cm.n_cols() <= 14 and cm.n_rows() <= 24:
        uni = (1 << cm.n_rows()) - 1
        masks = []
        for jj in range(cm.n_cols()):
            m = 0
            for i in range(cm.n_rows()):
                if cm.matrix[i][jj]:
                    m |= 1 << i
            masks.append(m)
        return exact_min_cost(masks, cm.n_cols(), uni)[0]
    from topospine.cover.minimize import minimize_cover

    _, cost, _ = minimize_cover(cm.copy(), use_collapse=False)
    return cost


def star_collapse_face_rows(
    g: GridComplex,
    p: GridColumn,
    f: tuple,
) -> dict:
    """Theorem A (face rows): free face ⇒ ``p`` essential and ``opt = 1 + opt(K/p)``.

    ``K/p`` forces ``p``: delete rows covered by ``p`` and delete column ``p``.
    ``st(f)`` is the geometric star recorded for the paper/Lean narrative.
    """
    cm = face_row_table(g)
    try:
        j = cm.cols.index(p.name)
    except ValueError:
        return {"ok": False, "reason": "p_missing"}
    st = star_of_free_face(p.cell, f)
    n = cm.n_cols()
    n_rows = cm.n_rows()
    exclusive = [
        i
        for i in range(n_rows)
        if cm.matrix[i][j] and not any(cm.matrix[i][jj] for jj in range(n) if jj != j)
    ]
    opt = _covering_opt(cm)
    cm_in = cm.copy()
    rows_drop = {i for i in range(cm_in.n_rows()) if cm_in.matrix[i][j]}
    cm_in.remove_rows(rows_drop)
    if p.name in cm_in.cols:
        cm_in.remove_cols({cm_in.cols.index(p.name)})
    collapsed_opt = _covering_opt(cm_in)
    cm_out = cm.copy()
    cm_out.remove_cols({cm_out.cols.index(p.name)})
    c_out = _covering_opt(cm_out)
    predicted = 1.0 + collapsed_opt
    essential = len(exclusive) > 0 and (c_out > opt or c_out == float("inf"))
    return {
        "ok": essential and predicted == opt,
        "opt": opt,
        "collapsed_plus_one": predicted,
        "c_out": c_out,
        "p_essential": essential,
        "exclusive_rows": len(exclusive),
        "st_size": len(st),
    }


def audit_face_row_theorem_a(a: int = 3, b: int = 3) -> dict:
    """Exhaustive Theorem A check on face-row free squares (unreduced grids)."""
    checked = mismatches = essential = 0
    for cfg in all_configs(a, b):
        g = build_grid(cfg, a, b)
        by = {c.name: c for c in g.columns}
        for c in g.columns:
            if c.dim != 2:
                continue
            others = [o.cell for o in g.columns if o is not c]
            for f in free_faces(c.cell, others):
                rec = star_collapse_face_rows(g, c, f)
                checked += 1
                essential += int(rec.get("p_essential") or rec.get("exclusive_rows", 0) > 0)
                if not rec["ok"]:
                    mismatches += 1
    return {"checked": checked, "mismatches": mismatches, "essential_pairs": essential}


def audit_link_bounds(a: int = 3, b: int = 3, sample: int | None = None) -> dict:
    """Theorem C (sandbox): L ≤ opt ≤ U on every vertex-row grid-surrogate free pair."""
    checked = viol = exact = 0
    gaps: list[int] = []
    n = 0
    for cfg in all_configs(a, b):
        n += 1
        if sample is not None and n > sample:
            break
        core = to_core(build_grid(cfg, a, b))
        if core is None:
            continue
        for p, f in collapsible_pairs(core):
            inst = link_out_complex(core, p, f)
            checked += 1
            if not (inst.L <= inst.opt <= inst.U):
                viol += 1
            if inst.exact_stitch:
                exact += 1
            if inst.U < float("inf"):
                gaps.append(int(inst.U - inst.opt))
    from collections import Counter

    hist = Counter(gaps)
    return {
        "checked": checked,
        "violations": viol,
        "exact_stitch": exact,
        "exact_rate": (exact / checked) if checked else 0.0,
        "gap_histogram": dict(sorted(hist.items())),
    }
