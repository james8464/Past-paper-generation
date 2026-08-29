from __future__ import annotations

import random
import secrets

from cspapergen.models import (
    MarkingGuidance,
    Paper1Context,
    PaperBlueprint,
    Question,
    QuestionPart,
    Stimulus,
    Syllabus,
)
from cspapergen.question_bank import (
    QUESTION_STYLES,
    ao_for_marks,
    build_question,
)

QUESTION_TOTALS = [8, 8, 8, 3, 3, 12, 10, 12, 7, 4, 6, 9, 4, 6]
PAPER2_QUESTION_PLAN = [
    ("software_classification", (2, 2, 4)),
    ("sound_sampling", (2, 2, 2, 2)),
    ("bitmap_storage", (6, 2)),
    ("legal_issues_short", (3,)),
    ("client_server_short", (3,)),
    ("sql_normalisation", (2, 3, 2, 3, 2)),
    ("stored_program", (2, 6, 1, 1)),
    ("ipv4_extended", (12,)),
    ("truth_table_completion", (4, 2, 1)),
    ("compression_short", (2, 2)),
    ("fibonacci_recursion", (1, 1, 2, 2)),
    ("floating_point", (1, 1, 1, 2, 3, 1)),
    ("boolean_simplification", (4,)),
    ("assembly_program", (6,)),
]

Paper2Standardisation = tuple[tuple[str, ...], tuple[str, ...]]

