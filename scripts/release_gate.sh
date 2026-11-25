#!/usr/bin/env bash
# Release gate for v0.1.0-arxiv-ae (Papers A+E freeze).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

echo "=== TopoSpine release gate ==="

# Grep: Paper B must not claim current covering vacuity without supersession language.
B_TEX="$ROOT/papers/B-certified-synthesis/main.tex"
if grep -qi 'vacuous' "$B_TEX"; then
  grep -qiE 'superseded|Paper~E|Paper E|C56|Horn covering' "$B_TEX" \
    || fail "Paper B mentions vacuous without Paper E / C56 / superseded"
  ok "Paper B vacuity language gated"
else
  ok "Paper B has no vacuous claim"
fi

# Python tests
if [[ -d "$ROOT/python" ]]; then
  (cd "$ROOT/python" && python -m pytest ../tests -q --tb=line) || fail "pytest"
  ok "pytest"
fi

# Lean
if [[ -d "$ROOT/lean" ]] && command -v lake >/dev/null 2>&1; then
  (cd "$ROOT/lean" && lake build) || fail "lake build"
  ok "lake build"
else
  echo "WARN: lake not found; skip Lean"
fi

# Tutorials 01–06
for i in 01 02 03 04 05 06; do
  script="$ROOT/tutorials/run_tutorial_${i}.py"
  if [[ -f "$script" ]]; then
    python "$script" || fail "tutorial $i"
    ok "tutorial $i"
  fi
done

# Tectonic (optional) for A/E
if command -v tectonic >/dev/null 2>&1; then
  for paper in A-cyclic-core E-tda-horn-programs; do
    tex="$ROOT/papers/$paper/main.tex"
    if [[ -f "$tex" ]]; then
      (cd "$ROOT/papers/$paper" && tectonic main.tex) || fail "tectonic $paper"
      ok "tectonic $paper"
    fi
  done
  if [[ -f "$ROOT/papers/B-certified-synthesis/main.tex" ]]; then
    (cd "$ROOT/papers/B-certified-synthesis" && tectonic main.tex) || fail "tectonic B"
    ok "tectonic B"
  fi
else
  echo "WARN: tectonic not found; skip PDF rebuild"
fi

echo "=== release gate green ==="
