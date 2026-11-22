"""2D grid complexes for the free-face collapse as a local transform.

Every unit square of an ``a x b`` grid is filled (top cell of dim 2), hollow
(boundary edges only) or absent.  Vertex-row covering is the logic-minimization
problem: rows are vertices of the complex; columns are top cells; unit weights.
Face-row covering uses all proper faces (edges and vertices) as rows.

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
    """Exact unit-cost cover by increasing subset size.  Bitmasks over rows."""
    if universe == 0:
        return 0.0, []
    best: tuple[float, list[int]] = (float("inf"), [])
    for k in range(1, n_cols + 1):
        found = False
        for combo in combinations(range(n_cols), k):
            cov = 0
            for j in combo:
                cov |= row_masks[j]
            if cov & universe == universe:
                best = (float(k), list(combo))
                found = True
                break
        if found:
            break
    return best


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


# ----------------------------------------------------------------- core + transform
@dataclass
class CoreInstance:
    grid: GridComplex
    core_cols: list[GridColumn]
    core_rows: frozenset[tuple[int, int]]
    essentials: list[str]
    row_index: dict[tuple[int, int], int]
    col_masks: list[int]
    universe: int


def to_core(g: GridComplex) -> CoreInstance | None:
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
    far_mask = 0
    for v in F:
        far_mask |= 1 << core.row_index[v]
    # some optimal cover of original excludes p, OR covers F without p
    far_ok = False
    if far_mask == 0:
        far_ok = True
    else:
        # exists optimal cover without p covering F?
        for combo in combinations(range(len(others)), int(opt) if opt < float("inf") else 0):
            cov = 0
            for j in combo:
                cov |= other_masks[j]
            if cov & far_mask == far_mask and (cov | core.col_masks[idx_p]) & core.universe == core.universe:
                # cover of size |combo|+1 including p
                if len(combo) + 1 == opt:
                    far_ok = True
                    break
        # or optimal cover excluding p entirely
        if not far_ok:
            c_out, _ = exact_min_cost(other_masks, len(other_masks), core.universe)
            if c_out == opt:
                far_ok = True
        # also: exists any cover of F by others of size <= opt-1 that extends
        if not far_ok and far_mask:
            for k in range(0, int(opt)):
                for combo in combinations(range(len(others)), k):
                    cov = 0
                    for j in combo:
                        cov |= other_masks[j]
                    if cov & far_mask == far_mask:
                        # can we finish covering the rest with p?
                        if (cov | core.col_masks[idx_p]) & core.universe == core.universe and k + 1 == opt:
                            far_ok = True
                            break
                if far_ok:
                    break
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


def characterization_holds(core: CoreInstance, p: GridColumn, f: tuple, res: TransformResult) -> bool:
    """opt(P') == opt(P)  iff  far side is empty or coverable without p in some optimum."""
    return res.agrees == (res.far_empty or res.far_coverable_without_p)


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
    """Face rows: no cyclic core keeps a collapsible square. Vertex rows: many do."""
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


def verify_characterization(a: int = 3, b: int = 3, sample: int | None = None) -> dict:
    """Check agrees <=> (far empty or far coverable) on every (core, p, f)."""
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
            res = apply_transform(core, p, f)
            # Recompute far_coverable more carefully for the iff
            ok_iff = _iff_far_side(core, p, f, res)
            checked += 1
            if not ok_iff:
                mismatches += 1
    return {"checked": checked, "mismatches": mismatches}


def _iff_far_side(core: CoreInstance, p: GridColumn, f: tuple, res: TransformResult) -> bool:
    """opt(P')=opt(P) iff exists an optimal cover of P that excludes p OR covers F_p without needing p alone."""
    idx_p = core.core_cols.index(p)
    others_masks = [core.col_masks[k] for k in range(len(core.core_cols)) if k != idx_p]
    F = far_rows(p, f, core.core_rows)
    far_mask = 0
    for v in F:
        far_mask |= 1 << core.row_index[v]
    opt = res.opt
    # Exists optimal cover excluding p?
    c_out, _ = exact_min_cost(others_masks, len(others_masks), core.universe)
    exclude_ok = c_out == opt
    # Exists optimal cover including p that covers F with the other chosen columns?
    include_ok = False
    if far_mask == 0:
        include_ok = True
    else:
        # choose k = opt-1 others; with p they cover everything; others cover F
        k = int(opt) - 1
        if k >= 0:
            for combo in combinations(range(len(others_masks)), k):
                cov = 0
                for j in combo:
                    cov |= others_masks[j]
                if (cov & far_mask == far_mask) and ((cov | core.col_masks[idx_p]) & core.universe == core.universe):
                    include_ok = True
                    break
    predicted = exclude_ok or include_ok
    return predicted == res.agrees