# These notes play the same role as question-specific standardisation guidance in
# an awarding-body mark scheme.  They are deliberately attached here, after the
# Paper 2 repartitioning step, because the source question-bank items can be used
# with different part structures and mark totals elsewhere in the application.
PAPER2_STANDARDISATION: dict[str, tuple[Paper2Standardisation, ...]] = {
    "software_classification": (
        (
            (
                "Accept application software and utility software in either order when the arrows make each intended branch unambiguous.",
                "Accept applications for application software, but both missing branches must be named for both marks.",
            ),
            (
                "Do not accept system software for the user-task examples or a named package where the question asks for a category.",
            ),
        ),
        (
            (
                "Accept a contrast expressed through purpose: maintaining or configuring the system versus completing a user-oriented task.",
                "Accept one paired example only when the function of each example makes the distinction explicit.",
            ),
            (
                "Do not award two independent descriptions that never establish a difference between the categories.",
            ),
        ),
        (
            (
                "Accept assembly language as the low-level language and any compiled or interpreted high-level language as a valid comparison.",
                "Credit linked contrasts involving abstraction, portability, hardware control, development time, maintainability or translation.",
            ),
            (
                "Do not credit the absolute claim that every high-level program is slower or that low-level code needs no translation.",
            ),
        ),
    ),
    "sound_sampling": (
        (
            (
                "Accept an exact unrounded value or a correctly rounded two-decimal value when the unit MiB is stated.",
                "Allow a single arithmetic slip after a correct rate × duration × resolution × channels method; award subsequent method marks consistently.",
            ),
            (
                "Do not accept MB in place of MiB unless the candidate explicitly converts using 1024 squared and merely mislabels the final unit.",
            ),
        ),
        (
            (
                "Accept 36 kHz or 36 000 Hz; the numerical answer and the twice-the-highest-frequency justification are separately creditworthy.",
                "Accept a rate greater than 36 kHz only if it is explicitly identified as sufficient rather than the requested minimum.",
            ),
            (
                "Do not accept 18 kHz, or a bare 36 with no unit where its scale is ambiguous.",
            ),
        ),
        (
            (
                "Accept a clearly described false lower-frequency signal, frequency folding, or two different analogue signals producing the same samples.",
                "Accept the term aliasing only when accompanied by a consequence for reconstruction or the represented waveform.",
            ),
            (
                "Do not credit only 'lower quality', 'distortion' or 'data is lost' without explaining the sampling effect.",
            ),
        ),
        (
            (
                "Treat sampling rate and sample resolution as separate dimensions; credit a linked accuracy and storage consequence for each.",
                "Accept bit depth for sample resolution and amplitude levels or quantisation levels for the representable values.",
            ),
            (
                "Do not credit a higher sampling rate as creating more amplitude levels or a higher resolution as taking samples more often.",
            ),
        ),
    ),
    "bitmap_storage": (
        (
            (
                "Accept any equivalent staged calculation using width × height × colour depth, division by eight, then division by 1024 squared.",
                "Award subsequent method marks after one numerical slip when the candidate carries their value forward consistently and states MiB.",
            ),
            (
                "Do not use a 1000-based megabyte conversion for a mebibyte answer, and do not omit the bits-to-bytes division.",
            ),
        ),
        (
            (
                "Accept greater colour accuracy, more representable colours or reduced colour banding together with the increased bits-per-pixel storage cost.",
                "Credit one correct effect if only image quality or only file size is developed; the two marking points are independent.",
            ),
            (
                "Do not credit increased spatial resolution, pixel count or image dimensions because those properties are held constant.",
            ),
        ),
    ),
    "legal_issues_short": (
        (
            (
                "Credit distinct developed reasons about technological change, cross-border jurisdiction, attribution of responsibility, evidence or enforceability.",
                "Accept a relevant contemporary example when it explains why a particular legal definition or enforcement action becomes difficult.",
            ),
            (
                "Do not award a list of named laws or a generic statement that technology is complicated without a linked legal difficulty.",
            ),
        ),
    ),
    "client_server_short": (
        (
            (
                "Credit centrally managed authentication, permissions, backups or shared files when the benefit is applied to the organisation in the stem.",
                "Accept dedicated service availability or consistent data as a third reason if it is contrasted with peer-to-peer responsibility.",
            ),
            (
                "Do not credit 'faster', 'more secure' or 'more reliable' unless the answer explains which central server feature produces that outcome.",
            ),
        ),
    ),
    "sql_normalisation": (
        (
            (
                "Accept ISNULL(Email) only for a named SQL dialect that supports it; standard SQL uses Email IS NULL.",
                "The identification mark may be earned by stating that NULL is not compared using the equality operator.",
            ),
            (
                "Do not accept Email = 'NULL', Email = 0 or Email = an empty string as equivalent to a null value.",
            ),
        ),
        (
            (
                "Accept INNER JOIN or an unambiguous equi-join, COUNT of any non-null booking field, and an alias used consistently in HAVING and ORDER BY.",
                "Allow GROUP BY Activity with SESSION.Activity qualified or unqualified where no ambiguity exists; the ordering must be descending by the aggregate.",
            ),
            (
                "Do not accept a WHERE condition on COUNT, DISTINCT activities without grouping, or ordering alphabetically instead of by booking count.",
            ),
        ),
        (
            (
                "Accept omission of the column list only when all three values are supplied in the schema order and the statement remains syntactically valid.",
                "Allow double-quoted string literals only if the candidate consistently states a database dialect in which they are valid.",
            ),
            (
                "Do not credit a statement that omits either quote-delimited text value or places the email and name against the wrong columns.",
            ),
        ),
        (
            (
                "Accept TRUE, 1 or the dialect's equivalent Boolean literal; both composite-key fields must constrain the same WHERE clause.",
                "Award the update and assignment mark even if one key predicate is wrong, provided no other column is unintentionally changed.",
            ),
            (
                "Do not award full credit for filtering only by MemberID or only by SessionID because that can alter multiple bookings.",
            ),
        ),
        (
            (
                "Accept FALSE, 0 or an equivalent Boolean literal and either order of the two AND-connected predicates.",
                "A valid table alias may qualify both SessionID and Attended without affecting credit.",
            ),
            (
                "Do not accept DELETE * FROM BOOKING, and do not award the selection mark if attended bookings could also be removed.",
            ),
        ),
    ),
    "stored_program": (
        (
            (
                "Accept that machine-code instructions and the data they operate on share addressable main memory and are fetched by the processor.",
                "The two points may be expressed in either order, but storage and execution must both be present.",
            ),
            (
                "Do not accept only that programs are saved on secondary storage or that the processor itself permanently stores every instruction.",
            ),
        ),
        (
            (
                "Award bus marks only where the address bus carries an address, the data bus carries the instruction, and the control bus carries a read signal.",
                "Accept MDR or MBR, and accept PC increment before or after transfer to MAR when the sequence remains logically consistent.",
            ),
            (
                "Do not interchange MAR with MDR, or claim that the program counter contains the instruction currently being decoded.",
            ),
        ),
        (
            (
                "Accept the current instruction, the instruction being decoded, or the instruction presently being executed as equivalent descriptions.",
            ),
            (
                "Do not accept the address of the next instruction; that is the role of the program counter.",
            ),
        ),
        (
            (
                "Accept reprogrammability, loading a different instruction sequence, or treating instructions as data, with no hardware rewiring required.",
            ),
            (
                "Do not credit only 'it is faster' or 'it stores programs' without explaining the resulting benefit.",
            ),
        ),
    ),
    "ipv4_extended": (
        (
            (
                "Use the level descriptors holistically; a top-level response should compare at least two approaches and reach a context-based recommendation.",
                "Credit accurate development of private addressing with NAT, DHCP lease management, IPv6 migration, dual stack, routing and firewall policy.",
                "Accept carrier-grade NAT or address sharing when limitations for inbound services, logging or troubleshooting are considered.",
            ),
            (
                "Do not treat NAT as a firewall, IPv6 as automatically secure, or DHCP as creating additional public IPv4 addresses.",
            ),
        ),
    ),
    "truth_table_completion": (
        (
            (
                "Award one mark for each correct output row; a copied input value in the output column is not sufficient working.",
                "If a candidate evaluates an unprinted intermediate column, use it to apply positive marking to the final output where possible.",
            ),
            (
                "Do not infer a correct row from an altered input combination; mark only the output for the supplied row.",
            ),
        ),
        (
            (
                "Accept any one complete A, B and C combination whose output is 1; allocate the two marks according to the published split.",
                "The values may be written as a binary triple if their variable order is clear.",
            ),
            (
                "Do not combine A and B from one valid row with C from another row.",
            ),
        ),
        (
            (
                "Accept systematic coverage of inputs, comparison with an expected result, or isolation of the input that exposes a circuit fault.",
            ),
            (
                "Do not credit only that a truth table 'shows whether it works' without identifying what is checked.",
            ),
        ),
    ),
    "compression_short": (
        (
            (
                "Accept reduced storage, shorter transfer time, lower bandwidth use or lower transmission cost as distinct reasons where appropriate.",
                "Two marks require two consequences rather than two phrasings of the same storage saving.",
            ),
            (
                "Do not credit improved data quality, greater security or automatic removal of redundant records.",
            ),
        ),
        (
            (
                "Accept exact reconstruction or no permanently discarded source data, followed by a consequence specific to the named data in the stem.",
                "For executable data, the consequence must concern unchanged instructions or correct execution; for records, it must concern exact values or auditability.",
            ),
            (
                "Do not credit a generic statement that lossless is 'better quality' without explaining why exact recovery matters here.",
            ),
        ),
    ),
    "fibonacci_recursion": (
        (
            (
                "Accept the empty-list pattern, the [] clause, or the expression returning 0 as the base case.",
            ),
            (
                "Do not accept x:xs or the recursive call, which belongs to the recursive case.",
            ),
        ),
        (
            (
                "Accept 8 with or without a shown expansion; zero and the negative value contribute nothing to the total.",
            ),
            (
                "Do not accept 6 from summing every list member or 10 from treating the negative value as positive.",
            ),
        ),
        (
            (
                "Accept head and tail terminology for x and xs when the answer explains how the matching clause selects the recursive definition.",
                "The termination point must be linked to repeatedly shortening the immutable list until [] matches.",
            ),
            (
                "Do not credit only that the function calls itself; the role of the two patterns is required.",
            ),
        ),
        (
            (
                "Accept referential transparency expressed as the same immutable input giving the same output with no externally visible state change.",
                "Credit absence of file, global-variable or input/output side effects as a valid development.",
            ),
            (
                "Do not claim that every recursive function is pure; purity depends on its data dependencies and side effects.",
            ),
        ),
    ),
    "floating_point": (
        (
            (
                "Accept the named direction only; judge it from the signed exponent rather than the mantissa sign.",
            ),
            (
                "Do not reverse the movement by describing movement of digits instead of movement of the binary point.",
            ),
        ),
        (
            (
                "Accept an exact fraction or equivalent denary value; award the mark only when both two's-complement mantissa and exponent are interpreted correctly.",
            ),
            (
                "Do not read either field as unsigned, and do not place the binary point before the mantissa sign bit.",
            ),
        ),
        (
            (
                "Accept 'normalised' with the first-two-bits-differ test, namely 01 for a positive fraction or 10 for a negative fraction.",
            ),
            (
                "Do not accept that normalisation merely means there are no leading zeroes in the printed bit pattern.",
            ),
        ),
        (
            (
                "Accept smaller representable steps, more significant fractional bits, reduced quantisation error or increased precision as linked statements.",
            ),
            (
                "Do not credit increased range because the exponent field is explicitly unchanged.",
            ),
        ),
        (
            (
                "Credit wider exponent range and therefore wider magnitude range separately from the loss of mantissa precision.",
                "Accept increased rounding or quantisation error as the consequence of fewer mantissa bits.",
            ),
            (
                "Do not claim that more exponent bits increase precision or that fewer mantissa bits reduce the range.",
            ),
        ),
        (
            (
                "Accept underflow; accept underflow error, but no explanation is required for the single mark.",
            ),
            (
                "Do not accept overflow, truncation or rounding error for a non-zero magnitude too close to zero.",
            ),
        ),
    ),
    "boolean_simplification": (
        (
            (
                "Accept any sequence of named or visibly correct Boolean identities provided every intermediate expression is equivalent and the final form is minimal.",
                "Use the symbols ·, +, overbar, ⊕, ⊼ and ⊽ consistently with the operation being shown; accept conventional prime notation for NOT.",
            ),
            (
                "Do not credit an arithmetic cancellation rule, an unexplained final answer after invalid working, or words used in place of the required Boolean expression.",
            ),
        ),
    ),
    "assembly_program": (
        (
            (
                "Credit purpose, application to the supplied immediate value, stored result and implementation as separate marking dimensions.",
                "Accept floor(log2(n)) + 1 as the bit length for the positive input, or a correct iteration trace showing the same count.",
                "Accept division by two only when the answer respects unsigned, zero-fill logical shifting and integer bit behaviour.",
            ),
            (
                "Do not describe the loop as counting set bits: R0 increments for every shift, including when the discarded least-significant bit is zero.",
                "Do not treat # as an address or [100] as the literal value 100; those meanings are stated explicitly in the question.",
            ),
        ),
    ),
}


