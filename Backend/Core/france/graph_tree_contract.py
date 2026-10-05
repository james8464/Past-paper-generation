"""Seeded, student-visible facts for the French NSI graph/tree exercise.

The model may author prose around these facts, but it cannot author the facts.
No model-generated code is executed here.
"""

from __future__ import annotations

import heapq
import json
import random
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise

_NODES = ("A", "B", "C", "D", "E", "F")
_TASK_IDS = ("1a", "1b", "1c", "1d", "1e", "1f")
_NODE_API = (
    "class Noeud:\n"
    "    def __init__(self, valeur):\n"
    "        self.valeur = valeur\n"
    "        self.gauche = None\n"
    "        self.droite = None"
)
_FAULTY_BFS = (
    "def parcours_largeur(reseau, depart):\n"
    "    visites = {depart}\n"
    "    file = [depart]\n"
    "    ordre = []\n"
    "    while file:\n"
    "        sommet = file.pop(0)\n"
    "        ordre.append(sommet)\n"
    "        for voisin in reseau[sommet]:\n"
    "            if visin not in visites:\n"
    "                visites.add(voisin)\n"
    "                file.append(voisin)\n"
    "    return ordre"
)
_CORRECTED_BFS = _FAULTY_BFS.replace("if visin not in visites:", "if voisin not in visites:")


def _run_trusted_bfs(source: str, graph: dict[str, list[str]]) -> list[str]:
    """Execute only the two fixed, application-owned snippets, never model code."""
    if source not in {_FAULTY_BFS, _CORRECTED_BFS}:
        raise ValueError("Unknown trusted debugging code")
    namespace: dict = {}
    exec(source, {"__builtins__": {}}, namespace)
    return namespace["parcours_largeur"](graph, "A")


def _debug_case(adjacency: dict[str, list[tuple[str, int]]]) -> dict:
    input_graph = {
        node: [neighbor for neighbor, _ in edges] for node, edges in adjacency.items()
    }
    try:
        _run_trusted_bfs(_FAULTY_BFS, input_graph)
    except NameError as error:
        if "visin" not in str(error):
            raise ValueError("Unexpected debugging fault") from error
    else:
        raise ValueError("Faulty debugging code did not fail")
    corrected = _run_trusted_bfs(_CORRECTED_BFS, input_graph)
    return {
        "faulty_code": _FAULTY_BFS,
        "input": input_graph,
        "start": "A",
        "expected_error": "NameError",
        "corrected_order": corrected,
    }


def _graph_adjacency(graph: dict) -> dict[str, list[tuple[str, int]]]:
    if (
        graph.get("id") != "reseau"
        or graph.get("nodes") != list(_NODES)
        or graph.get("directed") is not False
    ):
        raise ValueError("Invalid graph material")
    edges = graph.get("edges")
    if not isinstance(edges, list) or not 5 <= len(edges) <= 12:
        raise ValueError("Invalid graph edges")
    adjacency: dict[str, list[tuple[str, int]]] = {node: [] for node in _NODES}
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        if (
            not isinstance(edge, list)
            or len(edge) != 3
            or edge[0] not in adjacency
            or edge[1] not in adjacency
            or edge[0] == edge[1]
            or type(edge[2]) is not int
            or not 1 <= edge[2] <= 100
        ):
            raise ValueError("Invalid graph edge")
        pair = tuple(sorted(edge[:2]))
        if pair in seen:
            raise ValueError("Duplicate graph edge")
        seen.add(pair)
        a, b, weight = edge
        adjacency[a].append((b, weight))
        adjacency[b].append((a, weight))
    for neighbours in adjacency.values():
        neighbours.sort()
    reached = {"A"}
    pending = ["A"]
    while pending:
        current = pending.pop()
        for neighbour, _ in adjacency[current]:
            if neighbour not in reached:
                reached.add(neighbour)
                pending.append(neighbour)
    if reached != set(_NODES):
        raise ValueError("Disconnected graph")
    return adjacency


def _tree_nodes(tree: dict) -> dict[int, tuple[int | None, int | None]]:
    if tree.get("id") != "arbre" or tree.get("columns") != ["cle", "gauche", "droite"]:
        raise ValueError("Invalid BST material")
    rows = tree.get("rows")
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError("Invalid BST rows")
    nodes: dict[int, tuple[int | None, int | None]] = {}
    for row in rows:
        if (
            not isinstance(row, list)
            or len(row) != 3
            or type(row[0]) is not int
            or not 0 <= row[0] <= 999
            or any(child is not None and type(child) is not int for child in row[1:])
        ):
            raise ValueError("Invalid BST row")
        key = row[0]
        if key in nodes:
            raise ValueError("Duplicate BST key")
        nodes[key] = (row[1], row[2])
    root = tree.get("root")
    insert_key = tree.get("insert_key")
    if (
        type(root) is not int
        or root not in nodes
        or type(insert_key) is not int
        or not 0 <= insert_key <= 999
        or insert_key in nodes
    ):
        raise ValueError("Invalid BST root or insertion key")
    parents: dict[int, int] = {}
    for key, children in nodes.items():
        for child in children:
            if child is None:
                continue
            if child not in nodes or child in parents or child == root:
                raise ValueError("Invalid BST parent")
            parents[child] = key
    if set(parents) != set(nodes) - {root}:
        raise ValueError("Disconnected BST")

    def visit(key: int, lower: int, upper: int) -> None:
        if not lower < key < upper:
            raise ValueError("BST order violation")
        left, right = nodes[key]
        if left is not None:
            visit(left, lower, key)
        if right is not None:
            visit(right, key, upper)

    visit(root, -1, 1000)
    return nodes


