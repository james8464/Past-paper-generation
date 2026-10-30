# Small, bounded verification contracts. Never execute model-supplied Python.

import ast
import heapq
import operator
import re
import sqlite3


def _trace(code: str, variable: str):
    if not isinstance(code, str) or len(code) > 8000:
        raise ValueError("Programme trop long")
    tree = ast.parse(code)
    if sum(1 for _ in ast.walk(tree)) > 1000:
        raise ValueError("Programme trop complexe")
    environment = {}
    budget = 5000
    binary = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
    }
    comparison = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def tick():
        nonlocal budget
        budget -= 1
        if budget < 0:
            raise ValueError("Limite d'étapes dépassée")

    def bounded(value):
        if type(value) is int and abs(value) <= 10**9:
            return value
        if type(value) is bool or value is None:
            return value
        if isinstance(value, str) and len(value) <= 4096:
            return value
        if isinstance(value, list) and len(value) <= 256:
            for item in value:
                if isinstance(item, list):
                    raise ValueError("Listes imbriquées non prises en charge")
                bounded(item)
            return value
        raise ValueError("Valeur hors limites")

    def expression(node):
        tick()
        if isinstance(node, ast.Constant):
            return bounded(node.value)
        if isinstance(node, ast.Name):
            return environment[node.id]
        if isinstance(node, ast.List):
            return bounded([expression(item) for item in node.elts])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.Not)):
            value = expression(node.operand)
            if isinstance(node.op, ast.Not):
                return not value
            if type(value) is int:
                return bounded(-value)
        if isinstance(node, ast.BinOp) and type(node.op) in binary:
            left, right = expression(node.left), expression(node.right)
            if type(left) is not int or type(right) is not int:
                raise ValueError("Opérations limitées aux entiers")
            return bounded(binary[type(node.op)](left, right))
        if (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and type(node.ops[0]) in comparison
        ):
            return comparison[type(node.ops[0])](
                expression(node.left), expression(node.comparators[0])
            )
        if isinstance(node, ast.Subscript):
            value, index = expression(node.value), expression(node.slice)
            if isinstance(value, (list, str)) and type(index) is int:
                return value[index]
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and not node.keywords
        ):
            args = [expression(arg) for arg in node.args]
            if (
                node.func.id == "range"
                and 1 <= len(args) <= 3
                and all(type(arg) is int for arg in args)
            ):
                result = range(*args)
                if len(result) <= 256:
                    return list(result)
            if (
                node.func.id == "len"
                and len(args) == 1
                and isinstance(args[0], (list, str))
            ):
                return len(args[0])
        raise ValueError("Construction Python non prise en charge")

    def statements(nodes):
        for node in nodes:
            tick()
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                environment[node.targets[0].id] = bounded(expression(node.value))
            elif (
                isinstance(node, ast.For)
                and isinstance(node.target, ast.Name)
                and not node.orelse
            ):
                values = expression(node.iter)
                if not isinstance(values, list):
                    raise ValueError("Itération non prise en charge")
                for value in values:
                    environment[node.target.id] = value
                    statements(node.body)
            elif isinstance(node, ast.If):
                statements(node.body if expression(node.test) else node.orelse)
            else:
                raise ValueError("Instruction Python non prise en charge")

    statements(tree.body)
    return environment[variable]


