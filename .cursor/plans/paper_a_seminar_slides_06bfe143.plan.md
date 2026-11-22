---
name: Paper A seminar slides
overview: "A graduate-seminar beamer talk for Paper A, built around two pictures: why the one-branch collapse needs transport hypothesis (H), and why shotgun shelling skips the reduction that sequential collapse relies on."
todos:
  - id: paper-a-seminar
    content: "Beamer talk in papers/A-cyclic-core/talk: (H) versus the one-branch argument, shotgun failure, compiled with tectonic"
    status: in_progress
isProject: false
---

# Paper A seminar: why (H), and why shotgun fails

Talk for a graduate student seminar, about 25 minutes, from [papers/A-cyclic-core/main.tex](papers/A-cyclic-core/main.tex). Beamer, compiled with tectonic, in `papers/A-cyclic-core/talk/`. The 2007 core figure already in the paper is reused. No new theorems.

## The talk’s spine
- Cyclic core as a covering table, then the classical two branches on a column p: include p, or exclude p. Optimum is the cheaper of those two.
- Free face f of a collapsible cell, and the one-branch procedure quoted as “Collapsible Cube Reduction”: delete p, insert the free face (or the set of them), solve once, and either keep that cover or swap the face back for p.
- What that procedure always gets: every exclude-p cover remains feasible after the expansion, so the expanded optimum is at most the exclude-p optimum.
- What it does not get: a comparison with the include-p optimum. That missing inequality is Definition (H), `cost(expanded) ≤ cost(best cover that contains p)`.
- Walk the quoted steps 4 and 5 against the proof of Theorem (collapse under (H)). Step 4 returns an exclude-p cover. Step 5 returns an include-p cover only as cheap as the expanded optimum, and only under unit or monotone weights. Both are global minima only after (H).
- Cover-admissibility is a different, checkable predicate. It holds on the n=5 examples where the branch returns 9 against an exact 8, and 8 against an exact 7. On all n≤4 functions it never disagreed. On 40,000 random n=5 functions it disagreed 42 times.
- Shotgun: two admissible pairs at once, then decode. Sequential collapse re-reduces between the two steps. The batch skips that. The guarded rule stays feasible and still costs 5 where the optimum is 4 (7 columns, 14 rows). The unguarded rules also leave reduced tables with an uncovered row (672 of 864 nontrivial n=4 instances).
- Close on what is certified instead: plain branch-and-bound. Collapse-branch and shotgun stay audited comparators. The open question for the room: a checkable condition that actually implies (H).

## Slides
- Title and the one-sentence claim.
- Covering table and the two branches, with costs C_in and C_out.
- Free face, one picture of a collapsible cube.
- The quoted one-branch procedure, steps 0–5, as a flow.
- The inequality that is free: expanded cost ≤ C_out.
- The cost line where (H) fails: C_in below the expanded cost, which still sits at or under C_out.
- Steps 4 and 5 annotated with which inequality each one uses.
- Admissibility versus (H), and the n=5 counts.
- Shotgun versus one-then-reduce-then-the-next.
- The 4-versus-5 witness and the infeasible batch.
- What the code certifies, and the open question.

## Completion
- `talk/main.tex` compiles with tectonic.
- Every numeric claim on a slide is one of: all n≤4 agree; 9 vs 8 and 8 vs 7; 42/40000; shotgun 5 vs 4; 672 infeasible n=4 batches.
- The 2007 figure is included as geometry of that core, not as a proof of (H).
