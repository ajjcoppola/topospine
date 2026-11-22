"""Synthetic embedding clouds, npz loader, and nearest-neighbour recall."""

from __future__ import annotations

import pytest

from topospine.embeddings.clouds import (
    load_embedding_npz,
    suggest_base_scale,
    synthetic_embedding_cloud,
    try_embedding_npz,
)
from topospine.spines.relative_tower import nn_recall_A


def test_synthetic_cloud_is_deterministic_and_has_bridges():
    p1, y1, m1 = synthetic_embedding_cloud()
    p2, y2, _ = synthetic_embedding_cloud()
    assert p1 == p2 and y1 == y2
    assert m1["source"] == "synthetic"
    assert y1.count(-1) == m1["n_clusters"] * m1["n_bridge_per_edge"]
    assert y1.count(0) == m1["n_per"]
    assert suggest_base_scale(p1) > 0


def test_nn_recall_extremes():
    pts, labels, _ = synthetic_embedding_cloud(n_per=6, n_bridge=2, seed=2)
    A = [i for i, y in enumerate(labels) if y == 0]
    # each point is its own centre, so a neighbour sits in a different piece
    assert nn_recall_A(pts, A, list(range(len(pts)))) == 0.0
    # one centre for the whole cloud: every neighbour shares it
    assert nn_recall_A(pts, A, [A[0]]) == 1.0


def test_npz_roundtrip_and_env(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    pts, labels, _ = synthetic_embedding_cloud(n_per=4, n_bridge=1, dim=3, seed=3)
    path = tmp_path / "emb.npz"
    np.savez(path, embeddings=np.asarray(pts), labels=np.asarray(labels))
    loaded, y, meta = load_embedding_npz(path)
    assert len(loaded) == len(pts) and y == labels and meta["dim"] == 3
    monkeypatch.delenv("TOPOSPINE_EMB_NPZ", raising=False)
    assert try_embedding_npz() is None
    monkeypatch.setenv("TOPOSPINE_EMB_NPZ", str(path))
    assert try_embedding_npz() is not None
    bad = tmp_path / "bad.npz"
    np.savez(bad, foo=np.zeros(3))
    with pytest.raises(ValueError):
        load_embedding_npz(bad)