def _sql(contract, *, sql_materials=None):
    schema, query = contract["schema"], contract["query"]
    if (
        not isinstance(schema, str)
        or not isinstance(query, str)
        or max(len(schema), len(query)) > 8000
    ):
        raise ValueError("Requête hors limites")
    with sqlite3.connect(":memory:") as db:
        # Some Python builds omit extension loading altogether. The authorizer
        # below independently denies load_extension even when SQLite exposes it.
        disable_extensions = getattr(db, "enable_load_extension", None)
        if disable_extensions is not None:
            disable_extensions(False)
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 65536)
        db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8192)
        db.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 64)
        calls = 0
        inspecting = False
        query_tables = None

        def progress():
            nonlocal calls
            calls += 1
            return int(calls > 1000)

        denied = {
            sqlite3.SQLITE_ATTACH,
            sqlite3.SQLITE_DETACH,
            sqlite3.SQLITE_PRAGMA,
            sqlite3.SQLITE_CREATE_VTABLE,
            sqlite3.SQLITE_DROP_VTABLE,
            sqlite3.SQLITE_CREATE_TRIGGER,
            sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
        }

        def authorize(action, arg1, arg2, _database, _trigger):
            if inspecting:
                return sqlite3.SQLITE_OK
            if query_tables is not None:
                if action == sqlite3.SQLITE_READ:
                    return (
                        sqlite3.SQLITE_OK
                        if _database == "main"
                        and arg1 in query_tables
                        and (arg2 in query_tables[arg1] or arg2 == "")
                        else sqlite3.SQLITE_DENY
                    )
                if action not in {
                    sqlite3.SQLITE_SELECT,
                    sqlite3.SQLITE_FUNCTION,
                    sqlite3.SQLITE_RECURSIVE,
                }:
                    return sqlite3.SQLITE_DENY
            if action in denied or (
                action == sqlite3.SQLITE_FUNCTION
                and str(arg2).lower()
                not in {
                    "count",
                    "sum",
                    "min",
                    "max",
                    "avg",
                    "abs",
                    "round",
                    "length",
                    "lower",
                    "upper",
                    "coalesce",
                }
            ):
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        db.set_authorizer(authorize)
        db.set_progress_handler(progress, 100)
        db.executescript(schema)
        tables = contract.get("rows", {})
        if not isinstance(tables, dict) or len(tables) > 12:
            raise ValueError("Trop de tables")
        for table, rows in tables.items():
            if (
                not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", table)
                or not isinstance(rows, list)
                or len(rows) > 256
            ):
                raise ValueError("Table hors limites")
            for row in rows:
                if not isinstance(row, list) or not 1 <= len(row) <= 64:
                    raise ValueError("Ligne hors limites")
                db.execute(
                    f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in row)})', row
                )
        if sql_materials is not None:
            from Backend.Core.france.sql_sources import validate_database

            inspecting = True
            try:
                query_tables = validate_database(db, sql_materials)
            finally:
                inspecting = False
            # Invalidate prepared-statement permissions after owned inspection.
            db.set_authorizer(authorize)
        cursor = db.execute(query)
        if "result_query" in contract:
            cursor = db.execute(contract["result_query"])
        result = cursor.fetchmany(257)
        if len(result) > 256:
            raise ValueError("Résultat hors limites")
        return [list(row) for row in result]


def _shortest_path(contract):
    edges = contract["edges"]
    if not isinstance(edges, list) or len(edges) > 256:
        raise ValueError("Graphe hors limites")
    graph = {}
    for start, end, weight in edges:
        if (
            not isinstance(start, str)
            or not isinstance(end, str)
            or type(weight) is not int
            or not 0 <= weight <= 10**6
        ):
            raise ValueError("Arête invalide")
        graph.setdefault(start, []).append((end, weight))
        graph.setdefault(end, [])
        if contract.get("directed") is False:
            graph[end].append((start, weight))
    start, end = contract["start"], contract["end"]
    if start not in graph or end not in graph:
        raise ValueError("Sommet absent")
    queue, visited = [(0, start)], set()
    while queue:
        distance, node = heapq.heappop(queue)
        if node in visited:
            continue
        if node == end:
            return distance
        visited.add(node)
        for neighbour, weight in graph[node]:
            if neighbour not in visited:
                heapq.heappush(queue, (distance + weight, neighbour))
    raise ValueError("Aucun chemin")


