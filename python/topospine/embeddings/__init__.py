"""Point clouds from embeddings: synthetic clusters and a local ``.npz`` loader."""

from topospine.embeddings.clouds import (
    load_embedding_npz,
    suggest_base_scale,
    synthetic_embedding_cloud,
    try_embedding_npz,
    write_minilm_npz,
)

__all__ = [
    "load_embedding_npz",
    "suggest_base_scale",
    "synthetic_embedding_cloud",
    "try_embedding_npz",
    "write_minilm_npz",
]