def _expected(graph: dict, tree: dict, debug_case: dict) -> dict:
    adjacency = _graph_adjacency(graph)
    nodes = _tree_nodes(tree)
    if debug_case != _debug_case(adjacency):
        raise ValueError("Invalid debugging code or test case")
    queue = [(0, ("A",), "A")]
    best: dict[str, tuple[int, tuple[str, ...]]] = {"A": (0, ("A",))}
    while queue:
        weight, path, current = heapq.heappop(queue)
        if best[current] != (weight, path):
            continue
        for neighbour, edge_weight in adjacency[current]:
            candidate = (weight + edge_weight, (*path, neighbour))
            if neighbour not in best or candidate < best[neighbour]:
                best[neighbour] = candidate
                heapq.heappush(queue, (*candidate, neighbour))
    shortest_weight, shortest_path = best["F"]
    bfs = []
    queued = {"A"}
    pending = deque(["A"])
    while pending:
        current = pending.popleft()
        bfs.append(current)
        for neighbour, _ in adjacency[current]:
            if neighbour not in queued:
                queued.add(neighbour)
                pending.append(neighbour)
    insertion = tree["insert_key"]
    current = tree["root"]
    search_path = []
    while True:
        search_path.append(current)
        left, right = nodes[current]
        child = left if insertion < current else right
        if child is None:
            break
        current = child
    return {
        "1a": {"path": list(shortest_path), "weight": shortest_weight},
        "1b": {
            "neighbours": [node for node, _ in adjacency["A"]],
            "weight_sum": sum(weight for _, weight in adjacency["A"]),
        },
        "1c": {
            "fault": "misspelled_neighbour",
            "correct_name": "voisin",
            "corrected_order": debug_case["corrected_order"],
        },
        "1d": {"order": bfs},
        "1e": {"search_path": search_path, "insert_key": insertion},
        "1f": {"inorder": sorted([*nodes, insertion])},
    }


@dataclass(frozen=True)
class GraphTreeContract:
    """Immutable canonical JSON; callers receive fresh copies of its data."""

    _json: str

    def to_dict(self) -> dict:
        return json.loads(self._json)

    @property
    def digest(self) -> str:
        return sha256(self._json.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, data: dict) -> GraphTreeContract:
        if (
            not isinstance(data, dict)
            or data.get("version") != 2
            or type(data.get("seed")) is not int
            or data.get("exercise_id") != "1"
            or data.get("task_ids") != list(_TASK_IDS)
            or data.get("node_api") != _NODE_API
        ):
            raise ValueError("Invalid graph/tree contract identity")
        graph = data.get("graph")
        tree = data.get("tree")
        if not isinstance(graph, dict) or not isinstance(tree, dict):
            raise ValueError("Missing graph/tree material")
        expected = _expected(graph, tree, data.get("debug_case"))
        if "expected" in data and data["expected"] != expected:
            raise ValueError("Canonical result does not match contract data")
        canonical = {**data, "expected": expected}
        if set(canonical) != {
            "version",
            "seed",
            "exercise_id",
            "task_ids",
            "node_api",
            "graph",
            "tree",
            "debug_case",
            "expected",
        }:
            raise ValueError("Unexpected graph/tree contract field")
        return cls(
            json.dumps(
                canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        )


def build_graph_tree_contract(seed: int, exercise_id: str) -> GraphTreeContract:
    """Make one small, connected graph and a separate valid BST for a seed."""
    if type(seed) is not int or exercise_id != "1":
        raise ValueError("Unsupported graph/tree seed or exercise")
    rng = random.Random(f"french-nsi-graph-tree-v1:{seed}:{exercise_id}")
    edges = [[a, b, rng.randint(2, 9)] for a, b in pairwise(_NODES)]
    edges.extend(
        [a, b, rng.randint(6, 16)]
        for a, b in (("A", "C"), ("B", "D"), ("C", "E"), ("D", "F"))
    )
    keys = rng.sample(range(10, 100), 5)
    insert_key = next(
        value for value in rng.sample(range(10, 100), 90) if value not in keys
    )
    children: dict[int, list[int | None]] = {key: [None, None] for key in keys}
    for key in keys[1:]:
        parent = keys[0]
        while True:
            direction = 0 if key < parent else 1
            child = children[parent][direction]
            if child is None:
                children[parent][direction] = key
                break
            parent = child
    graph = {
        "id": "reseau",
        "nodes": list(_NODES),
        "edges": edges,
        "directed": False,
    }
    return GraphTreeContract.from_dict(
        {
            "version": 2,
            "seed": seed,
            "exercise_id": exercise_id,
            "task_ids": list(_TASK_IDS),
            "node_api": _NODE_API,
            "graph": graph,
            "debug_case": _debug_case(_graph_adjacency(graph)),
            "tree": {
                "id": "arbre",
                "columns": ["cle", "gauche", "droite"],
                "root": keys[0],
                "rows": [[key, *children[key]] for key in keys],
                "insert_key": insert_key,
            },
        }
    )
