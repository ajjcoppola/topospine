"""Embedding point clouds for relative spines.

Two sources, both local:

* :func:`synthetic_embedding_cloud` — seeded Gaussian blobs joined by bridge
  points.  Always available; this is the CI default.
* :func:`load_embedding_npz` — a ``.npz`` with ``embeddings`` (N, D) and
  ``labels`` (N,).  Optional ``sentences`` (N,).  :func:`try_embedding_npz`
  reads ``TOPOSPINE_EMB_NPZ`` only.  No download is attempted.

:func:`write_minilm_npz` encodes a fixed sentence list with
``sentence-transformers`` when that package is installed (the MiniLM weights
must already be cached or the call is allowed to fetch them).  It is a data
prep tool, not part of the certificate path.
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path
from typing import Sequence

Point = tuple[float, ...]

# Four topics, six sentences.  Encoded once into data/embeddings_minilm_tiny.npz.
MINILM_SENTENCES: list[tuple[str, int]] = [
    ("The mitochondrion produces ATP for the cell.", 0),
    ("DNA polymerase copies the genome during replication.", 0),
    ("Photosynthesis converts light into chemical energy.", 0),
    ("Ribosomes translate messenger RNA into protein.", 0),
    ("Neurons transmit signals across synapses.", 0),
    ("Enzymes lower the activation energy of reactions.", 0),
    ("A Boolean function maps bit strings to bits.", 1),
    ("Prime implicants cover the on-set of a circuit.", 1),
    ("An and-inverter graph is a logic network.", 1),
    ("Don't-care minterms need not be covered.", 1),
    ("Branch and bound searches a covering table.", 1),
    ("A cyclic core has no essential columns.", 1),
    ("A torus has two independent one-dimensional holes.", 2),
    ("The two-sphere is simply connected.", 2),
    ("A free face collapses in simple homotopy.", 2),
    ("Vietoris-Rips connects nearby points by edges.", 2),
    ("Cup length bounds the size of a cover.", 2),
    ("Betti numbers count homology classes.", 2),
    ("The train arrives at the central station at noon.", 3),
    ("Pack a raincoat for the coastal hike.", 3),
    ("The museum opens on Monday mornings.", 3),
    ("A ferry crosses the bay every hour.", 3),
    ("Street markets sell fruit in the old town.", 3),
    ("The hotel is two blocks from the river.", 3),
]


def synthetic_embedding_cloud(
    n_per: int = 16,
    dim: int = 8,
    n_clusters: int = 4,
    n_bridge: int = 8,
    seed: int = 1,
    noise: float = 0.12,
) -> tuple[list[Point], list[int], dict]:
    """Blobs on a circle in the first two coordinates, plus bridges between neighbours.

    Bridge points are labelled ``-1`` so a class label can be used as the
    designated subset A without absorbing the bridges.
    """
    rng = random.Random(seed)
    points: list[Point] = []
    labels: list[int] = []
    centres: list[list[float]] = []
    for k in range(n_clusters):
        ang = 2 * math.pi * k / n_clusters
        centre = [0.0] * dim
        centre[0] = 2.2 * math.cos(ang)
        centre[1] = 2.2 * math.sin(ang)
        centres.append(centre)
        for _ in range(n_per):
            pt = tuple(centre[d] + rng.gauss(0, noise) for d in range(dim))
            points.append(pt)
            labels.append(k)
    for k in range(n_clusters):
        a, b = centres[k], centres[(k + 1) % n_clusters]
        for j in range(1, n_bridge + 1):
            t = j / (n_bridge + 1)
            mid = [(1 - t) * a[d] + t * b[d] for d in range(dim)]
            pt = tuple(mid[d] + rng.gauss(0, noise * 0.5) for d in range(dim))
            points.append(pt)
            labels.append(-1)
    meta = {
        "source": "synthetic",
        "n_clusters": n_clusters,
        "n_per": n_per,
        "n_bridge_per_edge": n_bridge,
        "dim": dim,
        "seed": seed,
        "bridge_label": -1,
    }
    return points, labels, meta


def suggest_base_scale(points: Sequence[Point], knn: int = 4) -> float:
    """A coarse scale: median distance from each point to its ``knn``-th neighbour."""
    if len(points) < 2:
        return 1.0
    dists = []
    for i, p in enumerate(points):
        ds = sorted(
            math.sqrt(sum((x - y) ** 2 for x, y in zip(p, q)))
            for j, q in enumerate(points)
            if j != i
        )
        dists.append(ds[min(knn, len(ds) - 1)])
    dists.sort()
    return dists[len(dists) // 2]


def load_embedding_npz(path: str | Path) -> tuple[list[Point], list[int], dict]:
    import numpy as np

    path = Path(path)
    data = np.load(path, allow_pickle=False)
    if "embeddings" not in data.files or "labels" not in data.files:
        raise ValueError(f"{path} needs arrays 'embeddings' and 'labels', got {data.files}")
    emb = data["embeddings"]
    labels = [int(x) for x in data["labels"].tolist()]
    if emb.shape[0] != len(labels):
        raise ValueError("embeddings and labels have different lengths")
    points = [tuple(float(x) for x in row) for row in emb]
    meta: dict = {
        "source": "npz",
        "file": path.name,
        "dim": int(emb.shape[1]),
        "n": int(emb.shape[0]),
    }
    if "sentences" in data.files:
        meta["sentences"] = [str(s) for s in data["sentences"].tolist()]
    return points, labels, meta


def try_embedding_npz() -> tuple[list[Point], list[int], dict] | None:
    """Load ``TOPOSPINE_EMB_NPZ`` when it points at an existing file.  No download."""
    raw = os.environ.get("TOPOSPINE_EMB_NPZ")
    if not raw or not Path(raw).exists():
        return None
    return load_embedding_npz(raw)


def write_minilm_npz(path: str | Path, pairs: Sequence[tuple[str, int]] | None = None) -> Path:
    """Encode ``pairs`` (sentence, label) with all-MiniLM-L6-v2 and write a compressed npz."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    pairs = list(pairs) if pairs is not None else list(MINILM_SENTENCES)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    emb = model.encode([s for s, _ in pairs], normalize_embeddings=True)
    np.savez_compressed(
        path,
        embeddings=np.asarray(emb, dtype=np.float32),
        labels=np.asarray([lab for _, lab in pairs], dtype=np.int32),
        sentences=np.asarray([s for s, _ in pairs]),
    )
    return path


def indices_with_label(labels: Sequence[int], label: int) -> list[int]:
    return [i for i, y in enumerate(labels) if y == label]
