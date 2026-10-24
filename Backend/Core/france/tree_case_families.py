"""Original whole-tree cases for the unreleased V32 draft.

Fixed application algorithms only. Independent flat/iterative/prefix-table
oracles check answers; no model-supplied code or expressions are executed.
"""

import json
from copy import deepcopy
from hashlib import sha256

VERSION = "fr-nsi-tree-cases-v1"
FAMILIES = ("rank", "expression", "prefix")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def count_below(nodes, root, limit):
    """Strict BST, unique integer keys; count keys strictly below limit."""
    if root is None:
        return 0
    key, left, right = nodes[root]
    if key >= limit:
        return count_below(nodes, left, limit)
    return 1 + count_below(nodes, left, limit) + count_below(nodes, right, limit)


def expression_value(nodes, root):
    """Full binary tree: integer leaves; internal +, - or * operators."""
    value, left, right = nodes[root]
    if left is None:
        return value
    a = expression_value(nodes, left)
    b = expression_value(nodes, right)
    if value == "+":
        return a + b
    if value == "-":
        return a - b
    return a * b


def count_interval(nodes, root, low, high):
    """Reuse strict ranks for inclusive integer bounds low <= high."""
    return count_below(nodes, root, high + 1) - count_below(nodes, root, low)


def decode_message(nodes, root, bits):
    """Full prefix tree with distinct letter leaves; 0 left, 1 right.

    Empty message is valid. Reject non-bits and a final incomplete code word.
    Reset to root after each emitted leaf. No mutation of the code tree.
    """
    output = ""
    current = root
    for bit in bits:
        if bit not in ("0", "1"):
            raise ValueError("Non-binary symbol")
        _, left, right = nodes[current]
        current = left if bit == "0" else right
        value, left, right = nodes[current]
        if left is None:
            output += value
            current = root
    if current != root:
        raise ValueError("Incomplete code word")
    return output


def transcode(nodes, root, bits, new_codes):
    """Decode old bits, then encode the same letters with the supplied new code.

    Precondition: new_codes contains a valid nonempty prefix code for every
    letter in the old alphabet. No optimal-code construction is required.
    """
    message = decode_message(nodes, root, bits)
    output = ""
    for letter in message:
        output += new_codes[letter]
    return output


def _shape(rows, root, family):
    """Check the complete tree, not only parent/child local relationships."""
    if family not in FAMILIES:
        raise ValueError("Unknown tree case family")
    nodes = {}
    for row in rows:
        if len(row) != 4 or type(row[0]) is not str or row[0] in nodes:
            raise ValueError("Duplicate or malformed tree row")
        nodes[row[0]] = tuple(row[1:])
    pending, visited, depths = [(root, 0, None, None)], set(), {}
    while pending:
        node, depth, low, high = pending.pop()
        if node not in nodes or node in visited:
            raise ValueError("Missing, shared or cyclic tree node")
        visited.add(node)
        depths[node] = depth
        value, left, right = nodes[node]
        if family == "rank":
            if (
                type(value) is not int
                or (low is not None and value <= low)
                or (high is not None and value >= high)
            ):
                raise ValueError("Strict BST ordering violated")
        elif (left is None) != (right is None):
            raise ValueError("Expected full binary tree")
        elif family == "expression":
            if (left is None and type(value) is not int) or (
                left is not None and value not in ("+", "-", "*")
            ):
                raise ValueError("Invalid expression node")
        elif (left is None and (type(value) is not str or len(value) != 1)) or (
            left is not None and value is not None
        ):
            raise ValueError("Invalid prefix node")
        if right is not None:
            pending.append(
                (right, depth + 1, value if family == "rank" else None, high)
            )
        if left is not None:
            pending.append((left, depth + 1, low, value if family == "rank" else None))
    if visited != set(nodes):
        raise ValueError("Unreachable tree nodes")
    if family == "prefix" and nodes[root][1] is None:
        raise ValueError("A prefix alphabet needs nonempty code words")
    leaves = [
        node
        for node, (_, left, right) in nodes.items()
        if left is None and right is None
    ]
    if family == "prefix" and len({nodes[n][0] for n in leaves}) != len(leaves):
        raise ValueError("Ambiguous repeated prefix letter")
    return nodes, dict(
        size=len(nodes), height=max(depths.values()), leaves=leaves, depths=depths
    )


def _expression_oracle(nodes, root):
    """Bottom-up dependency evaluation, independent of recursive solution."""
    values, order = {}, []
    pending = [(root, False)]
    while pending:
        node, ready = pending.pop()
        value, left, right = nodes[node]
        if left is None:
            values[node] = value
            order.append(node)
        elif ready:
            a, b = values[left], values[right]
            values[node] = {"+": a + b, "-": a - b, "*": a * b}[value]
            order.append(node)
        else:
            pending.extend([(node, True), (right, False), (left, False)])
    return values[root], dict(values=values, postorder=order)


