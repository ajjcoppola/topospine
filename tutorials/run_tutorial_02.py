#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.synth import PassManager, SynthesisState


def main() -> None:
    print("=== Tutorial 02: pass manager ===\n")
    cx = coppola_2007_boolean_complex()
    state = SynthesisState(
        complex=cx,
        grades={str(c): float(c.dimension) for c in cx.top_cells},
    )
    pm = PassManager.default()
    out = pm.run(state)
    exp = pm.export(out)
    print(f"size {state.size()} → {out.size()}; passes logged: {len(out.log)}")
    print(json.dumps({"passes": [e.get("pass") for e in out.log], "export_keys": list(exp)}, indent=2))
    assert out.size() <= state.size()
    print("\nTutorial 02 OK.")


if __name__ == "__main__":
    main()