def build_paper2_blueprint(syllabus: Syllabus, seed: int | None = None) -> PaperBlueprint:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    styles = {style.id: style for style in QUESTION_STYLES}
    questions = [
        _repartition_paper2_question(
            build_question(styles[style_id], index, sum(part_marks), rng),
            part_marks,
        )
        for index, (style_id, part_marks) in enumerate(
            PAPER2_QUESTION_PLAN,
            start=1,
        )
    ]

    return PaperBlueprint(seed=run_seed, questions=questions)


TOPIC_QUESTION_BANK_PLANS: dict[str, tuple[tuple[str, int], ...]] = {
    "4.2": (
        ("data_structures_stack_queue", 6),
        ("data_structures_hash", 6),
        ("data_structures_tree", 6),
        ("data_structures_graph", 6),
        ("data_structures_choice", 6),
    ),
    "4.10": (
        ("sql_normalisation", 12),
        ("erd_keys", 8),
        ("database_extended", 10),
    ),
    "4.12": (
        ("functional_programming", 8),
        ("functional_recursion", 8),
        ("functional_type_short", 4),
        ("functional_extended", 10),
    ),
}


def build_topic_question_bank(
    syllabus: Syllabus,
    *,
    topic_id: str,
    seed: int | None = None,
) -> PaperBlueprint:
    try:
        plan = TOPIC_QUESTION_BANK_PLANS[topic_id]
    except KeyError as error:
        raise ValueError(f"No question bank is available for topic {topic_id}") from error
    topic = syllabus.get_topic(topic_id)
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    styles = {style.id: style for style in QUESTION_STYLES}
    questions = [
        build_question(styles[style_id], number, marks, rng)
        for number, (style_id, marks) in enumerate(plan, start=1)
    ]
    return PaperBlueprint(
        assessment_kind="question-bank",
        focus_topic_id=topic_id,
        paper_code="7517/QB",
        title=f"A-level COMPUTER SCIENCE {topic.title} Question Bank",
        paper_number="QB",
        delivery_mode="written",
        session="Practice",
        duration_minutes=45,
        total_marks=sum(question.total_marks for question in questions),
        seed=run_seed,
        questions=questions,
    )


