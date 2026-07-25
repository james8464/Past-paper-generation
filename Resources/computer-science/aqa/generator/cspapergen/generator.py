from __future__ import annotations

import random
import secrets
from collections import Counter

from cspapergen.models import (
    MarkingGuidance,
    Paper1Context,
    PaperBlueprint,
    Question,
    QuestionPart,
    Stimulus,
    Syllabus,
)
from cspapergen.question_bank import build_question, styles_for_total

QUESTION_TOTALS = [4, 7, 8, 8, 10, 10, 11, 12, 12, 14, 4]


def build_paper2_blueprint(syllabus: Syllabus, seed: int | None = None) -> PaperBlueprint:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    middle_totals = list(QUESTION_TOTALS[1:-1])
    rng.shuffle(middle_totals)
    totals = [QUESTION_TOTALS[0], *middle_totals, QUESTION_TOTALS[-1]]

    used_styles: set[str] = set()
    topic_counts: Counter[str] = Counter()
    questions = []
    for index, total in enumerate(totals, start=1):
        candidates = styles_for_total(total)
        if not candidates:
            raise ValueError(f"No question styles available for {total} marks")
        candidates = sorted(
            candidates,
            key=lambda style: (
                style.id in used_styles,
                topic_counts[style.topic_id],
                rng.random(),
            ),
        )
        style = candidates[0]
        used_styles.add(style.id)
        topic_counts[style.topic_id] += 1
        questions.append(build_question(style, index, total, rng))

    return PaperBlueprint(seed=run_seed, questions=questions)


def build_paper1_blueprint(
    syllabus: Syllabus,
    seed: int | None = None,
) -> tuple[PaperBlueprint, Paper1Context]:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    context = _build_paper1_context(rng)
    questions = _build_paper1_questions(context, rng)
    blueprint = PaperBlueprint(
        paper_code="7517/1",
        title="A-level COMPUTER SCIENCE Paper 1",
        paper_number="1",
        delivery_mode="on-screen",
        session="Afternoon",
        materials=[
            "a computer with Python 3",
            "the Electronic Answer Document",
            "the supplied Skeleton Program",
            "the supplied Preliminary Material and data file",
        ],
        seed=run_seed,
        questions=questions,
    )
    return blueprint, context


def _build_paper1_context(rng: random.Random) -> Paper1Context:
    scenarios = [
        (
            "Habitat Survey Manager",
            "Field teams record species observations at monitored habitats.",
            "Observation",
            ["WOODLAND", "WETLAND", "GRASSLAND"],
        ),
        (
            "Community Library Tracker",
            "Volunteers record loans and reading activity for community libraries.",
            "LoanRecord",
            ["FICTION", "SCIENCE", "HISTORY"],
        ),
        (
            "Renewable Energy Monitor",
            "Technicians record output readings from local renewable-energy sites.",
            "SiteReading",
            ["SOLAR", "WIND", "HYDRO"],
        ),
        (
            "Youth Sports League",
            "Officials record results and fair-play points for local teams.",
            "MatchRecord",
            ["JUNIOR", "INTERMEDIATE", "SENIOR"],
        ),
    ]
    title, summary, record_name, categories = rng.choice(scenarios)
    rng.shuffle(categories)
    command_names = ["ADD", "REPORT", "BEST", "QUIT"]
    threshold = rng.choice([40, 50, 60, 75])
    multiplier = rng.choice([2, 3, 4])
    data_rows = [
        f"{rng.randint(100, 999)},{rng.choice(categories)},{rng.randint(12, 95)}"
        for _ in range(8)
    ]
    program = f'''from dataclasses import dataclass

CATEGORIES = {categories!r}
THRESHOLD = {threshold}
MULTIPLIER = {multiplier}


@dataclass
class {record_name}:
    identifier: int
    category: str
    value: int


def load_records(filename):
    records = []
    with open(filename, encoding="utf-8") as source:
        for line in source:
            identifier, category, value = line.strip().split(",")
            records.append({record_name}(int(identifier), category, int(value)))
    return records


def adjusted_value(record):
    if record.value >= THRESHOLD:
        return record.value * MULTIPLIER
    return record.value


def category_totals(records):
    totals = {{category: 0 for category in CATEGORIES}}
    for record in records:
        totals[record.category] += adjusted_value(record)
    return totals


def find_best(records):
    best = records[0]
    for record in records[1:]:
        if adjusted_value(record) > adjusted_value(best):
            best = record
    return best


def add_record(records):
    # Candidate task: validate and append a new record.
    pass


def print_report(records):
    # Candidate task: display categories in descending total order.
    pass


def main():
    records = load_records("cs-paper-1-practice-data.txt")
    command = ""
    while command != "QUIT":
        command = input("Command: ").strip().upper()
        if command == "ADD":
            add_record(records)
        elif command == "REPORT":
            print_report(records)
        elif command == "BEST":
            print(find_best(records))
        elif command != "QUIT":
            print("Unknown command")


if __name__ == "__main__":
    main()
'''
    return Paper1Context(
        scenario_title=title,
        scenario_summary=summary,
        record_name=record_name,
        category_names=categories,
        command_names=command_names,
        skeleton_program=program,
        data_file="\n".join(data_rows) + "\n",
    )


