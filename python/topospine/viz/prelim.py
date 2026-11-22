"""Save PCA scatters and A-radius bars.  Numbers come from the caller; nothing is invented."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

Point = tuple[float, ...]


def pca2(points: Sequence[Point]) -> list[tuple[float, float]]:
    """First two principal components (numpy SVD).  Centred, not scaled."""
    import numpy as np

    X = np.asarray(points, dtype=float)
    if X.ndim != 2 or X.shape[0] == 0:
        return []
    if X.shape[1] == 1:
        X = np.concatenate([X, np.zeros((len(X), 1))], axis=1)
    X = X - X.mean(axis=0, keepdims=True)
    _u, _s, vt = np.linalg.svd(X, full_matrices=False)
    k = min(2, vt.shape[0])
    coords = X @ vt[:k].T
    if k == 1:
        coords = np.concatenate([coords, np.zeros((len(coords), 1))], axis=1)
    return [(float(a), float(b)) for a, b in coords]


def _scatter(ax, xy, labels, title: str, centres: Sequence[int] | None = None) -> None:
    import numpy as np

    lab = np.asarray(labels)
    for value in sorted(set(int(v) for v in lab)):
        mask = lab == value
        name = "bridge" if value < 0 else f"label {value}"
        ax.scatter(
            [xy[i][0] for i in range(len(xy)) if mask[i]],
            [xy[i][1] for i in range(len(xy)) if mask[i]],
            s=18,
            label=name,
        )
    if centres:
        ax.scatter(
            [xy[i][0] for i in centres if i < len(xy)],
            [xy[i][1] for i in centres if i < len(xy)],
            s=80,
            facecolors="none",
            edgecolors="black",
            linewidths=1.2,
            label="centres",
        )
    ax.set_title(title)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(fontsize=8, frameon=False)
    ax.set_aspect("equal", adjustable="datalim")


def write_prelim_figures(
    out_dir: Path,
    *,
    embedding_points: Sequence[Point],
    embedding_labels: Sequence[int],
    embedding_title: str,
    cloud_points: Sequence[Point] | None = None,
    cloud_labels: Sequence[int] | None = None,
    cloud_centres: Sequence[int] | None = None,
    cloud_title: str = "",
    md_points: Sequence[Point] | None = None,
    md_labels: Sequence[int] | None = None,
    md_title: str = "",
    radius_rows: list[tuple[str, list[float]]] | None = None,
) -> list[Path]:
    """Write PNG files.  Each panel is omitted when its data is missing."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    fig, ax = plt.subplots(figsize=(6.2, 5.0))
    _scatter(ax, pca2(embedding_points), embedding_labels, embedding_title)
    fig.tight_layout()
    p = out_dir / "embeddings_pca.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    written.append(p)

    if cloud_points is not None and cloud_labels is not None:
        fig, ax = plt.subplots(figsize=(6.2, 5.0))
        _scatter(ax, pca2(cloud_points), cloud_labels, cloud_title, cloud_centres)
        fig.tight_layout()
        p = out_dir / "synthetic_cloud_pca.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        written.append(p)

    if md_points is not None and md_labels is not None:
        fig, ax = plt.subplots(figsize=(6.2, 5.0))
        _scatter(ax, pca2(md_points), md_labels, md_title)
        fig.tight_layout()
        p = out_dir / "md17_ethanol_pca.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        written.append(p)

    if radius_rows:
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        n_levels = len(radius_rows[0][1])
        import numpy as np

        x = np.arange(n_levels)
        width = 0.8 / max(len(radius_rows), 1)
        for i, (name, vals) in enumerate(radius_rows):
            ax.bar(x + i * width, vals, width, label=name)
        ax.set_xticks(x + width * (len(radius_rows) - 1) / 2)
        ax.set_xticklabels([f"level {k}" for k in range(n_levels)])
        ax.set_ylabel("A-covering radius")
        ax.set_title("A-radius by method (coarse to fine)")
        ax.legend(fontsize=8, frameon=False)
        fig.tight_layout()
        p = out_dir / "a_radius_bars.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        written.append(p)
    return written