def _repartition_paper2_question(
    question: Question,
    target_marks: tuple[int, ...],
) -> Question:
    source = question.parts
    desired_count = len(target_marks)
    try:
        standardisation = PAPER2_STANDARDISATION[question.style_id]
    except KeyError as error:
        raise ValueError(
            f"Paper 2 standardisation is missing for {question.style_id}"
        ) from error
    if len(standardisation) != desired_count:
        raise ValueError(
            f"Paper 2 standardisation for {question.style_id} has "
            f"{len(standardisation)} parts; expected {desired_count}"
        )
    rebuilt: list[QuestionPart] = []
    for index, marks in enumerate(target_marks):
        if index < desired_count - 1:
            part = source[min(index, len(source) - 1)]
            points = list(part.marking.points)
            prompt = part.prompt
        else:
            remaining = source[min(index, len(source) - 1) :]
            part = remaining[0]
            points = [
                point
                for item in remaining
                for point in item.marking.points
            ]
            prompt = (
                " ".join(item.prompt for item in remaining)
                if len(remaining) > 1
                else part.prompt
            )
        if index >= len(source):
            dimension = (
                "technical requirement",
                "implementation consequence",
                "limitation or trade-off",
            )[(index - len(source)) % 3]
            prompt = (
                f"Using the same scenario, explain one further {dimension} associated "
                f"with {question.title.lower()}."
            )
            points = [
                f"Credit a technically accurate point about {question.title.lower()};",
                "The point must be developed and applied to the stated scenario;",
            ]
        accept, reject = standardisation[index]
        guidance = part.marking.model_copy(
            update={
                "ao": (
                    part.marking.ao
                    if question.style_id == "sql_normalisation"
                    else ao_for_marks(marks)
                ),
                "points": points,
                "accept": list(accept),
                "reject": list(reject),
            }
        )
        rebuilt.append(
            part.model_copy(
                update={
                    "label": str(index + 1),
                    "marks": marks,
                    "prompt": prompt,
                    "answer_lines": max(part.answer_lines, marks + 2),
                    "marking": guidance,
                }
            )
        )
    return question.model_copy(update={"parts": rebuilt})

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
    # Candidate task: display categories in descending adjusted-total order.
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
            "A report displays records in descending adjusted-value order. A separate identifier index is used to locate records.",
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
            "The supplied program reads raw value fields from a data file. THRESHOLD and MULTIPLIER are defined constants.",
            Stimulus(kind="code", title="Function to complete", code="def adjusted_value(raw_value):\n    # Return None if raw_value is malformed.\n    pass"),
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
    return _align_paper1_structure(questions, context, rng)


