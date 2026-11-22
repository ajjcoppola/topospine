"""Abstract simplicial complexes and flag strong collapse (weak neighborhood)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class SimplicialComplex:
    vertices: set[int]
    faces: set[frozenset[int]]  # maximal faces

    @classmethod
    def from_maximal_faces(cls, maximal: Iterable[Iterable[int]]) -> SimplicialComplex:
        faces = {frozenset(f) for f in maximal}
        verts: set[int] = set()
        for f in faces:
            verts |= set(f)
        return cls(vertices=verts, faces=faces)

    def all_faces(self) -> set[frozenset[int]]:
        out: set[frozenset[int]] = set()
        for mf in self.faces:
            mf_list = sorted(mf)
            for mask in range(1, 1 << len(mf_list)):
                out.add(frozenset(mf_list[i] for i in range(len(mf_list)) if mask & (1 << i)))
        return out

    def as_simplex_list(self) -> list[frozenset[int]]:
        return sorted(self.all_faces(), key=lambda s: (len(s), sorted(s)))


def closed_neighborhood(graph: dict[int, set[int]], v: int, verts: set[int]) -> set[int]:
    return (graph.get(v, {v}) | {v}) & verts


def is_collapsible_flag(complex: SimplicialComplex) -> bool:
    """
    Strong collapse on flag 1-skeleton using *weak* closed-neighborhood inclusion:

        N[v] ⊆ N[u] for some u ≠ v  (equality allowed when v is dominated including twins).

    Then elementary free-face collapse of remaining tree-like residue.
    Collapsible iff reduction reaches ≤ 1 vertex.
    """
    if not complex.vertices:
        return True
    edges = {f for f in complex.all_faces() if len(f) == 2}
    graph: dict[int, set[int]] = {v: {v} for v in complex.vertices}
    for e in edges:
        a, b = tuple(e)
        graph[a].add(b)
        graph[b].add(a)
    verts = set(complex.vertices)
    changed = True
    while changed:
        changed = False
        for v in list(verts):
            nv = closed_neighborhood(graph, v, verts)
            for u in verts:
                if u == v:
                    continue
                nu = closed_neighborhood(graph, u, verts)
                # Weak inclusion: N[v] ⊆ N[u]
                if nv <= nu:
                    verts.remove(v)
                    changed = True
                    break
            if changed:
                break
    return len(verts) <= 1