# Compare evidence recursively without Python's bool/int/float coercion.
def _same_typed_value(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if {(type(key), key) for key in actual} != {
            (type(key), key) for key in expected
        }:
            return False
        return all(
            _same_typed_value(value, expected[key]) for key, value in actual.items()
        )
    if isinstance(actual, (list, tuple)):
        return len(actual) == len(expected) and all(
            _same_typed_value(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def verify_contract(contract: dict, *, sql_materials=None) -> dict:
    kind = contract.get("kind")
    if kind not in {
        "binary",
        "sql",
        "python_trace",
        "shortest_path",
        "graph_tree",
        "graph_tree_depth_contract",
        "graph_resilience_contract",
        "graph_route_trace_contract",
        "graph_two_outage_contract",
        "tree_construction_contract",
        "route_selection_contract",
        "route_family_contract",
        "database_contract",
        "database_depth_contract",
        "database_audit_contract",
        "database_reconciliation_contract",
        "database_case_contract",
        "tree_case_contract",
        "system_case_contract",
        "network_contract",
        "network_depth_contract",
        "network_reasoning_contract",
        "network_incident_contract",
        "network_incident_timeline_contract",
    }:
        return {
            "state": "unresolved",
            "passed": False,
            "reason": "Vérification humaine nécessaire",
        }
    try:
        if kind == "system_case_contract":
            from Backend.Core.france.system_case_families import build_case
            from Backend.Core.france.system_case_prose import VERSION

            if set(contract) != {
                "kind",
                "version",
                "seed",
                "case_sha256",
                "task_id",
                "expected",
            }:
                raise ValueError("Whole system case contract fields changed")
            data = build_case(contract["seed"])
            if (
                contract["version"] != VERSION
                or contract["case_sha256"] != data["sha256"]
                or contract["task_id"]
                not in {f"3{letter}" for letter in "abcdefghijkl"}
            ):
                raise ValueError("Whole system case identity mismatch")
            actual = data["expected"]
        elif kind == "tree_case_contract":
            from Backend.Core.france.tree_case_families import build_case
            from Backend.Core.france.tree_case_prose import VERSION

            if set(contract) != {
                "kind",
                "version",
                "seed",
                "case_sha256",
                "task_id",
                "expected",
            }:
                raise ValueError("Whole tree case contract fields changed")
            data = build_case(contract["seed"])
            if (
                contract["version"] != VERSION
                or contract["case_sha256"] != data["sha256"]
                or contract["task_id"] not in {f"1{letter}" for letter in "abcdefghij"}
            ):
                raise ValueError("Whole tree case identity mismatch")
            actual = data["expected"]
        elif kind == "database_case_contract":
            from Backend.Core.france.database_case_families import build_case
            from Backend.Core.france.database_case_prose import VERSION

            if set(contract) != {
                "kind",
                "version",
                "seed",
                "case_sha256",
                "task_id",
                "expected",
            }:
                raise ValueError("Whole database case contract fields changed")
            data = build_case(contract["seed"])
            if (
                contract["version"] != VERSION
                or contract["case_sha256"] != data["sha256"]
                or contract["task_id"]
                not in {f"2{letter}" for letter in "abcdefghijkl"}
            ):
                raise ValueError("Whole database case identity mismatch")
            actual = data["expected"]
        elif kind == "network_incident_timeline_contract":
            from Backend.Core.france.network_incident_timeline_contract import (
                NetworkIncidentTimelineContract,
            )

            data = NetworkIncidentTimelineContract.from_dict(
                contract["contract"]
            ).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de chronologie d'incident réseau absente")
            actual = data["expected"]
        elif kind == "network_incident_contract":
            from Backend.Core.france.network_incident_contract import (
                NetworkIncidentContract,
            )

            data = NetworkIncidentContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche d'incident réseau absente")
            actual = data["expected"]
        elif kind in {
            "graph_two_outage_contract",
            "tree_construction_contract",
            "route_selection_contract",
            "route_family_contract",
        }:
            from Backend.Core.france.graph_two_outage_contract import (
                GraphTwoOutageContract,
            )

            data = GraphTwoOutageContract.from_dict(contract["contract"]).to_dict()
            task_id = contract["task_id"]
            if task_id not in data["task_ids"]:
                raise ValueError("Tâche de double fermeture absente")
            actual = data["expected"][task_id]
            if kind == "tree_construction_contract":
                from Backend.Core.france.tree_construction_authoring import (
                    tree_construction_expected,
                )

                if task_id != "1j":
                    raise ValueError("Tâche de construction d'arbre inconnue")
                actual = tree_construction_expected(data)
            elif kind == "route_family_contract":
                from Backend.Core.france.route_task_families import family_expected

                if task_id not in {"1f", "1g"}:
                    raise ValueError("Tâche de famille de trajet inconnue")
                actual = family_expected(data)
            elif kind == "route_selection_contract":
                from Backend.Core.france.route_selection_authoring import (
                    route_selection_expected,
                )

                if task_id not in {"1f", "1g"}:
                    raise ValueError("Tâche de sélection de trajet inconnue")
                actual = route_selection_expected(data)
        elif kind == "graph_route_trace_contract":
            from Backend.Core.france.graph_route_trace_contract import (
                GraphRouteTraceContract,
            )

            data = GraphRouteTraceContract.from_dict(contract["contract"]).to_dict()
            task_id = contract["task_id"]
            if task_id not in data["task_ids"]:
                raise ValueError("Tâche de trace des trajets absente")
            actual = data["expected"][task_id]
        elif kind == "graph_resilience_contract":
            from Backend.Core.france.graph_resilience_contract import (
                GraphResilienceContract,
            )

            data = GraphResilienceContract.from_dict(contract["contract"]).to_dict()
            task_id = contract["task_id"]
            if task_id not in data["task_ids"]:
                raise ValueError("Tâche de résilience graphe absente")
            actual = data["expected"][task_id]
        elif kind == "network_reasoning_contract":
            from Backend.Core.france.network_reasoning_contract import (
                NetworkReasoningContract,
            )

            data = NetworkReasoningContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de raisonnement réseau absente")
            actual = data["expected"]
        elif kind == "graph_tree_depth_contract":
            from Backend.Core.france.graph_tree_depth_contract import (
                GraphTreeDepthContract,
            )

            data = GraphTreeDepthContract.from_dict(contract["contract"]).to_dict()
            task_id = contract["task_id"]
            if task_id not in data["task_ids"]:
                raise ValueError("Tâche de graphe/arbre approfondie absente")
            actual = data["expected"][task_id]
        elif kind == "network_depth_contract":
            from Backend.Core.france.network_depth_contract import NetworkDepthContract

            data = NetworkDepthContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de réseau approfondi absente")
            actual = data["expected"]
        elif kind == "network_contract":
            from Backend.Core.france.network_contract import NetworkContract

            data = NetworkContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de réseau absente")
            actual = data["expected"]
        elif kind == "database_reconciliation_contract":
            from Backend.Core.france.database_reconciliation_contract import (
                DatabaseReconciliationContract,
            )

            data = DatabaseReconciliationContract.from_dict(
                contract["contract"]
            ).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de réconciliation d'incidents absente")
            actual = data["expected"]
            if "construction_version" in contract:
                from Backend.Core.france.database_construction_authoring import (
                    construction_expected,
                )

                if contract["construction_version"] != "v28" or contract[
                    "task_id"
                ] not in {"2h", "2l"}:
                    raise ValueError("Contrat de construction inconnu")
                actual = construction_expected(data)
        elif kind == "database_audit_contract":
            from Backend.Core.france.database_audit_contract import (
                DatabaseAuditContract,
            )

            data = DatabaseAuditContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche d'audit d'incidents absente")
            actual = data["expected"]
        elif kind == "database_depth_contract":
            from Backend.Core.france.database_depth_contract import (
                DatabaseDepthContract,
            )

            data = DatabaseDepthContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de base de données approfondie absente")
            actual = data["expected"]
        elif kind == "database_contract":
            from Backend.Core.france.database_contract import DatabaseContract

            data = DatabaseContract.from_dict(contract["contract"]).to_dict()
            if contract["task_id"] not in data["task_ids"]:
                raise ValueError("Tâche de base de données absente")
            actual = data["expected"]
        elif kind == "graph_tree":
            from Backend.Core.france.graph_tree_contract import GraphTreeContract

            data = GraphTreeContract.from_dict(contract["contract"]).to_dict()
            task_id = contract["task_id"]
            if task_id not in data["task_ids"]:
                raise ValueError("Tâche de graphe/arbre absente")
            actual = data["expected"][task_id]
        elif kind == "binary":
            value = contract["input"]
            if not isinstance(value, str) or not re.fullmatch(r"[01]{1,64}", value):
                raise ValueError("Nombre binaire invalide")
            actual = int(value, 2)
        elif kind == "sql":
            actual = _sql(contract, sql_materials=sql_materials)
        elif kind == "python_trace":
            actual = _trace(contract["code"], contract["variable"])
        else:
            actual = _shortest_path(contract)
        passed = _same_typed_value(actual, contract["expected"])
        return {
            "state": "passed" if passed else "failed",
            "passed": passed,
            "actual": actual,
        }
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        SyntaxError,
        ArithmeticError,
        sqlite3.Error,
        RecursionError,
    ) as error:
        return {"state": "failed", "passed": False, "reason": str(error)}
