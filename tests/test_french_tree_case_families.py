# Whole tree cases: different reasoning, independent oracles, linked states.

from copy import deepcopy
from itertools import product

import pytest


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_tree_case_is_fresh_bound_and_independently_verified(seed):
    from Backend.Core.france.tree_case_families import build_case, verify_case

    case = build_case(seed)
    assert case["expected"]["independent_matches"] is True
    assert len(case["expected"]["states"]) == 3
    assert verify_case(case)
    original = deepcopy(case)
    case["public"]["rows"][0][1] = "corruption"
    assert not verify_case(case)
    assert build_case(seed) == original
    for seed in (True, "270100", 1.0, None):
        with pytest.raises(ValueError):
            build_case(seed)


def test_rank_counts_against_flat_keys_for_boundaries_and_degenerate_trees():
    from Backend.Core.france.tree_case_families import count_below

    for values in ([], [0], [-4, -1, 0, 3, 8], list(range(30))):
        nodes = {
            str(i): (v, None, str(i + 1) if i + 1 < len(values) else None)
            for i, v in enumerate(values)
        }
        before = deepcopy(nodes)
        for limit in range(-6, 33):
            assert count_below(nodes, "0" if values else None, limit) == sum(
                v < limit for v in values
            )
        assert nodes == before


def test_expression_order_negative_values_and_no_mutation():
    from Backend.Core.france.tree_case_families import expression_value

    for a, b, c in product(range(-3, 4), repeat=3):
        nodes = {
            "r": ("-", "a", "m"),
            "a": (a, None, None),
            "m": ("*", "b", "c"),
            "b": (b, None, None),
            "c": (c, None, None),
        }
        before = deepcopy(nodes)
        assert expression_value(nodes, "r") == a - b * c
        assert nodes == before


def test_decoder_concatenation_reset_truncation_and_invalid_symbols():
    from Backend.Core.france.tree_case_families import build_case, decode_message

    case = build_case(270102)
    nodes = {row[0]: tuple(row[1:]) for row in case["public"]["rows"]}
    code = {"A": "0", "B": "10", "C": "110", "D": "111"}
    before = deepcopy(nodes)
    for length in range(5):
        for letters in product(code, repeat=length):
            bits = "".join(code[c] for c in letters)
            assert decode_message(nodes, "r", bits) == "".join(letters)
    for bits in ("1", "11", "01", "0011", "2", "0x", "10 0"):
        with pytest.raises(ValueError):
            decode_message(nodes, "r", bits)
    assert nodes == before


def test_case_variants_have_different_operations_and_state_effects():
    from Backend.Core.france.tree_case_families import build_case

    cases = [build_case(seed) for seed in range(270100, 270103)]
    assert [c["family"] for c in cases] == ["rank", "expression", "prefix"]
    assert [s["answer"] for s in cases[0]["expected"]["states"]] == [5, 6, 7]
    assert [s["answer"] for s in cases[1]["expected"]["states"]] == [25, 16, 3]
    assert [s["answer"] for s in cases[2]["expected"]["states"]] == [
        "ABCD",
        "ADCB",
        "ABCD",
    ]


@pytest.mark.parametrize(
    "seed,algorithm",
    [
        (270100, "count_below"),
        (270100, "count_interval"),
        (270101, "expression_value"),
        (270102, "decode_message"),
        (270102, "transcode"),
    ],
)
def test_independent_oracle_rejects_corrupted_application_algorithm(
    monkeypatch, seed, algorithm
):
    from Backend.Core.france import tree_case_families as cases

    monkeypatch.setattr(cases, algorithm, lambda *args: None)
    with pytest.raises(ValueError, match="independent oracle"):
        cases.build_case(seed)


def test_bst_rank_matches_flat_oracle_for_varied_shapes():
    import random

    from Backend.Core.france.tree_case_families import count_below

    rng = random.Random(270100)
    for _ in range(100):
        values = rng.sample(range(-100, 101), rng.randrange(1, 25))
        nodes = {}
        for index, value in enumerate(values):
            key = str(index)
            nodes[key] = [value, None, None]
            if index:
                current = "0"
                while True:
                    side = 1 if value < nodes[current][0] else 2
                    if nodes[current][side] is None:
                        nodes[current][side] = key
                        break
                    current = nodes[current][side]
        before = deepcopy(nodes)
        for limit in [min(values), max(values) + 1, *values[:4]]:
            assert count_below(nodes, "0", limit) == sum(
                value < limit for value in values
            )
        assert nodes == before


def test_tree_shape_rejects_global_order_cycles_shared_and_unreachable_nodes():
    from Backend.Core.france.tree_case_families import _shape, build_case

    original = build_case(270100)["public"]["rows"]
    bad = []
    rows = deepcopy(original)
    rows[4][1] = rows[0][1] + 1  # Locally > parent, globally invalid left subtree.
    bad.append(rows)
    rows = deepcopy(original)
    rows[3][2] = "r"
    bad.append(rows)
    rows = deepcopy(original)
    rows[2][2] = "d"
    bad.append(rows)
    rows = deepcopy(original)
    rows.append(["unreachable", 1000, None, None])
    bad.append(rows)
    rows = deepcopy(original)
    rows[0][2] = "absent"
    bad.append(rows)
    for rows in bad:
        with pytest.raises(ValueError):
            _shape(rows, "r", "rank")


def test_prefix_tree_rejects_empty_code_and_repeated_letter():
    from Backend.Core.france.tree_case_families import _shape, build_case

    with pytest.raises(ValueError):
        _shape([["r", "A", None, None]], "r", "prefix")
    rows = build_case(270102)["public"]["rows"]
    rows[-1][1] = "A"
    with pytest.raises(ValueError):
        _shape(rows, "r", "prefix")


def test_rank_helper_composes_an_inclusive_interval_without_off_by_one():
    from Backend.Core.france.tree_case_families import build_case, count_interval

    case = build_case(270100)
    nodes = {r[0]: tuple(r[1:]) for r in case["public"]["rows"]}
    keys = [row[1] for row in case["public"]["rows"]]
    before = deepcopy(nodes)
    for low in range(min(keys) - 1, max(keys) + 2):
        for high in (low, low + 1, max(keys) + 1):
            assert count_interval(nodes, "r", low, high) == sum(
                low <= v <= high for v in keys
            )
    assert nodes == before
    assert count_interval({}, None, 0, 0) == 0


def test_prefix_migration_preserves_message_but_not_old_bitstream():
    from Backend.Core.france.tree_case_families import (
        build_case,
        decode_message,
        transcode,
    )

    case = build_case(270102)
    nodes = {r[0]: tuple(r[1:]) for r in case["public"]["rows"]}
    codes = {"A": "0", "B": "111", "C": "110", "D": "10"}
    migrated = deepcopy(nodes)
    migrated["b"] = ("D", None, None)
    migrated["d"] = ("B", None, None)
    for length in range(4):
        for letters in product("ABCD", repeat=length):
            message = "".join(letters)
            original = "".join(
                {"A": "0", "B": "10", "C": "110", "D": "111"}[c] for c in message
            )
            output = transcode(nodes, "r", original, codes)
            assert output == "".join(codes[c] for c in message)
            assert decode_message(migrated, "r", output) == message
