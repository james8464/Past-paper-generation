"""Immutable app-owned facts for the V17 French graph/tree reasoning sequence.

The older six-question graph/tree contract is intentionally left unchanged.
Only trusted, fixed application code appears in the candidate material.
"""

from __future__ import annotations

import heapq
import json
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise

from Backend.Core.france.graph_tree_contract import build_graph_tree_contract

_NODES = ("A", "B", "C", "D", "E", "F")
_TASK_IDS = tuple(f"1{letter}" for letter in "abcdefghij")
_DETOUR = ("A", "C", "E", "F")
_FAULTY_SEARCH = (
    "def contient(noeud, cle):\n"
    "    if noeud is None:\n"
    "        return False\n"
    "    if cle == noeud.valeur:\n"
    "        return True\n"
    "    if cle > noeud.valeur:\n"
    "        return contient(noeud.gauche, cle)\n"
    "    return contient(noeud.droite, cle)"
)


def _canonical(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _adjacency(graph: dict) -> dict[str, list[tuple[str, int]]]:
    adjacent: dict[str, list[tuple[str, int]]] = {node: [] for node in _NODES}
    for left, right, weight in graph["edges"]:
        adjacent[left].append((right, weight))
        adjacent[right].append((left, weight))
    for neighbours in adjacent.values():
        neighbours.sort()
    return adjacent


def _dijkstra_steps(
    adjacency: dict[str, list[tuple[str, int]]],
) -> tuple[list[dict], dict]:
    """Trace the first two settled vertices and cross-check the final path."""
    best: dict[str, tuple[int, tuple[str, ...]]] = {"A": (0, ("A",))}
    previous: dict[str, str] = {}
    queue = [(0, ("A",), "A")]
    settled: set[str] = set()
    steps: list[dict] = []
    while queue:
        distance, path, node = heapq.heappop(queue)
        if node in settled or best[node] != (distance, path):
            continue
        settled.add(node)
        for neighbour, weight in adjacency[node]:
            if neighbour in settled:
                continue
            candidate = (distance + weight, (*path, neighbour))
            if neighbour not in best or candidate < best[neighbour]:
                best[neighbour] = candidate
                previous[neighbour] = node
                heapq.heappush(queue, (*candidate, neighbour))
        if len(steps) < 2:
            steps.append(
                {
                    "settled": node,
                    "tentative": {
                        vertex: best[vertex][0] if vertex in best else None
                        for vertex in _NODES
                    },
                    "predecessors": dict(sorted(previous.items())),
                }
            )
    if len(settled) != len(_NODES) or len(steps) != 2:
        raise ValueError("Graph traversal incomplete")
    return steps, {"path": list(best["F"][1]), "weight": best["F"][0]}


def _bfs_states(adjacency: dict[str, list[tuple[str, int]]]) -> list[dict]:
    queue = deque(["A"])
    visited = {"A"}
    states = []
    for _ in range(2):
        current = queue.popleft()
        for neighbour, _weight in adjacency[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
        states.append(
            {"dequeued": current, "queue": list(queue), "visited": sorted(visited)}
        )
    return states


def _facts(seed: int) -> dict:
    if type(seed) is not int:
        raise ValueError("Unsupported graph/tree depth seed")
    base = build_graph_tree_contract(seed, "1").to_dict()
    graph = base["graph"]
    adjacency = _adjacency(graph)
    steps, shortest = _dijkstra_steps(adjacency)
    if shortest != base["expected"]["1a"]:
        raise ValueError("Graph route trace disagrees with fixed contract")
    weights = {frozenset((a, b)): weight for a, b, weight in graph["edges"]}
    detour_weight = sum(
        weights[frozenset((left, right))] for left, right in pairwise(_DETOUR)
    )
    insertion = base["expected"]["1e"]
    parent = insertion["search_path"][-1]
    expected = {
        "1a": {
            "neighbours": [name for name, _weight in adjacency["A"]],
            "degree": len(adjacency["A"]),
            "incident_weight": sum(weight for _name, weight in adjacency["A"]),
        },
        "1b": {"path": list(_DETOUR), "weight": detour_weight},
        "1c": {"steps": steps},
        "1d": shortest,
        "1e": {"states": _bfs_states(adjacency)},
        "1f": {"error": "NameError", "misspelled": "visin", "correct_name": "voisin"},
        "1g": {"order": base["expected"]["1d"]["order"], "reason": "enqueue_once"},
        "1h": {
            **insertion,
            "parent": parent,
            "side": "gauche" if insertion["insert_key"] < parent else "droite",
        },
        "1i": {"inorder": base["expected"]["1f"]["inorder"]},
        "1j": {
            "wrong_comparison": ">",
            "correct_comparison": "<",
            "search_path": [*insertion["search_path"], insertion["insert_key"]],
            "found": True,
        },
    }
    return {
        "version": 3,
        "seed": seed,
        "exercise_id": "1",
        "task_ids": list(_TASK_IDS),
        "node_api": base["node_api"],
        "graph": graph,
        "tree": base["tree"],
        "debug_case": base["debug_case"],
        "search_code": _FAULTY_SEARCH,
        "expected": expected,
    }


@dataclass(frozen=True)
class GraphTreeDepthContract:
    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> GraphTreeDepthContract:
        if not isinstance(data, dict) or type(data.get("seed")) is not int:
            raise ValueError("Invalid graph/tree depth contract")
        canonical = _facts(data["seed"])
        if _canonical(data) != _canonical(canonical):
            raise ValueError("Graph/tree depth facts differ from application contract")
        return cls(_canonical(canonical))


def build_graph_tree_depth_contract(seed: int) -> GraphTreeDepthContract:
    return GraphTreeDepthContract.from_dict(_facts(seed))
