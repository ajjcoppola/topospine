"""Small, size-capped readers for ``.pla`` (espresso) and combinational ``.blif`` files.

Both return a :class:`LogicSpec`: per-output ON/DC minterm sets over the inputs, with
the same minterm convention as :class:`topospine.synth.aig.AIG` (first input = MSB).
Caps keep the Python pipeline honest: ``max_inputs`` (default 10) and a clear error
otherwise.  Only combinational, single-model files are supported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from topospine.synth.logic_passes import LogicState


@dataclass
class LogicSpec:
    name: str
    inputs: list[str]
    outputs: list[str]
    on: dict[str, set[int]] = field(default_factory=dict)
    dc: dict[str, set[int]] = field(default_factory=dict)
    gate_count_reference: int | None = None  # AND/NAND gate count of the source netlist, if known

    @property
    def n(self) -> int:
        return len(self.inputs)


def _expand(cube: str) -> list[int]:
    n = len(cube)
    opts = [("0", "1") if ch in "-~xX2" else (ch,) for ch in cube]
    return [int("".join(p), 2) if n else 0 for p in product(*opts)]


def read_pla(text: str, name: str = "pla", max_inputs: int = 10) -> LogicSpec:
    """Espresso ``.pla`` (type fd/fr treated as fd: ``1`` -> ON, ``-``/``2`` -> DC, ``0``/``~`` ignored)."""
    ni = no = None
    ilb: list[str] | None = None
    ob: list[str] | None = None
    rows: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("."):
            parts = line.split()
            key = parts[0]
            if key == ".i":
                ni = int(parts[1])
            elif key == ".o":
                no = int(parts[1])
            elif key == ".ilb":
                ilb = parts[1:]
            elif key == ".ob":
                ob = parts[1:]
            elif key == ".type" and parts[1] not in ("fd", "f", "fr"):
                raise ValueError(f"unsupported PLA type {parts[1]}")
            elif key == ".e":
                break
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"bad PLA row {line!r}")
        rows.append((parts[0], parts[1]))
    if ni is None or no is None:
        raise ValueError("PLA missing .i / .o")
    if ni > max_inputs:
        raise ValueError(f"{ni} inputs exceeds cap {max_inputs}")
    inputs = ilb or [f"x{i}" for i in range(ni)]
    outputs = ob or [f"y{j}" for j in range(no)]
    spec = LogicSpec(name, inputs, outputs, {o: set() for o in outputs}, {o: set() for o in outputs})
    for cube, outs in rows:
        if len(cube) != ni or len(outs) != no:
            raise ValueError(f"row width mismatch {cube} {outs}")
        mins = _expand(cube)
        for o, ch in zip(outputs, outs):
            if ch == "1":
                spec.on[o].update(mins)
            elif ch in "-2":
                spec.dc[o].update(mins)
    for o in outputs:
        spec.dc[o] -= spec.on[o]
    return spec


def read_blif(text: str, max_inputs: int = 10) -> LogicSpec:
    """Combinational BLIF with ``.names`` tables (single model, no latches)."""
    lines: list[str] = []
    buf = ""
    for raw in text.splitlines():
        line = raw.split("#")[0].rstrip()
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        lines.append(buf + line)
        buf = ""
    model = "blif"
    inputs: list[str] = []
    outputs: list[str] = []
    tables: list[tuple[list[str], str, list[tuple[str, str]]]] = []
    cur: tuple[list[str], str, list[tuple[str, str]]] | None = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("."):
            parts = s.split()
            key = parts[0]
            if key == ".model":
                model = parts[1] if len(parts) > 1 else model
            elif key == ".inputs":
                inputs += parts[1:]
            elif key == ".outputs":
                outputs += parts[1:]
            elif key == ".names":
                cur = (parts[1:-1], parts[-1], [])
                tables.append(cur)
            elif key == ".end":
                break
            elif key in (".latch", ".subckt", ".gate"):
                raise ValueError(f"unsupported BLIF construct {key}")
            continue
        assert cur is not None, "BLIF cover row before .names"
        parts = s.split()
        if len(parts) == 1:
            cur[2].append(("", parts[0]))
        else:
            cur[2].append((parts[0], parts[1]))
    n = len(inputs)
    if n > max_inputs:
        raise ValueError(f"{n} inputs exceeds cap {max_inputs}")
    by_out = {t[1]: t for t in tables}

    def eval_all(m: int) -> dict[str, int]:
        val = {nm: (m >> (n - 1 - i)) & 1 for i, nm in enumerate(inputs)}

        def get(sig: str) -> int:
            if sig in val:
                return val[sig]
            fanin, _, rows = by_out[sig]
            ins = [get(f) for f in fanin]
            phase = rows[0][1] if rows else "0"
            hit = False
            for pat, outv in rows:
                if all(p == "-" or int(p) == v for p, v in zip(pat, ins)):
                    hit = True
                    break
            res = int(hit) if phase == "1" else int(not hit)
            if not rows:
                res = 0
            val[sig] = res
            return res

        return {o: get(o) for o in outputs}

    spec = LogicSpec(model, inputs, outputs, {o: set() for o in outputs}, {o: set() for o in outputs})
    for m in range(1 << n):
        r = eval_all(m)
        for o in outputs:
            if r[o]:
                spec.on[o].add(m)
    # two-input gate count of the source netlist (tables with exactly 2 inputs)
    spec.gate_count_reference = sum(1 for t in tables if len(t[0]) == 2)
    return spec


def spec_to_states(spec: LogicSpec) -> dict[str, LogicState]:
    return {
        o: LogicState.from_minterms(spec.n, spec.on[o], spec.dc[o], name=f"{spec.name}.{o}")
        for o in spec.outputs
        if spec.on[o]
    }