def _align_paper1_structure(
    questions: list[Question],
    context: Paper1Context,
    rng: random.Random,
) -> list[Question]:
    """Match the recurring 7517/1 sub-question and mark pattern."""
    parts_by_question: dict[int, list[QuestionPart]] = {
        1: [
            _paper1_part("1", 1, "Explain why a record can normally be found more quickly in a hash table than in an ordered list.", ["A hash function gives direct access to the expected storage location;"], 2, "AO1"),
            _paper1_part("2", 4, "Describe the steps required to add a record to a hash table that resolves collisions using chaining.", [
                "Apply the hash function to the record's key;",
                "Use the result to select the table position;",
                "Detect that the position already contains a record or chain;",
                "Add the new record to the chain at that position;",
            ], 6, "AO2"),
            _paper1_part("3", 1, "Explain why the time needed to retrieve a record may increase as the hash table becomes full.", ["More collisions create longer chains or require more probes;"], 2, "AO2"),
            _paper1_part("4", 1, "Explain why linear search has time complexity O(n).", ["In the worst case every item is examined once;"], 2, "AO1"),
            _paper1_part("5", 1, "Explain why binary search has time complexity O(log n).", ["Each comparison discards half of the remaining search interval;"], 2, "AO1"),
            _paper1_part("6", 1, "State one advantage of linear search over binary search.", ["The records do not need to be ordered;"], 2, "AO1"),
            _paper1_part("7", 1, "Explain why merge sort is considered tractable.", ["Its polynomial/log-linear time complexity is practical for realistic input sizes;"], 2, "AO1"),
            _paper1_part("8", 1, "State the maximum number of passes needed to bubble-sort a list containing 80 items.", ["79 passes;"], 2, "AO2"),
        ],
        2: [
            _paper1_part("1", 2, "Define the term decomposition as used in computational thinking.", [
                "Breaking a complex problem into smaller sub-problems;",
                "Each sub-problem can be solved or developed separately;",
            ], 4, "AO1"),
        ],
        3: [
            _paper1_part("1", 1, "State the purpose of a depth-first traversal of a graph.", ["To visit or search all reachable vertices by following a path as far as possible before backtracking;"], 2, "AO1"),
            _paper1_part("2", 2, "State two properties that would show that the represented graph is not a tree.", ["It contains a cycle;", "It is disconnected or has more than one path between a pair of vertices;"], 4, "AO2"),
            _paper1_part("3", 2, "Complete an adjacency matrix for the graph represented by AL. Record only the entries that contain 1.", ["Entries are symmetric for the undirected graph;", "All and only the listed edges are represented;"], 5, "AO2"),
            _paper1_part("4", 1, "Describe the base case in reachable that returns True.", ["The current vertex is the target vertex;"], 2, "AO2"),
            _paper1_part("5", 6, "Trace the call reachable(3, 6). Record, in order, every recursive call and every change made to visited.", [
                "The initial call is recorded;",
                "Vertices are marked before their neighbours are explored;",
                "Adjacent vertices are considered in list order;",
                "Already visited vertices are not revisited;",
                "The target call returns True and the result propagates;",
                "The call sequence and visited states are complete;",
            ], 10, "AO2"),
        ],
        4: [
            _paper1_part("1", 12, "Design an algorithm that selects the more suitable implementation for a supplied input size, executes it and records comparable timing evidence. Give the algorithm in structured English or code.", [
                "Accept or receive the input size;",
                "Generate equivalent input data for both algorithms;",
                "Use a monotonic high-resolution timer;",
                "Record the start time immediately before execution;",
                "Record the end time immediately after execution;",
                "Calculate elapsed time;",
                "Repeat trials;",
                "Use the same data or equivalent copies;",
                "Calculate a representative average or median;",
                "Select the algorithm with the lower measured time;",
                "Return or display the selection and evidence;",
                "Algorithm is complete, unambiguous and terminates;",
            ], 18, "AO3"),
            _paper1_part("2", 1, "State one reason why a single timing trial may be unreliable.", ["Other processes, caching or timer variation can affect one measurement;"], 3, "AO3"),
        ],
        5: [
            _paper1_part("1", 2, f"State the first two recursive calls made when evaluating the supplied function for n = {rng.choice([5, 6])}.", [
                "First recursive call decreases n by one;",
                "Second recursive call decreases n by one again;",
            ], 4, "AO1"),
            _paper1_part("2", 2, "Explain the purpose of the base case.", [
                "It supplies a result without another recursive call;",
                "It ensures that the recursion terminates;",
            ], 4, "AO1"),
            _paper1_part("3", 1, "State one consequence of removing the base case.", ["Calls continue until a recursion-depth or stack-overflow error occurs;"], 3, "AO2"),
        ],
        6: [
            _paper1_part("1", 2, "Complete the missing transitions in the supplied state-transition table.", ["Correct transition from state S1;", "Correct transition from state S2;"], 4, "AO2"),
            _paper1_part("2", 2, "Write a regular expression that accepts exactly the same strings as the finite-state machine.", ["Expression accepts the required prefix and repetitions;", "Expression rejects strings ending in a non-accepting state;"], 4, "AO2"),
            _paper1_part("3", 2, "State two test strings: one accepted and one rejected by the finite-state machine.", ["Valid accepted string;", "Valid rejected string;"], 4, "AO2"),
            _paper1_part("4", 1, "State the meaning of a double circle on a state-transition diagram.", ["An accepting/final state;"], 2, "AO1"),
            _paper1_part("5", 1, "State whether a deterministic finite-state machine may have two transitions with the same input from one state.", ["No;"], 2, "AO1"),
            _paper1_part("6", 2, "Explain how the machine processes an input string.", ["Start in the initial state and consume one symbol at a time;", "Follow the matching transition and accept only if the final state is accepting;"], 4, "AO2"),
            _paper1_part("7", 1, "State one reason for representing validation rules as a finite-state machine.", ["It provides an unambiguous, implementable model of every valid transition;"], 3, "AO2"),
            _paper1_part("8", 3, "Explain how an implementation should respond when no transition exists for the next input symbol.", [
                "Reject the input;",
                "Do not consume further symbols or enter an undefined state;",
                "Return a clear invalid result without terminating the whole program;",
            ], 6, "AO2"),
        ],
        7: [
            _paper1_part("1", 1, f"State the programming paradigm used to define {context.record_name}.", ["Object-oriented programming;"], 2, "AO1"),
            _paper1_part("2", 2, "Explain one benefit of encapsulating the record fields.", [
                "Fields can be accessed through controlled methods or properties;",
                "This protects invariants and reduces unintended changes;",
            ], 4, "AO2"),
        ],
        8: [
            _paper1_part("1", 1, "State the condition that must be true of the identifier index before binary search can be used.", ["The index must be ordered by identifier;"], 1, "AO1"),
        ],
        9: [
            _paper1_part("1", 4, f"Write code to validate that a category is one of {', '.join(context.category_names)} and that a numeric value is between 0 and 100 inclusive.", [
                "Input is normalised consistently;",
                "Membership of the allowed categories is tested;",
                "Both inclusive numeric bounds are tested;",
                "A correct Boolean result or validation action is produced;",
            ], 8, "AO3"),
            _paper1_part("2", 1, "State one test that checks a boundary of the numeric range.", [
                "Use 0 or 100 and expect the value to be accepted;",
            ], 3, "AO3"),
        ],
        10: [
            _paper1_part("1", 7, "Complete adjusted_value. Convert raw_value to an integer, return None if conversion fails, return the converted value multiplied by MULTIPLIER when it is at least THRESHOLD, and otherwise return the converted integer value.", [
                "1 mark: int(raw_value) or an equivalent conversion is attempted;",
                "1 mark: ValueError and/or TypeError is caught without terminating the program;",
                "1 mark: None is returned from the exception path;",
                "1 mark: the converted value is compared with THRESHOLD using >=;",
                "1 mark: the converted value is multiplied by MULTIPLIER only on the threshold branch;",
                "1 mark: the adjusted result is returned from that branch;",
                "1 mark: the converted integer value is returned otherwise;",
            ], 12, "AO3"),
            _paper1_part("2", 1, "State one test that exercises the threshold boundary.", ["Input raw_value equal to THRESHOLD; expected output THRESHOLD * MULTIPLIER;"], 3, "AO3"),
        ],
        11: [
            _paper1_part("1", 11, "Complete add_record so that all inputs are validated, duplicate identifiers are rejected and a new object is appended only when every value is valid.", [
                "Identifier is converted safely;",
                "Existing identifiers are checked;",
                "Duplicate identifiers are rejected;",
                "Category input is normalised;",
                "Category is checked against the allowed values;",
                "Numeric value is converted safely;",
                "Lower bound is checked;",
                "Upper bound is checked;",
                "A correctly populated object is constructed;",
                "The object is appended only after all validation succeeds;",
                "The implementation is complete and readable;",
            ], 18, "AO3"),
            _paper1_part("2", 1, "State one test that demonstrates duplicate identifiers are rejected.", ["Use an identifier already present and confirm that no record is appended;"], 3, "AO3"),
        ],
        12: [
            _paper1_part("1", 11, "Complete print_report so that categories are displayed in descending adjusted-total order, ties are resolved alphabetically and record.identifier is shown for the best record in each category. You may define suitable helper functions.", [
                "1 mark: traverses every current record exactly once when accumulating report data;",
                "1 mark: calls adjusted_value, or implements the same threshold rule, instead of adding each raw value;",
                "1 mark: maintains a separate accumulated total for every category, including categories with no records;",
                "1 mark: tracks the record with the greatest adjusted value separately within each non-empty category;",
                "1 mark: represents an empty category without attempting to access a missing best record;",
                "1 mark: orders categories using the adjusted total as a descending primary key;",
                "1 mark: uses the category name as an ascending secondary key when adjusted totals are equal;",
                "1 mark: displays every category name once;",
                "1 mark: displays the corresponding adjusted total for every category;",
                "1 mark: displays record.identifier for the tracked best record in each non-empty category;",
                "1 mark: leaves the records list and its Record objects unchanged after producing the report;",
            ], 18, "AO3"),
            _paper1_part("2", 1, "State one input data set and its expected output order that tests the alphabetical tie break.", ["1 mark: gives two categories with equal adjusted totals and expects those category names in alphabetical order;"], 3, "AO3"),
            _paper1_part("3", 2, "Explain why a dictionary is suitable for storing the category totals.", [
                "A category key gives direct access to its accumulated total;",
                "Lookup and update are efficient on average;",
            ], 4, "AO2"),
        ],
    }
    question_updates = {
        1: {
            "topic_id": "4.3",
            "style_id": "hash_search_sort",
            "title": "Hashing, searching and sorting",
            "stem": "A data service stores records either in a hash table or in an ordered list.",
            "stimulus": None,
        },
        2: {
            "topic_id": "4.3",
            "style_id": "decomposition",
            "title": "Computational thinking",
            "stem": "",
            "stimulus": None,
        },
        3: {
            "topic_id": "4.2",
            "style_id": "recursive_graph_traversal",
            "title": "Graph representation and traversal",
            "stem": "A graph is stored as the adjacency list AL. The recursive function searches for a path between two vertices.",
            "stimulus": Stimulus(
                kind="code",
                title="Adjacency list and recursive traversal",
                code=(
                    "AL = {1:[2,4], 2:[1,3,5], 3:[2,6],\n"
                    "      4:[1,5], 5:[2,4,6], 6:[3,5]}\n"
                    "def reachable(current, target, visited):\n"
                    "    if current == target: return True\n"
                    "    visited.add(current)\n"
                    "    for neighbour in AL[current]:\n"
                    "        if neighbour not in visited:\n"
                    "            if reachable(neighbour, target, visited):\n"
                    "                return True\n"
                    "    return False"
                ),
            ),
        },
        6: {
            "topic_id": "4.4",
            "style_id": "finite_state_machine",
            "title": "Finite-state machines",
            "stem": "A validator accepts binary strings that begin with 1 and contain an even number of 0 digits.",
            "stimulus": Stimulus(
                kind="fsm",
                title="Finite-state machine and incomplete transition table",
                headers=["Current state", "Input 0", "Input 1"],
                rows=[["S0 (start)", "-", "S1"], ["S1 (accept)", "S2", "S1"], ["S2", "", ""]],
            ),
        },
    }
    return [
        question.model_copy(
            update={
                **question_updates.get(question.number, {}),
                "parts": parts_by_question[question.number],
            }
        )
        for question in questions
    ]


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
    ao: str | None = None,
) -> QuestionPart:
    return QuestionPart(
        label=label,
        prompt=prompt,
        marks=marks,
        answer_lines=answer_lines,
        marking=MarkingGuidance(
            ao=ao or ("AO1/AO2/AO3" if marks >= 10 else "AO1/AO2"),
            points=points,
        ),
    )
