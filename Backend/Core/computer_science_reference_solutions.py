"""Shared reference snippets used by the renderer and publication integrity gate."""

from __future__ import annotations

import keyword


def paper1_reference_code(
    question_number: int, *, record_name: str = "Observation"
) -> str:
    if not record_name.isidentifier() or keyword.iskeyword(record_name):
        raise ValueError("Reference solution requires a valid record class name")
    examples = {
        4: """def timed(function, values, trials=5):
    results = []
    for _ in range(trials):
        data = values.copy()
        started = timer()
        function(data)
        results.append(timer() - started)
    return sum(results) / len(results)

def compare(n):
    values = make_data(n)
    mean_x = timed(run_X, values)
    mean_y = timed(run_Y, values)
    faster = "X" if mean_x < mean_y else "Y"
    if mean_x == mean_y:
        faster = "tie"
    print(faster, mean_x, mean_y)

compare(int(input("Input size: ")))""",
        9: """def valid_entry(category, value_text):
    category = category.strip().upper()
    if category not in CATEGORIES:
        return False
    try:
        value = int(value_text)
    except (ValueError, TypeError):
        return False
    return 0 <= value <= 100""",
        10: """def parse_adjusted_value(raw_value):
    try:
        value = int(raw_value)
    except (ValueError, TypeError):
        return None
    if value >= THRESHOLD:
        return value * MULTIPLIER
    return value""",
        11: f"""def add_record(records):
    try:
        identifier = int(input(\"Identifier: \"))
        if any(item.identifier == identifier for item in records):
            print(\"Identifier already used\")
            return
        category = input(\"Category: \").strip().upper()
        if category not in CATEGORIES:
            print(\"Invalid category\")
            return
        value = int(input(\"Value: \"))
        if not 0 <= value <= 100:
            print(\"Value out of range\")
            return
    except ValueError:
        print(\"A whole number is required\")
        return
    records.append({record_name}(identifier, category, value))""",
        12: """def print_report(records):
    totals = {category: 0 for category in CATEGORIES}
    best = {category: None for category in CATEGORIES}
    best_values = {}
    for record in records:
        value = adjusted_value(record)
        category = record.category
        totals[category] += value
        if best[category] is None or value > best_values[category]:
            best[category] = record
            best_values[category] = value
    ordered = sorted(totals, key=lambda name: (-totals[name], name))
    for category in ordered:
        leader = best[category]
        print(category, totals[category], leader.identifier if leader else "-")

# A descending numeric key and ascending category key implement
# the required deterministic tie break.""",
    }
    return examples[question_number]
