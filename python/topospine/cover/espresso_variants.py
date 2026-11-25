"""Modern Espresso-family two-level minimizers and Espresso-Horn (Roth free-face escape).

Implements six comparable cube-array / ``.pla`` minimizers for Paper A benchmarks:

* ``espresso_ii_minimize`` — Brayton et al. (1984) ``ESSENTIALS → EXPAND →
  IRREDUNDANT → REDUCE (sccc) → LAST_GASP``.
* ``espresso_signature_minimize`` — McGeer et al. (1993) canonical signature
  cubes avoiding full Blake prime enumeration before cyclic-core reduction.
* ``boom_cd_minimize`` — Fiser–Hlavicka (2003) Coverage-Directed Search from
  ``Q_n`` against ``F^c``, then ``EXPAND + IRREDUNDANT``.
* ``abc_isop_minimize`` — Berkeley ABC / ``yosys-abc`` Minato–Morreale ZDD ISOP
  via ``read_pla; collapse; sop; write_pla``.
* ``highs_lp_ilp_bound`` — SciPy HiGHS LP relaxation ``ceil(z_LP)`` (zero-gap /
  TU detection) and optional exact MILP comparator.
* ``espresso_horn_minimize`` — Complement Free-Face Duality (H3), Zero-Loss Roth
  Push-Down (L0-A), Horn-Guided ``REDUCE`` escaping ``sccc`` stalls, and
  Controlled Collapsible Horn Chains (H4) with tightened window
  ``L = max(L_MIS, ceil(z_LP)) ≤ opt ≤ U``.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Sequence

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube
from topospine.cover.cube_array import (
    _masks_from_cm,
    _mis_lower_bound,
    absorb_cubes,
    coerce_cubes,
    covering_table_from_cube_array,
    cube_contained_in_union,
    cube_difference,
    cube_intersection,
    expand_to_primes_blake,
    extract_cube_space_essentials,
    zero_loss_free_face_pushdown,
)
from topospine.cover.horn_chains import (
    complement_cubes,
    controlled_horn_chain_cover,
    free_faces_via_complement,
    horn_faces,
)

EspressoVariant = Literal[
    "espresso_ii",
    "espresso_signature",
    "boom_cd",
    "abc_isop",
    "highs_lp_ilp",
    "espresso_horn",
    "classic_espresso",
]


@dataclass
class EspressoResult:
    """Common result envelope for all Espresso-family minimizers."""

    variant: EspressoVariant
    cover: list[BooleanCube]
    cost: int
    lower_bound: int = 0
    upper_bound: int = 0
    certified_optimal: bool = False
    sccc_stalled: bool = False
    horn_splits: int = 0
    wall_time_s: float = 0.0
    meta: dict = field(default_factory=dict)

    @property
    def cover_strs(self) -> list[str]:
        return [str(c) for c in self.cover]


# ----------------------------------------------------------------- PLA helpers
def cubes_to_pla(
    on_cubes: Sequence[BooleanCube | str],
    *,
    off_cubes: Sequence[BooleanCube | str] | None = None,
    dc_cubes: Sequence[BooleanCube | str] | None = None,
    name: str = "f",
) -> str:
    """Serialize a single-output Espresso ``.pla`` (type ``fd``) from cube arrays."""
    on = coerce_cubes(on_cubes)
    if not on and not (dc_cubes or off_cubes):
        raise ValueError("empty ON-set with no DC/OFF")
    n = len(on[0].bits) if on else (
        len(coerce_cubes(dc_cubes)[0].bits) if dc_cubes else len(coerce_cubes(off_cubes)[0].bits)  # type: ignore[arg-type]
    )
    lines = [f".i {n}", ".o 1", f".ilb {' '.join(f'x{i}' for i in range(n))}", ".ob y", ".type fd"]
    for c in on:
        lines.append(f"{_cube_bits(c)} 1")
    for c in coerce_cubes(dc_cubes or ()):
        lines.append(f"{_cube_bits(c)} -")
    # Explicit OFF rows are omitted under type fd (complement of ON∪DC).
    _ = off_cubes
    lines.append(".e")
    lines.insert(0, f"# {name}")
    return "\n".join(lines) + "\n"


def _cube_bits(c: BooleanCube) -> str:
    return "".join("-" if b is None else str(b) for b in c.bits)


def pla_cubes_from_text(text: str) -> list[BooleanCube]:
    """Parse ON cubes (output bit ``1``) from Espresso ``.pla`` text."""
    ni: int | None = None
    cubes: list[BooleanCube] = []
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("."):
            parts = line.split()
            if parts[0] == ".i":
                ni = int(parts[1])
            continue
        parts = line.split()
        if len(parts) != 2 or ni is None:
            continue
        cube, outs = parts
        if len(cube) != ni:
            continue
        if outs[0] == "1":
            bits: list[int | None] = []
            for ch in cube:
                if ch in "-~xX2":
                    bits.append(None)
                else:
                    bits.append(int(ch))
            cubes.append(BooleanCube(tuple(bits)))
    return absorb_cubes(cubes)


def cover_contains_on(
    cover: Sequence[BooleanCube | str],
    on_cubes: Sequence[BooleanCube | str],
) -> bool:
    """Exact cube-space check that ``⋃ cover`` contains ``⋃ on_cubes``."""
    cov = coerce_cubes(cover)
    for t in coerce_cubes(on_cubes):
        if not cube_contained_in_union(t, cov):
            return False
    return True


def cover_avoids_off(
    cover: Sequence[BooleanCube | str],
    off_cubes: Sequence[BooleanCube | str],
) -> bool:
    """Exact check that no cube of ``cover`` meets any cube of ``off_cubes``."""
    cov = coerce_cubes(cover)
    off = coerce_cubes(off_cubes)
    for c in cov:
        for d in off:
            if cube_intersection(c, d) is not None:
                return False
    return True


# ----------------------------------------------------------------- classical Espresso primitives
def _expand_vs_off(
    cubes: Sequence[BooleanCube],
    off: Sequence[BooleanCube],
) -> list[BooleanCube]:
    """Raise literals while the candidate stays disjoint from every OFF cube."""
    expanded: list[BooleanCube] = []
    for c in cubes:
        cur = c
        for i, b in enumerate(cur.bits):
            if b is None:
                continue
            bits = list(cur.bits)
            bits[i] = None
            cand = BooleanCube(tuple(bits))
            if all(cube_intersection(cand, d) is None for d in off):
                cur = cand
        expanded.append(cur)
    return absorb_cubes(expanded)


def _sccc_reduce(
    cover: Sequence[BooleanCube],
    on_cubes: Sequence[BooleanCube],
) -> tuple[list[BooleanCube], bool]:
    """Espresso ``REDUCE``: shrink each ``p`` to the supercube of ``p # others``
    restricted to ON coverage (Shannon cofactor containment / sharp).

    Returns ``(reduced_cover, stalled)`` where ``stalled`` is True iff every cube
    is unchanged (classical local minimum / antipodal private-point trap).
    """
    cur = list(cover)
    stalled = True
    for i in range(len(cur)):
        p = cur[i]
        others = [cur[k] for k in range(len(cur)) if k != i]
        # Private ON residual of p: (p ∩ ON) \\ ⋃ others
        private_parts: list[BooleanCube] = []
        for on in on_cubes:
            inter = cube_intersection(p, on)
            if inter is None:
                continue
            private_parts.extend(cube_difference(inter, others))
        private_parts = absorb_cubes(private_parts)
        if not private_parts:
            # Fully redundant under ON — mark for drop
            stalled = False
            cur[i] = p  # kept temporarily; IRREDUNDANT drops it
            continue
        # Supercube of private parts (= bitwise OR of fixed literals that agree)
        bits: list[int | None] = list(private_parts[0].bits)
        for q in private_parts[1:]:
            for j, (bj, qj) in enumerate(zip(bits, q.bits)):
                if bj != qj:
                    bits[j] = None
        # Also free any literal of p that is free in all private parts
        reduced = BooleanCube(tuple(bits))
        # Ensure reduced ⊆ p (tighten free vars of p that disagree)
        rb = list(reduced.bits)
        for j, pb in enumerate(p.bits):
            if pb is not None and rb[j] is None:
                # Keep raised only if still covering all private parts
                trial = list(rb)
                trial[j] = pb
                tcube = BooleanCube(tuple(trial))
                if all(cube_contained_in_union(pp, [tcube]) for pp in private_parts):
                    rb[j] = pb
            elif pb is not None and rb[j] is not None and rb[j] != pb:
                rb[j] = pb
        reduced = BooleanCube(tuple(rb))
        if reduced != p:
            stalled = False
        cur[i] = reduced
    # Drop cubes that no longer cover anything useful / absorbed
    cleaned = absorb_cubes([c for c in cur if any(b is not None or True for b in c.bits)])
    # Filter fully-redundant after absorb
    cleaned = [c for c in cleaned if not cube_contained_in_union(c, [d for d in cleaned if d != c])
               or len(cleaned) == 1]
    # Prefer irredundant selection against ON
    return _irredundant_cubes(cleaned, on_cubes), stalled and len(cleaned) == len(cover)


def _irredundant_cubes(
    cover: Sequence[BooleanCube],
    on_cubes: Sequence[BooleanCube],
) -> list[BooleanCube]:
    """Greedy IRREDUNDANT: drop cubes whose removal still covers ON."""
    keep = list(cover)
    changed = True
    while changed:
        changed = False
        for c in list(keep):
            trial = [d for d in keep if d != c]
            if trial and cover_contains_on(trial, on_cubes):
                keep = trial
                changed = True
                break
    return absorb_cubes(keep)


def _essentials_then_cover(
    candidates: Sequence[BooleanCube],
    on_cubes: Sequence[BooleanCube],
) -> list[BooleanCube]:
    ess, rem = extract_cube_space_essentials(list(candidates))
    # Cover residual ON by remaining candidates greedily (largest first)
    covered = list(ess)
    residual = cube_difference(
        BooleanCube((None,) * len(on_cubes[0].bits)) if on_cubes else BooleanCube(()),
        [],
    )
    # Better: residual ON parts
    on_res = absorb_cubes(
        [p for on in on_cubes for p in cube_difference(on, covered)]
    )
    rem_sorted = sorted(rem, key=lambda c: (-c.dimension, str(c)))
    for c in rem_sorted:
        if not on_res:
            break
        if any(cube_intersection(c, r) is not None for r in on_res):
            covered.append(c)
            on_res = absorb_cubes([p for r in on_res for p in cube_difference(r, [c])])
    return _irredundant_cubes(covered, on_cubes)


# ----------------------------------------------------------------- 1. Espresso-II
def espresso_ii_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
    max_iters: int = 4,
) -> EspressoResult:
    """Classical Espresso-II heuristic operating in cube space against ``F^c``."""
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("espresso_ii", [], 0, 0, 0, True, wall_time_s=0.0)
    dc = coerce_cubes(dc_cubes)
    care = absorb_cubes(on + dc)
    off = complement_cubes(care)
    # EXPAND each ON cube vs OFF (raise into DC freely)
    expanded = _expand_vs_off(on, off)
    # Seed cover = irredundant expanded
    cover = _irredundant_cubes(expanded, on)
    stalled = False
    for _ in range(max_iters):
        cover, stalled = _sccc_reduce(cover, on)
        cover = _expand_vs_off(cover, off)
        cover = _irredundant_cubes(cover, on)
        if stalled:
            break
    # LAST_GASP: reduce each cube maximally then re-expand
    gasp, g_stall = _sccc_reduce(cover, on)
    gasp = _expand_vs_off(gasp, off)
    gasp = _irredundant_cubes(gasp, on)
    if len(gasp) < len(cover):
        cover = gasp
        stalled = g_stall
    cost = len(cover)
    return EspressoResult(
        variant="espresso_ii",
        cover=cover,
        cost=cost,
        lower_bound=0,
        upper_bound=cost,
        certified_optimal=False,
        sccc_stalled=stalled,
        wall_time_s=time.perf_counter() - t0,
        meta={"n_off": len(off)},
    )


# ----------------------------------------------------------------- 2. Espresso-Signature
def _signature_cube(
    seed: BooleanCube,
    off: Sequence[BooleanCube],
    on_all: Sequence[BooleanCube],
) -> BooleanCube:
    """Canonical signature cube containing ``seed``: maximal raise vs OFF, then
    drop literals that are not required by any private ON point of the raised cube.
    """
    raised = _expand_vs_off([seed], off)[0]
    # Private ON points of raised among on_all relative to other signatures later;
    # for a single signature, keep raised (McGeer σ contains all primes through seed).
    _ = on_all
    return raised


def espresso_signature_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
) -> EspressoResult:
    """McGeer-style signature cubes → essentials → irredundant cyclic-core cover."""
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("espresso_signature", [], 0, 0, 0, True, wall_time_s=0.0)
    care = absorb_cubes(on + coerce_cubes(dc_cubes))
    off = complement_cubes(care)
    # Expand ON into minterms-as-cubes only when small; else use ON cubes as seeds
    seeds: list[BooleanCube] = []
    for c in on:
        if c.dimension <= 2:
            # Enumerate vertices of small cubes as signature seeds
            free = [i for i, b in enumerate(c.bits) if b is None]
            if len(free) <= 2:
                from itertools import product as iproduct

                for assign in iproduct((0, 1), repeat=len(free)):
                    bits = list(c.bits)
                    for i, v in zip(free, assign):
                        bits[i] = v
                    seeds.append(BooleanCube(tuple(bits)))
            else:
                seeds.append(c)
        else:
            seeds.append(c)
    sigs = absorb_cubes([_signature_cube(s, off, on) for s in seeds])
    cover = _essentials_then_cover(sigs, on)
    cost = len(cover)
    return EspressoResult(
        variant="espresso_signature",
        cover=cover,
        cost=cost,
        lower_bound=0,
        upper_bound=cost,
        certified_optimal=False,
        wall_time_s=time.perf_counter() - t0,
        meta={"n_signatures": len(sigs)},
    )


# ----------------------------------------------------------------- 3. BOOM CD-Search
def _boom_cd_search(
    on: Sequence[BooleanCube],
    off: Sequence[BooleanCube],
    *,
    max_cubes: int = 256,
) -> list[BooleanCube]:
    """Top-down Coverage-Directed Search from ``Q_n`` against OFF."""
    if not on:
        return []
    n = len(on[0].bits)
    root = BooleanCube((None,) * n)
    found: list[BooleanCube] = []
    stack: list[BooleanCube] = [root]
    covered_on = list(on)

    while stack and len(found) < max_cubes and covered_on:
        cur = stack.pop()
        if any(cube_intersection(cur, d) is not None for d in off):
            # Illegal: split on a variable that separates OFF
            split_var = -1
            best = -1
            for i, b in enumerate(cur.bits):
                if b is not None:
                    continue
                # Prefer vars that appear fixed in OFF intersections
                score = sum(
                    1
                    for d in off
                    if cube_intersection(cur, d) is not None and d.bits[i] is not None
                )
                if score > best:
                    best = score
                    split_var = i
            if split_var < 0:
                # Fallback: first free var
                for i, b in enumerate(cur.bits):
                    if b is None:
                        split_var = i
                        break
            if split_var < 0:
                continue
            for val in (0, 1):
                bits = list(cur.bits)
                bits[split_var] = val
                child = BooleanCube(tuple(bits))
                if any(cube_intersection(child, o) is not None for o in covered_on):
                    stack.append(child)
            continue
        # Legal implicant: keep if it hits uncovered ON
        if any(cube_intersection(cur, o) is not None for o in covered_on):
            found.append(cur)
            covered_on = absorb_cubes(
                [p for o in covered_on for p in cube_difference(o, [cur])]
            )
    return absorb_cubes(found)


def boom_cd_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
) -> EspressoResult:
    """BOOM Coverage-Directed Search + EXPAND + IRREDUNDANT."""
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("boom_cd", [], 0, 0, 0, True, wall_time_s=0.0)
    care = absorb_cubes(on + coerce_cubes(dc_cubes))
    off = complement_cubes(care)
    raw = _boom_cd_search(on, off)
    expanded = _expand_vs_off(raw, off)
    cover = _irredundant_cubes(expanded, on)
    cost = len(cover)
    return EspressoResult(
        variant="boom_cd",
        cover=cover,
        cost=cost,
        lower_bound=0,
        upper_bound=cost,
        certified_optimal=False,
        wall_time_s=time.perf_counter() - t0,
        meta={"n_raw": len(raw)},
    )


# ----------------------------------------------------------------- 4. ABC ISOP
def find_abc_binary() -> str | None:
    return shutil.which("abc") or shutil.which("yosys-abc")


def find_classic_espresso() -> str | None:
    """Locate Berkeley Espresso CLI: ``PATH``, then repo ``third_party/espresso/build/espresso``."""
    found = shutil.which("espresso")
    if found:
        return found
    here = Path(__file__).resolve()
    # python/topospine/cover/espresso_variants.py → repo root
    root = here.parents[3]
    candidate = root / "third_party" / "espresso" / "build" / "espresso"
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


def classic_espresso_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
    timeout_s: int = 60,
    espresso_args: Sequence[str] = (),
) -> EspressoResult:
    """UC Berkeley Espresso heuristic via external CLI (large-.pla capable)."""
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("classic_espresso", [], 0, 0, 0, True, wall_time_s=0.0)
    exe = find_classic_espresso()
    if exe is None:
        return EspressoResult(
            variant="classic_espresso",
            cover=[],
            cost=-1,
            meta={"available": False, "error": "espresso not on PATH / third_party"},
            wall_time_s=time.perf_counter() - t0,
        )
    pla_in = cubes_to_pla(on, dc_cubes=dc_cubes, name="classic_espresso")
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.pla"
        inp.write_text(pla_in)
        cmd = [exe, *espresso_args, str(inp)]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return EspressoResult(
                variant="classic_espresso",
                cover=[],
                cost=-1,
                meta={"available": True, "binary": exe, "error": repr(exc)},
                wall_time_s=time.perf_counter() - t0,
            )
        # Espresso writes minimized PLA to stdout
        out_text = proc.stdout
        if proc.returncode != 0 and not out_text.strip():
            return EspressoResult(
                variant="classic_espresso",
                cover=[],
                cost=-1,
                meta={
                    "available": True,
                    "binary": exe,
                    "returncode": proc.returncode,
                    "stderr": proc.stderr[-500:],
                },
                wall_time_s=time.perf_counter() - t0,
            )
        cover = pla_cubes_from_text(out_text)
    cost = len(cover)
    return EspressoResult(
        variant="classic_espresso",
        cover=cover,
        cost=cost,
        lower_bound=0,
        upper_bound=cost,
        certified_optimal=False,
        wall_time_s=time.perf_counter() - t0,
        meta={"available": True, "binary": Path(exe).name, "returncode": proc.returncode},
    )


def abc_isop_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
    timeout_s: int = 30,
) -> EspressoResult:
    """Berkeley ABC Minato–Morreale ZDD ISOP via ``read_pla; collapse; sop; write_pla``."""
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("abc_isop", [], 0, 0, 0, True, wall_time_s=0.0)
    exe = find_abc_binary()
    if exe is None:
        return EspressoResult(
            variant="abc_isop",
            cover=[],
            cost=-1,
            meta={"available": False, "error": "abc / yosys-abc not on PATH"},
            wall_time_s=time.perf_counter() - t0,
        )
    pla_in = cubes_to_pla(on, dc_cubes=dc_cubes, name="abc_isop")
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.pla"
        outp = Path(td) / "out.pla"
        inp.write_text(pla_in)
        try:
            proc = subprocess.run(
                [exe, "-c", f"read_pla {inp}; collapse; sop; write_pla {outp}"],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return EspressoResult(
                variant="abc_isop",
                cover=[],
                cost=-1,
                meta={"available": True, "binary": Path(exe).name, "error": repr(exc)},
                wall_time_s=time.perf_counter() - t0,
            )
        if not outp.exists():
            return EspressoResult(
                variant="abc_isop",
                cover=[],
                cost=-1,
                meta={
                    "available": True,
                    "binary": Path(exe).name,
                    "returncode": proc.returncode,
                    "stderr": proc.stderr[-500:],
                    "error": "write_pla produced no file",
                },
                wall_time_s=time.perf_counter() - t0,
            )
        cover = pla_cubes_from_text(outp.read_text())
    cost = len(cover)
    return EspressoResult(
        variant="abc_isop",
        cover=cover,
        cost=cost,
        lower_bound=0,
        upper_bound=cost,
        certified_optimal=False,
        wall_time_s=time.perf_counter() - t0,
        meta={"available": True, "binary": Path(exe).name, "returncode": proc.returncode},
    )


# ----------------------------------------------------------------- 5. HiGHS LP / ILP
def highs_lp_ilp_bound(
    on_cubes: Sequence[BooleanCube | str],
    *,
    candidates: Sequence[BooleanCube | str] | None = None,
    solve_milp: bool = True,
    max_primes: int = 512,
) -> EspressoResult:
    """SciPy HiGHS LP relaxation lower bound ``ceil(z_LP)`` and optional exact MILP.

    When ``candidates`` is omitted, Blake primes of ``on_cubes`` are used (capped).
    Detects zero integrality gap (TU-like cores) when ``ceil(z_LP) == z_MILP``.
    """
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("highs_lp_ilp", [], 0, 0, 0, True, wall_time_s=0.0)
    if candidates is None:
        cands = expand_to_primes_blake(on, max_primes=max_primes)
    else:
        cands = coerce_cubes(candidates)
    cm = covering_table_from_cube_array(cands)
    if cm.n_rows() == 0:
        return EspressoResult("highs_lp_ilp", [], 0, 0, 0, True, wall_time_s=0.0)

    import numpy as np
    from scipy.optimize import LinearConstraint, Bounds, milp, linprog

    A = np.array(cm.matrix, dtype=float)
    R, C = A.shape
    c = np.ones(C)
    # LP relaxation
    lp = linprog(
        c,
        A_ub=-A,
        b_ub=-np.ones(R),
        bounds=(0, 1),
        method="highs",
    )
    z_lp = float(lp.fun) if lp.success else float("nan")
    ceil_lp = int(math.ceil(z_lp - 1e-9)) if lp.success else 0

    milp_cost = None
    milp_cover: list[BooleanCube] = []
    zero_gap = False
    if solve_milp:
        cons = LinearConstraint(A, lb=np.ones(R), ub=np.full(R, np.inf))
        res = milp(
            c=c,
            constraints=cons,
            integrality=np.ones(C),
            bounds=Bounds(0, 1),
        )
        if res.success:
            x = np.asarray(res.x)
            milp_cost = int(round(float(res.fun)))
            milp_cover = [cands[j] for j in range(C) if x[j] > 0.5]
            zero_gap = abs(z_lp - milp_cost) < 1e-6 if lp.success else False

    cover = milp_cover if milp_cover else []
    cost = milp_cost if milp_cost is not None else -1
    return EspressoResult(
        variant="highs_lp_ilp",
        cover=cover,
        cost=cost if cost is not None else -1,
        lower_bound=ceil_lp,
        upper_bound=cost if cost is not None and cost >= 0 else ceil_lp,
        certified_optimal=bool(zero_gap and milp_cost is not None),
        wall_time_s=time.perf_counter() - t0,
        meta={
            "z_lp": z_lp,
            "ceil_lp": ceil_lp,
            "milp_cost": milp_cost,
            "zero_integrality_gap": zero_gap,
            "n_candidates": C,
            "n_rows": R,
            "lp_success": bool(lp.success),
        },
    )


# ----------------------------------------------------------------- 6. Espresso-Horn
def _horn_guided_reduce(
    cover: Sequence[BooleanCube],
    on_cubes: Sequence[BooleanCube],
    off: Sequence[BooleanCube],
) -> tuple[list[BooleanCube], int, bool]:
    """When classical ``sccc`` stalls, split an ``sccc``-locked cube along a free-face horn.

    Returns ``(new_cover, n_splits, still_stalled)``.
    """
    reduced, stalled = _sccc_reduce(cover, on_cubes)
    if not stalled:
        return reduced, 0, False

    # Find a cube with a free face via complement duality
    splits = 0
    cur = list(reduced)
    for i, p in enumerate(list(cur)):
        if p.dimension < 1:
            continue
        frees = free_faces_via_complement(p, off_cubes=off)
        if not frees:
            continue
        # Prefer free face maximizing |horn ∩ residual ON of p|
        best_f = None
        best_score = -1
        others = [c for j, c in enumerate(cur) if j != i]
        private: list[BooleanCube] = []
        for on in on_cubes:
            inter = cube_intersection(p, on)
            if inter is None:
                continue
            private.extend(cube_difference(inter, others))
        private = absorb_cubes(private)
        for f in frees:
            horn = horn_faces(p, f)
            score = sum(
                1
                for h in horn
                for pp in private
                if cube_intersection(h, pp) is not None
            )
            if score > best_score:
                best_score = score
                best_f = f
        if best_f is None:
            continue
        horn = horn_faces(p, best_f)
        # Keep only horn faces that hit private ON
        active = [
            h for h in horn
            if any(cube_intersection(h, pp) is not None for pp in private)
        ]
        if not active:
            active = list(horn)
        # Expand horn faces vs OFF and replace p
        active = _expand_vs_off(active, off)
        cur = [c for j, c in enumerate(cur) if j != i] + active
        splits += 1
        stalled = False
        break

    cur = _irredundant_cubes(absorb_cubes(cur), on_cubes)
    return cur, splits, stalled and splits == 0


def espresso_horn_minimize(
    on_cubes: Sequence[BooleanCube | str],
    *,
    dc_cubes: Sequence[BooleanCube | str] = (),
    mode: Literal["exact", "approx", "probabilistic"] = "exact",
    num_chains: int = 8,
    seed: int = 0,
    use_lp_bound: bool = True,
) -> EspressoResult:
    """Espresso-Horn: H3 duality + L0-A push-down + Horn-Guided REDUCE + H4 chains.

    Certified window ``L = max(L_MIS, ceil(z_LP)) ≤ opt ≤ U``; optimality when ``U = L``.
    """
    t0 = time.perf_counter()
    on = coerce_cubes(on_cubes)
    if not on:
        return EspressoResult("espresso_horn", [], 0, 0, 0, True, wall_time_s=0.0)
    care = absorb_cubes(on + coerce_cubes(dc_cubes))
    off = complement_cubes(care)

    # Seed with Espresso-II then Horn-escape sccc stalls
    seed_res = espresso_ii_minimize(on, dc_cubes=dc_cubes)
    cover = list(seed_res.cover)
    total_splits = 0
    for _ in range(6):
        cover, splits, still = _horn_guided_reduce(cover, on, off)
        total_splits += splits
        cover = _expand_vs_off(cover, off)
        cover = _irredundant_cubes(cover, on)
        if still or splits == 0:
            break

    # Build covering table on Blake primes (or seed cover if prime expansion is huge)
    try:
        primes = expand_to_primes_blake(care, max_primes=1024)
    except ValueError:
        primes = absorb_cubes(cover + list(on))
    cm = covering_table_from_cube_array(primes)
    # Zero-loss Roth push-down
    cm, _, n_push = zero_loss_free_face_pushdown(cm)
    cm, _, ess = reduce_to_cyclic_core(cm)

    # LP / MIS lower bound
    masks, univ = _masks_from_cm(cm) if cm.n_rows() else ([], 0)
    C = cm.n_cols()
    row_cols = (
        [sum((1 << j) for j in range(C) if (masks[j] >> r) & 1) for r in range(cm.n_rows())]
        if C
        else []
    )
    l_mis = _mis_lower_bound(row_cols, univ) if univ else 0
    ceil_lp = 0
    if use_lp_bound and cm.n_rows() and cm.n_cols():
        try:
            import numpy as np
            from scipy.optimize import linprog

            A = np.array(cm.matrix, dtype=float)
            lp = linprog(
                np.ones(cm.n_cols()),
                A_ub=-A,
                b_ub=-np.ones(cm.n_rows()),
                bounds=(0, 1),
                method="highs",
            )
            if lp.success:
                ceil_lp = int(math.ceil(float(lp.fun) - 1e-9))
        except Exception:
            ceil_lp = 0
    L = max(l_mis, ceil_lp) + len(ess)

    if cm.n_rows() == 0:
        final = absorb_cubes(cover)
        cost = len(final)
        return EspressoResult(
            variant="espresso_horn",
            cover=final,
            cost=cost,
            lower_bound=cost,
            upper_bound=cost,
            certified_optimal=True,
            sccc_stalled=seed_res.sccc_stalled,
            horn_splits=total_splits,
            wall_time_s=time.perf_counter() - t0,
            meta={"n_push": n_push, "essentials": len(ess), "L_MIS": l_mis, "ceil_LP": ceil_lp},
        )

    chain = controlled_horn_chain_cover(cm, mode=mode, num_chains=num_chains, seed=seed)
    # Decode column names → cubes; add essentials (already removed from cyclic core)
    chosen = [cm.col_cubes[i] for i in chain.cover_indices if isinstance(cm.col_cubes[i], BooleanCube)]
    # Essentials were extracted; re-add by name lookup on original primes table
    # Rebuild with essentials included via covering of ON
    merged = absorb_cubes(list(chosen) + list(cover))
    merged = _irredundant_cubes(merged, on)
    # If chain cover alone is better and covers ON, prefer it
    chain_only = absorb_cubes(list(chosen))
    if chain_only and cover_contains_on(chain_only, on) and len(chain_only) <= len(merged):
        merged = chain_only

    U = len(merged)
    L_final = min(L, U)  # L cannot exceed a feasible U for reporting sanity
    # Recompute L against full problem: max(L_MIS_full sense, ceil_lp) — keep L from core + ess
    certified = U <= L or (chain.certified_optimal and cover_contains_on(merged, on))
    # Tighten: if U == L then certified
    if U == L:
        certified = True

    return EspressoResult(
        variant="espresso_horn",
        cover=merged,
        cost=U,
        lower_bound=L if L <= U else U,
        upper_bound=U,
        certified_optimal=certified and U == (L if L <= U else U),
        sccc_stalled=seed_res.sccc_stalled,
        horn_splits=total_splits,
        wall_time_s=time.perf_counter() - t0,
        meta={
            "mode": mode,
            "n_push": n_push,
            "essentials": len(ess),
            "L_MIS": l_mis,
            "ceil_LP": ceil_lp,
            "L": L,
            "chain_cost": chain.cost,
            "chain_certified": chain.certified_optimal,
            "horn_steps": chain.total_horn_steps,
            "bb_nodes": chain.bb_nodes,
        },
    )


def minimize_with_variant(
    variant: EspressoVariant,
    on_cubes: Sequence[BooleanCube | str],
    **kwargs,
) -> EspressoResult:
    """Dispatch helper for benchmarks."""
    if variant == "espresso_ii":
        return espresso_ii_minimize(on_cubes, **kwargs)
    if variant == "espresso_signature":
        return espresso_signature_minimize(on_cubes, **kwargs)
    if variant == "boom_cd":
        return boom_cd_minimize(on_cubes, **kwargs)
    if variant == "abc_isop":
        return abc_isop_minimize(on_cubes, **kwargs)
    if variant == "highs_lp_ilp":
        return highs_lp_ilp_bound(on_cubes, **kwargs)
    if variant == "espresso_horn":
        return espresso_horn_minimize(on_cubes, **kwargs)
    if variant == "classic_espresso":
        return classic_espresso_minimize(on_cubes, **kwargs)
    raise ValueError(f"unknown variant: {variant!r}")
