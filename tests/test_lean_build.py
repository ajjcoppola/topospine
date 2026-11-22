"""Gate: the whole Lean library must build (bare `lake build` silently built nothing in Loops 1-2)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

LEAN = Path(__file__).resolve().parents[1] / "lean"


@pytest.mark.skipif(shutil.which("lake") is None, reason="lake not installed")
def test_lake_build_all_modules():
    proc = subprocess.run(["lake", "build"], cwd=LEAN, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert "declaration uses 'sorry'" not in proc.stdout + proc.stderr
    assert "sorryAx" not in proc.stdout + proc.stderr
    import re

    code = "".join(p.read_text() for p in (LEAN / "TopoSpine").glob("*.lean"))
    code = re.sub(r"/-.*?-/", "", code, flags=re.S)  # strip block comments / docstrings
    code = re.sub(r"--[^\n]*", "", code)
    assert not re.search(r"\bsorry\b", code)
