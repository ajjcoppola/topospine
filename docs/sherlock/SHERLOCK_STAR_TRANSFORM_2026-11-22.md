# Sherlock — Star-of-free-face transform (2026-11-22)

## Question
Replace the free-face column swap by removing the **star** of the free face,
recurse on (i) complex \ star and (ii) free cube \ star, stitch (often with `p`),
and hope this kills the 2×3 ring counterexample and yields a theorem.

## Step 1 — Candidate meanings of “star”
1. Column-star of free face `f`: columns containing `f` → `{p}` only (free).
2. Closed star rows `V(f)`; drop `p`.
3. Columns meeting `V(f)` (vertex-closed star of `f` among top cells).
4. Closed star of carrier `p` (drop all of `V(p)` / all cols meeting `p`).
5. Partition Outside=`R\V(p)`, Local=`F_p`, Face=`V(f)`; stitch recipes T1–T6.
6. Face-row regime: free face already forces `p` essential (dichotomy).

## Step 2 — Distilled
- **A.** Vertex-row one-branch star stitch (no separate `C_out`) — hoped-for theorem.
- **B.** Vertex-row `min(Outside_⋆∪{p}, C_out)` — looks new but may be classical B&B.
- **C.** Face-row star collapse with forced `p` — likely true by dichotomy.

## Step 3–4 — Findings (exhaustive 3×3 vertex-row, 32 288 pairs)

| Claim | Result |
|-------|--------|
| 2×3 ring killed by star-partition + stitch-with-`p` | **Yes**, for meet-`V(f)` / `p`-only stars (via include-`p` branch) |
| One-branch `T3 = Reduced(MinCov(Outside, P\⋆(f)) ∪ {p})` alone | **Fails** 10.5% (`meet_f`) / 3.9% (`p_only`) |
| `T6 = min(T3, C_out)` | **0 failures** |
| Is `T6` new? | **No** — identical to classical `min(C_in, C_out)` on all 32 288 pairs (`t6_eq_classical = 32288`). When star-drop hurts Outside (`T3 > C_in`, 224 cases), `C_out` already equals opt |
| Face-row free square ⇒ `p` essential (2×3 unreduced) | **1458/1458** |

### Why one-branch cannot be unconditional on vertex rows
A free face occurs both when some optimum **includes** `p` and when some optimum **excludes** `p` (far-side theorem). Any procedure that always adds `p` after deleting the star fails on exclude-optima; any that never adds `p` fails on the 2×3 ring. Star enlargement (meet-`V(f)`, meet-`p`) does not remove that dichotomy; it only weakens the include branch.

### What *does* hold
1. **Far-side characterization** (already Paper A): still the vertex-row iff.
2. **Face-row star collapse (candidate theorem):** if rows are all proper faces and `f` is free for `p`, then `p` is essential, and  
   `opt(K) = 1 + opt(K \ st(f))`  
   with `st(f) = {cells ≥ f}` (elementary collapse of the cell complex). Matches “free faces generalize essentials.”
3. **Star partition as rewrite of B&B:** Outside without star-cols + optional `p`, min’d with `C_out`, is bookkeeping—not a complexity win.

## Step 5 — Suggestions / next probes
- Formalize face-row theorem in Lean + Python (`face_row_table` + star deletion).
- Optional: search for a *checkable* predicate under which vertex-row `T3` alone equals opt (likely implies far-side / `|F_p|≤1` style).
- Do **not** rewrite Paper A around vertex-row star one-branch; evidence refutes unconditional optimality.
- If papers move to face-row collapse, keep vertex-row far-side as the logic-minimization theorem.

## Step 6 — Cleanup
Probe scripts were ephemeral (`/tmp` / stdin). No temporary repo diagnostics to remove.

## Follow-up (implemented)
Option 3 shipped: face-row Theorem A + Link(`opp`) `(L,U)` window.
See `SHERLOCK_STAR_LINK_2026-11-22.md`, claims C42–C44.