def _prefix_oracle(nodes, root, bits):
    """Enumerate leaf code words first; tokenize without walking the tree."""
    words, pending = {}, [(root, "")]
    while pending:
        node, path = pending.pop()
        value, left, right = nodes[node]
        if left is None:
            words[path] = value
        else:
            pending.extend([(right, path + "1"), (left, path + "0")])
    offset, output, tokens = 0, "", []
    while offset < len(bits):
        matches = [word for word in words if bits.startswith(word, offset)]
        if len(matches) != 1:
            raise ValueError("Invalid prefix tokenization")
        word = matches[0]
        tokens.append(word)
        output += words[word]
        offset += len(word)
    return output, dict(codewords=words, tokens=tokens)


def _evaluate(public, family):
    nodes, shape = _shape(public["rows"], public["root"], family)
    root = public["root"]
    if family == "rank":
        keys = sorted(value for value, _, _ in nodes.values())
        expected = sum(value < public["limit"] for value in keys)
        actual = count_below(nodes, root, public["limit"])
        if type(actual) is not int or actual != expected:
            raise ValueError("Rank disagrees with independent oracle")
        low, high = keys[1], keys[-2]
        interval = sum(low <= key <= high for key in keys)
        if count_interval(nodes, root, low, high) != interval:
            raise ValueError("Interval composition disagrees with independent oracle")
        detail = dict(
            sorted_keys=keys,
            counted_keys=[v for v in keys if v < public["limit"]],
            interval_bounds=[low, high],
            interval_count=interval,
        )
    elif family == "expression":
        expected, detail = _expression_oracle(nodes, root)
        actual = expression_value(nodes, root)
    else:
        expected, detail = _prefix_oracle(nodes, root, public["bits"])
        actual = decode_message(nodes, root, public["bits"])
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError("Application algorithm disagrees with independent oracle")
    return dict(answer=expected, shape=shape, **detail)


def _source(family, seed):
    if family == "rank":
        offset = seed % 7
        rows = [
            ["r", 40, "a", "b"],
            ["a", 20, "c", "d"],
            ["b", 70, "e", "f"],
            ["c", 10, None, None],
            ["d", 30, None, None],
            ["e", 50, None, None],
            ["f", 90, None, None],
        ]
        for row in rows:
            row[1] += offset
        return dict(
            title="Un index ordonné pour préparer les colis",
            root="r",
            rows=rows,
            limit=65 + offset,
            insertions=[
                ["u", 60 + offset, "e", "right"],
                ["v", 25 + offset, "d", "left"],
            ],
        )
    if family == "expression":
        return dict(
            title="Recalculer un arbre de coût sans changer sa structure",
            root="r",
            rows=[
                ["r", "+", "l", "m"],
                ["l", "*", "s", "c"],
                ["s", "-", "a", "b"],
                ["a", 9, None, None],
                ["b", 4, None, None],
                ["c", 3, None, None],
                ["m", "*", "d", "e"],
                ["d", 2, None, None],
                ["e", 5, None, None],
            ],
            changes=[["b", 7], ["m", "-"]],
        )
    return dict(
        title="Décoder une transmission avec un arbre de préfixes",
        root="r",
        rows=[
            ["r", None, "a", "x"],
            ["a", "A", None, None],
            ["x", None, "b", "y"],
            ["b", "B", None, None],
            ["y", None, "c", "d"],
            ["c", "C", None, None],
            ["d", "D", None, None],
        ],
        bits="010110111",
        exchanged_leaves=["b", "d"],
        recoded_bits="011111010",
    )


def build_case(seed):
    if type(seed) is not int:
        raise ValueError("Whole tree case seed must be an integer")
    family = FAMILIES[(seed - 270100) % len(FAMILIES)]
    public = _source(family, seed)
    current = deepcopy(public)
    states = [dict(id="S0", **_evaluate(current, family))]
    for step in range(2):
        rows = {row[0]: row for row in current["rows"]}
        if family == "rank":
            identifier, value, parent, side = public["insertions"][step]
            index = 2 if side == "left" else 3
            if rows[parent][index] is not None:
                raise ValueError("Insertion would overwrite a subtree")
            rows[parent][index] = identifier
            current["rows"].append([identifier, value, None, None])
        elif family == "expression":
            identifier, value = public["changes"][step]
            rows[identifier][1] = value
        elif step == 0:
            a, b = public["exchanged_leaves"]
            rows[a][1], rows[b][1] = rows[b][1], rows[a][1]
        else:
            current["bits"] = public["recoded_bits"]
            original_nodes = {row[0]: tuple(row[1:]) for row in public["rows"]}
            codes = {letter: word for word, letter in states[-1]["codewords"].items()}
            if (
                transcode(original_nodes, public["root"], public["bits"], codes)
                != current["bits"]
            ):
                raise ValueError("Transcoding disagrees with independent oracle")
        states.append(dict(id=f"S{step + 1}", **_evaluate(current, family)))
    case = dict(
        version=VERSION,
        seed=seed,
        family=family,
        public=public,
        expected=dict(states=states, independent_matches=True),
    )
    return {**case, "sha256": sha256(_canonical(case).encode()).hexdigest()}


def verify_case(case):
    try:
        return _canonical(case) == _canonical(build_case(case["seed"]))
    except (KeyError, TypeError, ValueError):
        return False
