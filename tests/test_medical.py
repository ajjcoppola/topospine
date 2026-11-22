import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "applications" / "medical"))

from pipeline import reduce_volume, synthetic_blob  # noqa: E402


def test_synthetic_volume_reduces_or_certifies():
    out = reduce_volume(synthetic_blob((6, 6, 6), radius=2.0), (6, 6, 6))
    assert out["cells_before"] > 0
    assert out["cells_after"] <= out["cells_before"]
    assert out["wall_time_s"] >= 0