def _build_paper1_questions(context: Paper1Context, rng: random.Random) -> list[Question]:
    first_value = rng.randint(20, 45)
    second_value = rng.randint(65, 90)
    questions = [
        _paper1_question(
            1, "4.1", "programming_trace", "Program execution",
            "A short function processes two integer values.",
            Stimulus(
                kind="code",
                title="Code fragment",
                code=(
                    "def transform(a, b):\n"
                    "    while a < b:\n"
                    "        a = a + 3\n"
                    "        b = b - 2\n"
                    "    return a - b"
                ),
            ),
            [_paper1_part("1", 4, f"State the value returned by transform({first_value}, {second_value}) and describe how you obtained it.", [
                "Trace updates to both variables in the correct order;",
                "Stop when the loop condition first becomes false;",
                "Use the final values in the subtraction;",
                "Award the final value if consistent with the trace;",
            ], 8)],
        ),
        _paper1_question(
            2, "4.4", "regular_language", "Regular languages",
            "A system accepts identifiers that begin with one letter followed by one or more digits.",
            Stimulus(kind="code", title="Candidate expression", code="[A-Z][0-9]+"),
            [_paper1_part("1", 4, "Explain how the regular expression recognises valid identifiers and give one valid and one invalid example.", [
                "First character must be an uppercase letter;",
                "Remaining part contains one or more digits;",
                "Valid example satisfies both components;",
                "Invalid example fails a stated component;",
            ], 8)],
        ),
        _paper1_question(
            3, "4.2", "stack_queue", "Stacks and queues",
            "A service processes urgent requests in last-in, first-out order and routine requests in first-in, first-out order.",
            None,
            [_paper1_part("1", 5, "Name the abstract data structure appropriate to each request type and explain the operations used to add and remove requests.", [
                "Urgent requests use a stack;",
                "Stack uses push and pop;",
                "Routine requests use a queue;",
                "Queue uses enqueue and dequeue;",
                "Explanation links removal order to LIFO and FIFO;",
            ], 10)],
        ),
        _paper1_question(
            4, "4.3", "complexity", "Algorithm complexity",
            "Two algorithms solve the same problem. Algorithm X is O(n log n) and Algorithm Y is O(n²).",
            None,
            [_paper1_part("1", 5, "Compare the likely performance of the algorithms as n increases. Explain why Big O alone does not determine the faster algorithm for every input.", [
                "O(n log n) grows more slowly than O(n squared);",
                "Algorithm X is therefore likely to scale better;",
                "Big O describes asymptotic growth;",
                "Constant factors or implementation details are omitted;",
                "Small inputs or data characteristics may change actual running time;",
            ], 10)],
        ),
        _paper1_question(
            5, "4.1", "recursion", "Recursive programming",
            "A recursive function calculates a value from a positive integer.",
            Stimulus(kind="code", title="Recursive function", code="def value(n):\n    if n == 1:\n        return 2\n    return n + value(n - 1)"),
            [_paper1_part("1", 6, f"Trace value({rng.choice([4, 5, 6])}). Explain the purpose of the base case.", [
                "Expand recursive calls in the correct order;",
                "Reach the call with n equal to 1;",
                "Return 2 from the base case;",
                "Combine returned values correctly;",
                "Base case stops further recursive calls;",
                "Without it the recursion would not terminate normally;",
            ], 12)],
        ),
        _paper1_question(
            6, "4.2", "graph_traversal", "Graph traversal",
            "Locations are represented by an unweighted graph. A route with the fewest edges is required.",
            Stimulus(kind="network", title="Graph", diagram=rng.choice(["mesh-wan", "star-lan"])),
            [_paper1_part("1", 6, "Describe how breadth-first search can find a route with the fewest edges. Identify the main data structure it uses.", [
                "Start at the source vertex;",
                "Use a queue;",
                "Visit adjacent unvisited vertices;",
                "Record each vertex as visited and/or its predecessor;",
                "Process vertices level by level;",
                "First discovery of target gives a minimum-edge route;",
            ], 12)],
        ),
        _paper1_question(
            7, "4.1", "oop_design", "Object-oriented design",
            f"The Skeleton Program represents each item using the {context.record_name} class.",
            None,
            [_paper1_part("1", 8, "Explain how encapsulation, composition and inheritance could be used in an extended version of this system. Include one justified design choice.", [
                "Encapsulation groups state and operations in a class;",
                "Attributes can be protected through methods or properties;",
                "Composition models a has-a relationship;",
                "A container object could own record objects;",
                "Inheritance models an is-a relationship;",
                "A specialised record could inherit common behavior;",
                "Design choice is relevant to the scenario;",
                "Justification considers reuse, maintainability or validity;",
            ], 15)],
        ),
        _paper1_question(
            8, "4.3", "search_sort", "Searching and sorting",
            "A report must display records in descending adjusted-value order and then locate a record by identifier.",
            None,
            [_paper1_part("1", 8, "Recommend a sorting algorithm and a searching algorithm. Explain the conditions needed for the search algorithm and compare their time complexities.", [
                "Suitable efficient comparison sort identified;",
                "Expected average/worst complexity stated accurately;",
                "Binary search identified for repeated lookup;",
                "Binary search requires data ordered by search key;",
                "Binary search has logarithmic time complexity;",
                "Linear search does not require sorted data;",
                "Linear search has linear time complexity;",
                "Recommendation is justified for the stated use;",
            ], 15)],
        ),
        _paper1_question(
            9, "4.13", "test_design", "Systematic testing",
            f"The ADD command must accept an unused integer identifier, one of {', '.join(context.category_names)}, and a value from 0 to 100.",
            None,
            [_paper1_part("1", 10, "Design a compact test plan containing normal, boundary, erroneous and duplicate-identifier cases. State the expected outcome for each case.", [
                "Normal valid case with expected acceptance;",
                "Lower boundary value 0;",
                "Upper boundary value 100;",
                "Value immediately below range;",
                "Value immediately above range;",
                "Invalid category;",
                "Non-integer input;",
                "Duplicate identifier;",
                "Expected outcome stated for each case;",
                "Set is representative without redundant cases;",
            ], 18)],
        ),
        _paper1_question(
            10, "4.1", "skeleton_analysis", "Skeleton Program analysis",
            f"The supplied program loads {context.record_name} objects and calculates category totals.",
            Stimulus(kind="code", title="Relevant function", code="def adjusted_value(record):\n    if record.value >= THRESHOLD:\n        return record.value * MULTIPLIER\n    return record.value"),
            [_paper1_part("1", 10, "Using the supplied constants and data file, explain how adjusted values and category totals are produced. Identify two robustness weaknesses in the supplied program.", [
                "Threshold comparison is described correctly;",
                "Multiplier is applied only at or above threshold;",
                "Records are accumulated by category;",
                "Example uses supplied data consistently;",
                "File open can fail;",
                "Malformed row can fail during unpacking;",
                "Integer conversion can fail;",
                "Unknown category can cause a key error;",
                "Two weaknesses clearly identified;",
                "Relevant handling or validation suggested;",
            ], 18)],
        ),
        _paper1_question(
            11, "4.1", "adapt_program", "Programming task: complete ADD",
            "Open the supplied Skeleton Program in your development environment.",
            None,
            [_paper1_part("1", 14, "Complete add_record so that it validates all three inputs, rejects duplicate identifiers and appends a new object only when every value is valid. Test your code.", [
                "Identifier input obtained and converted safely;",
                "Duplicate identifiers detected;",
                "Category input normalised;",
                "Category checked against allowed values;",
                "Numeric value obtained and converted safely;",
                "Lower bound checked;",
                "Upper bound checked;",
                "Object constructed with correct fields;",
                "Object appended only after all validation;",
                "Clear feedback for invalid input;",
                "No existing data corrupted;",
                "Code is structured and readable;",
                "Normal test succeeds;",
                "At least one erroneous/boundary test succeeds;",
            ], 4)],
        ),
        _paper1_question(
            12, "4.3", "extend_program", "Programming task: report and analysis",
            "Extend the supplied program without changing the existing command behavior.",
            None,
            [_paper1_part("1", 20, "Complete print_report so that categories are displayed in descending total order, ties are resolved alphabetically, and the best record in each category is shown. Add a suitable efficient helper algorithm and test the complete feature.", [
                "Category totals calculated from current records;",
                "Adjusted rather than raw values used;",
                "All categories represented;",
                "Descending total order produced;",
                "Alphabetical tie break implemented;",
                "Best record found separately for each category;",
                "Empty category handled;",
                "Output includes category name;",
                "Output includes total;",
                "Output includes best record identifier;",
                "Suitable decomposition into helper function(s);",
                "Algorithm terminates for all valid data;",
                "No unintended mutation of source records;",
                "Efficient use of dictionary/list structures;",
                "Normal dataset tested;",
                "Tie case tested;",
                "Empty-category case tested;",
                "Expected and actual outcomes compared;",
                "Code is readable and documented;",
                "Complete solution meets every stated requirement;",
            ], 4)],
        ),
    ]
    return questions


def _paper1_question(
    number: int,
    topic_id: str,
    style_id: str,
    title: str,
    stem: str,
    stimulus: Stimulus | None,
    parts: list[QuestionPart],
) -> Question:
    return Question(
        number=number,
        topic_id=topic_id,
        style_id=style_id,
        title=title,
        stem=stem,
        stimulus=stimulus,
        parts=parts,
    )


def _paper1_part(
    label: str,
    marks: int,
    prompt: str,
    points: list[str],
    answer_lines: int,
) -> QuestionPart:
    return QuestionPart(
        label=label,
        prompt=prompt,
        marks=marks,
        answer_lines=answer_lines,
        marking=MarkingGuidance(
            ao="AO1/AO2/AO3" if marks >= 10 else "AO1/AO2",
            points=points,
        ),
    )
