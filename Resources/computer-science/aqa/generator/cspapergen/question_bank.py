from __future__ import annotations

import random
from dataclasses import dataclass

from cspapergen.models import MarkingGuidance, Question, QuestionPart, Stimulus


@dataclass(frozen=True)
class QuestionStyle:
    id: str
    topic_id: str
    totals: tuple[int, ...]
    maker: str


QUESTION_STYLES = [
    QuestionStyle("data_structures_stack_queue", "4.2", (6,), "data_structures_stack_queue"),
    QuestionStyle("data_structures_hash", "4.2", (6,), "data_structures_hash"),
    QuestionStyle("data_structures_tree", "4.2", (6,), "data_structures_tree"),
    QuestionStyle("data_structures_graph", "4.2", (6,), "data_structures_graph"),
    QuestionStyle("data_structures_choice", "4.2", (6,), "data_structures_choice"),
    QuestionStyle("software_classification", "4.6", (8,), "software_classification"),
    QuestionStyle("bitmap_storage", "4.5", (8,), "bitmap_storage"),
    QuestionStyle("legal_issues_short", "4.8", (3,), "legal_issues_short"),
    QuestionStyle("client_server_short", "4.9", (3,), "client_server_short"),
    QuestionStyle("ipv4_extended", "4.9", (12,), "ipv4_extended"),
    QuestionStyle("compression_short", "4.5", (4,), "compression_short"),
    QuestionStyle("fibonacci_recursion", "4.12", (6,), "fibonacci_recursion"),
    QuestionStyle("boolean_simplification", "4.6", (4,), "boolean_simplification"),
    QuestionStyle("assembly_program", "4.7", (6,), "assembly_program"),
    QuestionStyle("short_security", "4.6", (4,), "short_security"),
    QuestionStyle("software_roles_short", "4.6", (3,), "software_roles_three"),
    QuestionStyle("network_service_short", "4.9", (3,), "network_service_three"),
    QuestionStyle("binary_arithmetic_short", "4.5", (4,), "binary_short"),
    QuestionStyle("unicode_ascii_short", "4.5", (4,), "unicode_short"),
    QuestionStyle("fde_register_short", "4.7", (4,), "fde_short"),
    QuestionStyle("protocol_layers_short", "4.9", (4,), "protocol_short"),
    QuestionStyle("database_key_short", "4.10", (4,), "database_key_short"),
    QuestionStyle("big_data_short", "4.11", (4,), "big_data_short"),
    QuestionStyle("bitmap_size", "4.5", (7, 8, 10, 14), "bitmap"),
    QuestionStyle("sound_sampling", "4.5", (6, 7, 8, 10, 14), "sound"),
    QuestionStyle("rle_compression", "4.5", (7, 8, 9, 10, 14), "rle"),
    QuestionStyle("floating_point", "4.5", (8, 9, 10), "float"),
    QuestionStyle("logic_truth_table", "4.6", (8, 9, 14), "logic"),
    QuestionStyle("truth_table_completion", "4.6", (7, 8, 10), "truth_table"),
    QuestionStyle("boolean_algebra", "4.6", (8, 9, 10, 14), "boolean"),
    QuestionStyle("translator_language", "4.6", (8, 10), "translator"),
    QuestionStyle("security_measures", "4.6", (8, 10), "security"),
    QuestionStyle("processor_buses", "4.7", (8, 10), "processor"),
    QuestionStyle("stored_program", "4.7", (8, 10), "stored"),
    QuestionStyle("packet_switching", "4.9", (7, 8, 9, 10, 14), "packet"),
    QuestionStyle("network_topology", "4.9", (6, 7, 8, 10), "network_topology"),
    QuestionStyle("tcpip_dns", "4.9", (8, 9, 10), "tcpip"),
    QuestionStyle("sql_normalisation", "4.10", (8, 10, 14), "sql"),
    QuestionStyle("erd_keys", "4.10", (8, 9, 10), "erd"),
    QuestionStyle("big_data", "4.11", (8, 10), "bigdata"),
    QuestionStyle("functional_programming", "4.12", (8, 10, 14), "functional"),
    QuestionStyle("functional_recursion", "4.12", (8, 9), "recursion"),
    QuestionStyle("assembly_trace", "4.7", (11,), "assembly"),
    QuestionStyle("functional_type_short", "4.12", (4,), "functional_type"),
    QuestionStyle("ethics_extended", "4.8", (12,), "ethics12"),
    QuestionStyle("database_extended", "4.10", (12,), "database12"),
    QuestionStyle("network_security_extended", "4.9", (12,), "network12"),
    QuestionStyle("functional_extended", "4.12", (12,), "functional12"),
]

STYLE_IDS = {style.id for style in QUESTION_STYLES}


def styles_for_total(total: int) -> list[QuestionStyle]:
    return [style for style in QUESTION_STYLES if total in style.totals]


def build_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    builders = {
        "data_structures_stack_queue": _data_structures_stack_queue_question,
        "data_structures_hash": _data_structures_hash_question,
        "data_structures_tree": _data_structures_tree_question,
        "data_structures_graph": _data_structures_graph_question,
        "data_structures_choice": _data_structures_choice_question,
        "software_classification": _software_classification_question,
        "bitmap_storage": _bitmap_storage_question,
        "legal_issues_short": _legal_issues_short_question,
        "client_server_short": _client_server_short_question,
        "ipv4_extended": _ipv4_extended_question,
        "compression_short": _compression_short_question,
        "fibonacci_recursion": _fibonacci_recursion_question,
        "boolean_simplification": _boolean_simplification_question,
        "assembly_program": _assembly_program_question,
        "bitmap": _bitmap_question,
        "short_security": _short_security_question,
        "software_roles_three": _software_roles_three_question,
        "network_service_three": _network_service_three_question,
        "binary_short": _binary_short_question,
        "unicode_short": _unicode_short_question,
        "fde_short": _fde_short_question,
        "protocol_short": _protocol_short_question,
        "database_key_short": _database_key_short_question,
        "big_data_short": _big_data_short_question,
        "sound": _sound_question,
        "rle": _rle_question,
        "float": _floating_point_question,
        "logic": _logic_question,
        "truth_table": _truth_table_question,
        "boolean": _boolean_question,
        "translator": _translator_question,
        "security": _security_question,
        "processor": _processor_question,
        "stored": _stored_program_question,
        "packet": _packet_question,
        "network_topology": _network_topology_question,
        "tcpip": _tcpip_question,
        "sql": _sql_question,
        "erd": _erd_question,
        "bigdata": _big_data_question,
        "functional": _functional_question,
        "recursion": _recursion_question,
        "assembly": _assembly_trace_question,
        "functional_type": _functional_type_question,
        "ethics12": _ethics_extended_question,
        "database12": _database_extended_question,
        "network12": _network_extended_question,
        "functional12": _functional_extended_question,
    }
    return builders[style.maker](style, number, total, rng)


def _parts(raw: list[tuple[str, int, str, list[str], str, int]]) -> list[QuestionPart]:
    return [
        QuestionPart(
            label=label,
            marks=marks,
            prompt=prompt,
            answer_lines=lines,
            answer_unit=unit,
            marking=MarkingGuidance(ao=ao_for_marks(marks), points=points),
        )
        for label, marks, prompt, points, unit, lines in raw
    ]


def ao_for_marks(marks: int) -> str:
    if marks >= 12:
        return "AO1/AO2 extended response"
    if marks >= 4:
        return "AO1/AO2"
    return "AO1"


def _question(style: QuestionStyle, number: int, title: str, stem: str, stimulus: Stimulus | None, parts: list[QuestionPart]) -> Question:
    return Question(number=number, topic_id=style.topic_id, style_id=style.id, title=title, stem=stem, stimulus=stimulus, parts=parts)


def _fit_parts(parts: list[QuestionPart], total: int) -> list[QuestionPart]:
    current = sum(part.marks for part in parts)
    if current == total:
        return parts
    delta = total - current
    last = parts[-1]
    points = list(last.marking.points)
    if delta > 0:
        points.append("Credit any further valid, question-specific expansion;")
    marks = max(1, last.marks + delta)
    parts[-1] = last.model_copy(update={"marks": marks, "answer_lines": max(last.answer_lines, marks + 1), "marking": last.marking.model_copy(update={"points": points})})
    return parts


def _data_structures_stack_queue_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    values = rng.sample(range(12, 90), 4)
    a, b, c, d = values
    stimulus = Stimulus(
        kind="code",
        title="Operations",
        code=(
            f"push({a})\npush({b})\npop()\npush({c})\npush({d})"
        ),
    )
    parts = _parts([
        ("1", 2, "State the contents of the stack after all five operations. Give the values from bottom to top.", [f"Bottom-to-top order starts {a}, {c};", f"Top item is {d}, giving {a}, {c}, {d};"], "", 4),
        ("2", 2, "State the sequence of values removed if the same four inserted values were processed by a queue instead of a stack.", [f"The first removed value is {a};", f"FIFO order gives {a}, {b}, {c}, {d};"], "", 4),
        ("3", 2, "Explain why a stack is suitable for an undo feature in a drawing application.", ["The most recent action is stored at the top of the stack;", "LIFO removal reverses actions in the opposite order to that in which they were performed;"], "", 5),
    ])
    return _question(style, number, "Stacks and queues", "A program applies the operations shown to an initially empty stack.", stimulus, _fit_parts(parts, total))


def _data_structures_hash_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    size = rng.choice([7, 11])
    start = rng.randint(2, size - 2)
    keys = [start, start + size, start + 2 * size]
    final_slots = [start, (start + 1) % size, (start + 2) % size]
    stimulus = Stimulus(
        kind="code",
        title="Hash table rule",
        code=f"index = key MOD {size}\nCollision handling: linear probing\nKeys inserted: {keys[0]}, {keys[1]}, {keys[2]}",
    )
    parts = _parts([
        ("1", 3, "State the table index occupied by each key after all three insertions.", [f"Key {keys[0]} is stored at index {final_slots[0]};", f"Key {keys[1]} is stored at index {final_slots[1]} after one probe;", f"Key {keys[2]} is stored at index {final_slots[2]} after two probes;"], "", 6),
        ("2", 1, "State what is meant by a collision in a hash table.", ["Two different keys produce the same initial table index;"], "", 3),
        ("3", 2, "Explain one reason why the table should not be allowed to become almost full.", ["Linear probing may need to inspect many occupied slots because clusters become longer;", "Insertion and retrieval therefore become slower and may approach a linear search;"], "", 5),
    ])
    return _question(style, number, "Hash tables", "A hash table stores integer keys using the rule shown.", stimulus, _fit_parts(parts, total))


def _data_structures_tree_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    root = rng.choice([40, 50, 60])
    values = [root, root - 20, root + 20, root - 30, root - 10, root + 10]
    stimulus = Stimulus(kind="code", title="Insertion order", code=", ".join(map(str, values)))
    sorted_values = sorted(values)
    parts = _parts([
        ("1", 3, "Draw the binary search tree produced by inserting the values in the stated order.", [f"{root} is the root with {root - 20} as its left child and {root + 20} as its right child;", f"{root - 30} and {root - 10} are respectively the left and right children of {root - 20};", f"{root + 10} is the left child of {root + 20};"], "", 8),
        ("2", 1, "State the in-order traversal of the completed tree.", [f"{', '.join(map(str, sorted_values))};"], "", 3),
        ("3", 2, "Explain why an unbalanced binary search tree can make searching less efficient.", ["Many nodes can lie on one long branch so each comparison removes little of the remaining search space;", "In the worst case the search visits a number of nodes proportional to the number stored, like a linear search;"], "", 5),
    ])
    return _question(style, number, "Binary search trees", "The values shown are inserted into an initially empty binary search tree.", stimulus, _fit_parts(parts, total))


def _data_structures_graph_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    adjacency = "A: B, C\nB: A, D, E\nC: A, F\nD: B\nE: B, F\nF: C, E"
    stimulus = Stimulus(kind="code", title="Adjacency list", code=adjacency)
    parts = _parts([
        ("1", 2, "Starting at A, state the breadth-first traversal when adjacent vertices are considered alphabetically.", ["A, B, C are visited first;", "The complete traversal is A, B, C, D, E, F;"], "", 5),
        ("2", 2, "State one shortest route from A to F and give its number of edges.", ["A, C, F;", "The route contains 2 edges;"], "", 4),
        ("3", 2, "Explain one advantage of an adjacency list over an adjacency matrix for this graph.", ["Only existing edges and their endpoint references need to be stored;", "Because the graph is sparse, this normally uses less memory than storing a cell for every possible pair of vertices;"], "", 5),
    ])
    return _question(style, number, "Graphs", "An undirected graph is represented by the adjacency list shown.", stimulus, _fit_parts(parts, total))


def _data_structures_choice_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    context = rng.choice(["hospital treatment requests", "roadside-assistance callouts", "print jobs in a shared laboratory"])
    parts = _parts([
        ("1", 3, f"Explain why a priority queue is more suitable than an ordinary queue for scheduling {context}.", ["An ordinary queue removes items in arrival/FIFO order;", "A priority queue removes an item according to its stored priority rather than arrival alone;", f"Urgent {context} can therefore be processed before less urgent items while equal-priority items can retain arrival order;"], "", 7),
        ("2", 3, "Explain why a linked list could be preferable to an array when the number of waiting items changes frequently.", ["A linked list can grow or shrink without allocating one fixed contiguous block sized for the maximum;", "Insertion or deletion can update links without shifting all later elements;", "The trade-off is extra link storage and no constant-time indexed access;"], "", 7),
    ])
    return _question(style, number, "Selecting data structures", f"A service needs to schedule {context} and frequently add or remove waiting items.", None, _fit_parts(parts, total))


def _software_classification_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    examples = rng.choice(
        [
            "Spreadsheet|Image editor|Utility software|Translators",
            "Word processor|Video editor|Utility software|Translators",
            "Presentation software|Audio editor|Utility software|Translators",
        ]
    )
    stimulus = Stimulus(
        kind="classification",
        title="Figure 1",
        diagram=examples,
    )
    parts = _parts(
        [
            (
                "1",
                2,
                "Complete Figure 1 by naming the two missing categories of software.",
                [
                    "Application software identified for the user-task examples;",
                    "Utility software identified for the maintenance examples;",
                ],
                "",
                4,
            ),
            (
                "2",
                2,
                "Explain one difference between utility software and application software.",
                [
                    "Utility software maintains, protects or configures the computer system;",
                    "Application software helps a user perform a specific task;",
                ],
                "",
                4,
            ),
            (
                "3",
                4,
                "Compare developing a program in a low-level language with developing it in a high-level language.",
                [
                    "Low-level code offers direct hardware/register control (1 mark);",
                    "Low-level code is processor-specific and harder to maintain (1 mark);",
                    "High-level code provides abstraction and is easier to read or develop (1 mark);",
                    "High-level code usually requires translation and may provide less direct control (1 mark);",
                ],
                "",
                9,
            ),
        ]
    )
    return _question(
        style,
        number,
        "Types of software and programming languages",
        "Figure 1 classifies software and gives examples used by an organisation.",
        stimulus,
        parts,
    )


def _bitmap_storage_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    width, height = rng.choice([(1280, 720), (1600, 900), (1920, 1080)])
    colour_depth = rng.choice([16, 24, 32])
    bits = width * height * colour_depth
    mebibytes = bits / 8 / 1024 / 1024
    stimulus = Stimulus(
        kind="table",
        title="Table 1",
        headers=["Property", "Value"],
        rows=[
            ["Width", f"{width} pixels"],
            ["Height", f"{height} pixels"],
            ["Colour depth", f"{colour_depth} bits per pixel"],
        ],
    )
    parts = _parts(
        [
            (
                "1",
                6,
                "Calculate the minimum uncompressed file size of the bitmap in mebibytes. Show your working and give the answer to two decimal places.",
                [
                    f"Number of pixels = {width} x {height};",
                    f"Number of pixels = {width * height};",
                    f"File size in bits = {width * height} x {colour_depth};",
                    f"File size in bits = {bits};",
                    "Convert bits to bytes and then divide by 1024 squared to obtain MiB;",
                    f"Minimum uncompressed size = {mebibytes:.2f} MiB;",
                ],
                "MiB",
                8,
            ),
            (
                "2",
                2,
                "Explain one effect of increasing the colour depth while keeping the dimensions unchanged.",
                [
                    "More distinct colours can be represented, which can improve colour accuracy or reduce banding;",
                    "More bits are stored for every pixel, so the uncompressed file size increases;",
                ],
                "",
                4,
            ),
        ]
    )
    return _question(
        style,
        number,
        "Bitmap storage",
        "A digital publisher stores an uncompressed bitmap for a magazine cover.",
        stimulus,
        parts,
    )


def _legal_issues_short_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    system = rng.choice(
        [
            "facial-recognition services",
            "generative artificial intelligence",
            "automated recruitment systems",
        ]
    )
    parts = _parts(
        [
            (
                "1",
                3,
                f"Explain why laws governing {system} can be difficult to write and enforce.",
                [
                    "Technology and its uses change faster than legislation;",
                    "Services and data cross national jurisdictions with different laws;",
                    "Technical behaviour, responsibility or harm can be difficult to prove;",
                ],
                "",
                9,
            )
        ]
    )
    return _question(
        style,
        number,
        "Legal issues",
        f"Lawmakers are reviewing the use of {system}.",
        None,
        parts,
    )


def _client_server_short_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    organisation = rng.choice(["a college", "a design studio", "a medical practice"])
    parts = _parts(
        [
            (
                "1",
                3,
                "Explain why a client-server network would be more suitable than a peer-to-peer network.",
                [
                    "Accounts, permissions and security can be managed centrally;",
                    "Files and backups can be maintained centrally and consistently;",
                    "Dedicated servers can provide reliable shared services to many clients;",
                ],
                "",
                9,
            )
        ]
    )
    return _question(
        style,
        number,
        "Client-server networking",
        f"{organisation.title()} needs centrally managed accounts, files and backups.",
        None,
        parts,
    )


def _ipv4_extended_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    organisation = rng.choice(["a regional university", "a logistics company", "a hospital group"])
    return _question(
        style,
        number,
        "IPv4 address exhaustion",
        f"{organisation.title()} is expanding a large network while public IPv4 addresses remain scarce.",
        None,
        _extended_part(
            "Discuss technical approaches that can allow the organisation to connect more devices securely and reliably.",
            [
                "Network address translation lets many private addresses share fewer public IPv4 addresses;",
                "Private IPv4 address ranges can be reused inside separate networks;",
                "DHCP can allocate addresses efficiently for limited lease periods;",
                "IPv6 provides a much larger address space and supports long-term growth;",
                "Dual-stack operation can preserve compatibility during migration;",
                "NAT can complicate inbound connections, peer-to-peer services and troubleshooting;",
                "Firewalls, routing policy and address management remain necessary for security;",
                "A justified conclusion balances compatibility, cost, timescale and future capacity;",
            ],
        ),
    )


def _compression_short_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    data, consequence = rng.choice(
        [
            (
                "medical scan images",
                "No diagnostic detail from the medical scan is discarded, so a clinician can inspect an exact reconstruction;",
            ),
            (
                "executable software backups",
                "Every instruction byte in the executable software backup is restored exactly; a changed or missing byte could corrupt the program or alter its behaviour;",
            ),
            (
                "archived financial records",
                "Every value in the archived financial records is restored exactly, preserving the accuracy required for later audit and reconciliation;",
            ),
        ]
    )
    parts = _parts(
        [
            (
                "1",
                2,
                "State two reasons why data is compressed.",
                [
                    "Less secondary-storage capacity is required;",
                    "Less data must be transmitted, reducing transfer time or bandwidth use;",
                ],
                "",
                4,
            ),
            (
                "2",
                2,
                f"Explain why lossless compression may be required for {data}.",
                [
                    "The original data can be reconstructed exactly;",
                    consequence,
                ],
                "",
                5,
            ),
        ]
    )
    return _question(
        style,
        number,
        "Data compression",
        f"An organisation stores and transmits {data}.",
        None,
        parts,
    )


def _fibonacci_recursion_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    function_name = rng.choice(["sumPositive", "totalPositive", "addPositives"])
    code = (
        f"{function_name} [] = 0\n"
        f"{function_name} (x:xs) =\n"
        f"    (if x > 0 then x else 0) + {function_name} xs"
    )
    stimulus = Stimulus(kind="code", title="Program 1", code=code)
    parts = _parts(
        [
            ("1", 1, "State the base case in Program 1.", ["The empty-list pattern returns 0;"], "", 2),
            ("2", 1, f"State the value returned by {function_name} [-2, 5, 0, 3].", ["8;"], "", 2),
            (
                "3",
                2,
                "Explain how pattern matching controls the recursion in Program 1.",
                [
                    "1 mark: the [] and (x:xs) patterns select between the base and recursive definitions;",
                    "1 development mark: each recursive call uses the tail xs, so the immutable list becomes shorter until [] is matched;",
                ],
                "",
                5,
            ),
            (
                "4",
                2,
                "Explain why the function is a pure function.",
                [
                    "1 mark: the result depends only on the supplied immutable list and the function does not modify external state;",
                    "1 development mark: the same input therefore always produces the same output and evaluating the function has no side effects;",
                ],
                "",
                5,
            ),
        ]
    )
    return _question(
        style,
        number,
        "Functional list processing",
        "Program 1 is written in a functional language and uses pattern matching over an immutable list.",
        stimulus,
        parts,
    )


def _boolean_simplification_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    expression, answer = rng.choice(
        [
            ("A + A·B", "A"),
            ("A·B + A·B̅", "A"),
            ("(A + B)·(A + B̅)", "A"),
        ]
    )
    stimulus = Stimulus(kind="code", title="Expression", code=expression)
    parts = _parts(
        [
            (
                "1",
                4,
                "Using the rules of Boolean algebra, simplify the expression as far as possible. Show each step.",
                [
                    "A valid Boolean identity is selected;",
                    "The identity is applied correctly;",
                    "Intermediate working is logically equivalent to the original expression;",
                    f"Final answer is {answer};",
                ],
                "",
                10,
            )
        ]
    )
    return _question(
        style,
        number,
        "Boolean algebra",
        "A hardware designer wants to simplify a Boolean expression.",
        stimulus,
        parts,
    )


def _assembly_program_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    value = rng.choice([11, 13, 19, 23])
    code = (
        "      MOV R0, #0\n"
        f"      MOV R1, #{value}\n"
        "loop: CMP R1, #0\n"
        "      BEQ end\n"
        "      ADD R0, R0, #1\n"
        "      LSR R1, R1, #1\n"
        "      B loop\n"
        "end:  STR R0, [100]\n"
        "      HALT"
    )
    stimulus = Stimulus(kind="code", title="Program 1", code=code)
    parts = _parts(
        [
            (
                "1",
                6,
                "Explain the purpose of the assembly language program and how the instructions implement it. In this instruction set, # marks an immediate value, [100] is direct memory address 100, and LSR performs a zero-fill logical right shift on an unsigned register.",
                [
                    "Purpose — 1 mark: identifies that the program counts how many logical right shifts are needed for the positive unsigned input to reach zero, equivalently its binary bit length;",
                    f"Purpose — 1 mark: applies that purpose to input {value}, which requires {value.bit_length()} shifts / bits;",
                    "Purpose — 1 mark: states that the final count is stored in direct memory address 100;",
                    "Implementation — 1 mark: R0 is initialised to zero and incremented once on every loop iteration, so it records the shift count;",
                    f"Implementation — 1 mark: R1 starts at {value} and each zero-fill LSR divides its unsigned value by two, discarding the least-significant bit;",
                    "Implementation — 1 mark: CMP and BEQ stop the loop when R1 reaches zero, after which STR writes R0 to [100];",
                ],
                "",
                15,
            )
        ]
    )
    return _question(
        style,
        number,
        "Assembly language program",
        "Program 1 executes on a processor with general-purpose unsigned registers and the instruction conventions stated in the question.",
        stimulus,
        parts,
    )


def _bitmap_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    width = rng.choice([1280, 1920, 2048, 3840, 4000])
    height = rng.choice([720, 1080, 1536, 2160, 3000])
    colours = rng.choice([256, 65536, 16777216])
    bits = {256: 8, 65536: 16, 16777216: 24}[colours]
    stimulus = Stimulus(kind="table", title="Table 1", headers=["Property", "Value"], rows=[["Width", f"{width} pixels"], ["Height", f"{height} pixels"], ["Colours", f"{colours:,}"], ["Colour depth", f"{bits} bits"]])
    parts = _parts([
        ("1", 2, "Calculate the uncompressed size of one bitmap image in mebibytes. You should show your working.", [f"Pixels = {width} x {height};", f"Bits per pixel = {bits};", "Convert from bits to bytes and then to MiB;"], "mebibytes", 5),
        ("2", 1, "State one effect of increasing the colour depth of a bitmap image.", ["More colours can be represented;", "File size increases if resolution is unchanged;"], "", 2),
        ("3", 2, "Explain why metadata may be stored with the image.", ["Metadata stores data about the image such as dimensions/date/location;", "It allows software to interpret, search or manage the image correctly;"], "", 4),
        ("4", 3, "A lossy compression algorithm is applied to the image. Explain one advantage and one disadvantage of using lossy compression.", ["Advantage: smaller file size / faster transmission;", "Disadvantage: some original data is permanently removed;", "Linked explanation to image quality or suitability for purpose;"], "", 6),
    ])
    return _question(style, number, "Bitmap image data", "A digital camera stores images as bitmaps.", stimulus, _fit_parts(parts, total))


def _short_security_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = [
        QuestionPart(
            label="1",
            marks=4,
            prompt="Describe four measures, other than anti-virus software and user training, that can reduce the threat posed by malware.",
            answer_lines=15,
            marking=MarkingGuidance(
                ao="AO1 (understanding)",
                points=[
                    "Firewall can filter or block suspicious network traffic;",
                    "Access rights can limit the files/data malware can modify;",
                    "Regular updates patch vulnerabilities in applications or operating systems;",
                    "Backups kept offline can allow data to be recovered;",
                    "Sandboxing or virtual machines can isolate untrusted files/programs;",
                    "Disabling macros or removable media can reduce infection routes;",
                ],
                accept=["Any other technically valid preventative or recovery measure."],
                reject=["Anti-virus software or user training, as these are excluded by the question."],
            ),
        )
    ]
    return _question(style, number, "Malware protection", "Anti-virus software and user training are measures that can be used to reduce the threat posed by malware.", None, parts)


def _software_roles_three_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    context = rng.choice(
        [
            "A school installs a new operating system on its desktop computers.",
            "A design studio replaces the system software on its workstations.",
        ]
    )
    parts = _parts(
        [
            (
                "1",
                3,
                "Explain three functions performed by an operating system.",
                [
                    "Memory management allocates and releases memory for processes;",
                    "Processor scheduling shares processor time between processes;",
                    "Peripheral management controls access to input/output devices;",
                    "File management organises persistent data and access rights;",
                ],
                "",
                10,
            )
        ]
    )
    return _question(style, number, "Operating-system services", context, None, parts)


def _network_service_three_question(
    style: QuestionStyle,
    number: int,
    total: int,
    rng: random.Random,
) -> Question:
    service = rng.choice(["DNS", "DHCP"])
    if service == "DNS":
        prompt = "Explain how DNS helps a client connect to a named Internet service."
        points = [
            "A resolver receives the domain name requested by the client;",
            "DNS servers are queried until the relevant record is located;",
            "The associated IP address is returned so the client can address packets;",
        ]
    else:
        prompt = "Explain how DHCP configures a client when it joins a network."
        points = [
            "The client broadcasts a request for network configuration;",
            "A DHCP server offers an available IP address and other settings;",
            "The lease is acknowledged and used for a limited period;",
        ]
    parts = _parts([("1", 3, prompt, points, "", 10)])
    return _question(
        style,
        number,
        f"{service} network service",
        "A portable computer has just joined a managed network.",
        None,
        parts,
    )


def _binary_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    first, second = rng.choice([(57, 39), (86, 41), (103, 24), (118, 17)])
    parts = _parts([
        ("1", 2, f"Add the denary numbers {first} and {second}. Give your answer as an 8-bit unsigned binary number.", ["Correct conversion or binary addition method;", "Correct 8-bit binary result;"], "", 4),
        ("2", 2, "Explain what is meant by overflow in unsigned binary arithmetic.", ["Result is too large for the available number of bits;", "Most significant/carry bit is lost or cannot be represented;"], "", 4),
    ])
    return _question(style, number, "Unsigned binary arithmetic", "Unsigned binary is used to store integer values.", None, _fit_parts(parts, total))


def _unicode_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    context = rng.choice(["an international messaging app", "a website storing customer names", "a school database storing pupils' home languages"])
    parts = _parts([
        ("1", 2, "State two differences between ASCII and Unicode.", ["Unicode can represent a much larger character set;", "ASCII uses fewer bits per character than many Unicode encodings;", "Unicode supports characters from many languages;"], "", 4),
        ("2", 2, f"Explain why Unicode would be suitable for {context}.", ["It can represent non-English characters/symbols;", "This avoids data loss or incorrect display for users' text;"], "", 4),
    ])
    return _question(style, number, "Character coding", "Text characters must be represented in binary.", None, _fit_parts(parts, total))


def _fde_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "Describe the role of the program counter during the fetch-execute cycle.", ["Stores address of the next instruction;", "Is incremented or updated after an instruction is fetched/branch executed;"], "", 4),
        ("2", 2, "Describe the role of the memory address register during the fetch stage.", ["Holds the address to be accessed in main memory;", "Receives the address copied from the program counter before the memory read;"], "", 4),
    ])
    return _question(style, number, "Processor registers", "Registers are used while instructions are fetched and executed.", None, _fit_parts(parts, total))


def _protocol_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    layer = rng.choice(["application", "transport", "network", "link"])
    parts = _parts([
        ("1", 2, "State two reasons why network protocols are needed.", ["Allow devices/software from different manufacturers to communicate;", "Define rules/formats/order for messages;", "Support error control, addressing or routing;"], "", 4),
        ("2", 2, f"Describe one function of the {layer} layer in the TCP/IP protocol stack.", ["Valid function of the named layer;", "Description linked to communication between hosts or applications;"], "", 4),
    ])
    return _question(style, number, "Network protocols", "The TCP/IP stack is used when data is transmitted across a network.", None, _fit_parts(parts, total))


def _database_key_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "Explain the difference between a primary key and a foreign key.", ["Primary key uniquely identifies a record in its table;", "Foreign key is an attribute that refers to a primary key in another table;"], "", 4),
        ("2", 2, "Explain why referential integrity is important in a relational database.", ["It prevents foreign key values referring to non-existent records;", "It helps keep relationships between tables consistent/valid;"], "", 4),
    ])
    return _question(style, number, "Relational database keys", "A relational database stores data in linked tables.", None, _fit_parts(parts, total))


def _big_data_short_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "State two characteristics commonly associated with Big Data.", ["Volume;", "Velocity;", "Variety;", "Veracity;"], "", 4),
        ("2", 2, "Explain why distributed processing may be used to analyse Big Data.", ["Data/work can be split across many machines;", "This can reduce processing time or allow datasets too large for one machine to be handled;"], "", 4),
    ])
    return _question(style, number, "Big Data", "An organisation collects large quantities of data from online services.", None, _fit_parts(parts, total))


def _sound_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    rate = rng.choice([44100, 48000, 96000])
    seconds = rng.choice([90, 120, 180])
    resolution = rng.choice([16, 24])
    channels = rng.choice([1, 2])
    size_mib = rate * seconds * resolution * channels / 8 / 1024**2
    stimulus = Stimulus(kind="table", title="Table 1", headers=["Setting", "Value"], rows=[["Sampling rate", f"{rate} Hz"], ["Duration", f"{seconds} seconds"], ["Sample resolution", f"{resolution} bits"], ["Channels", str(channels)]])
    parts = _parts([
        ("1", 2, "Calculate the size of the recording in mebibytes. Show your working and give your answer to two decimal places.", [f"File size = {rate} × {seconds} × {resolution} × {channels} bits;", "Divide by 8 and then by 1024² to convert bits to MiB;", f"Final answer = {size_mib:.2f} MiB;"], "MiB", 5),
        ("2", 2, "Calculate the minimum sampling rate needed to record a sound whose highest frequency is 18 kHz, and justify your answer.", ["36 kHz / 36 000 Hz;", "The Nyquist theorem requires a sampling rate of at least twice the highest frequency in the signal;"], "Hz", 3),
        ("3", 2, "Explain what can happen if the sound is sampled below the Nyquist rate.", ["The samples can represent a false lower-frequency waveform, known as aliasing;", "The original waveform cannot then be reconstructed accurately from those samples;"], "", 4),
        ("4", 4, "Explain how increasing the sampling rate and sample resolution can affect the stored sound.", ["Increasing sampling rate captures the waveform more frequently;", "Increasing sample resolution increases the number of possible amplitude values;", "Both can improve accuracy/quality;", "Both increase file size/storage requirement;"], "", 7),
    ])
    return _question(style, number, "Digital sound", "A sound is sampled and stored digitally.", stimulus, _fit_parts(parts, total))


def _rle_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    row = rng.choice([
        "12, 12, 12, 12, 9, 9, 14, 18, 18, 18, 18, 18, 2, 2, 2, 7",
        "3, 3, 6, 6, 6, 6, 9, 10, 11, 11, 11, 4, 4, 4, 4, 4",
        "20, 21, 22, 22, 22, 8, 8, 8, 8, 1, 1, 5, 5, 5, 9, 9",
    ])
    stimulus = Stimulus(kind="code", title="Figure 1", code=row)
    parts = _parts([
        ("1", 2, "Encode the row of pixels using run length encoding. The run length and the pixel value are each stored using one byte.", ["Correct run lengths identified;", "Correct value paired with each run length;"], "", 4),
        ("2", 2, "Calculate the number of bytes needed before and after RLE.", ["Before RLE: one byte per original pixel;", "After RLE: two bytes per run;"], "bytes", 4),
        ("3", 2, "Comment on whether RLE is effective for this row of pixels.", ["Judgement based on whether encoded data is smaller/larger;", "Explanation linked to number and length of repeated runs;"], "", 4),
        ("4", 2, "State two circumstances in which RLE would be a suitable compression method.", ["Data contains long runs of repeated values;", "The data is lossless-compression sensitive / original must be recoverable;", "Images contain large flat areas of identical colour;"], "", 5),
    ])
    return _question(style, number, "Run length encoding", "A row of bitmap pixel data is to be compressed using RLE.", stimulus, _fit_parts(parts, total))


def _floating_point_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    value = rng.choice(["010110 0011", "101010 0010", "011001 1101"])
    conversion = {
        "010110 0011": "0.10110₂ = 0.6875 and 0011₂ = 3, so 0.6875 × 2³ = 5.5",
        "101010 0010": "1.01010₂ = -1 + 1/4 + 1/16 = -0.6875 and 0010₂ = 2, so -0.6875 × 2² = -2.75",
        "011001 1101": "0.11001₂ = 0.78125 and 1101₂ = -3, so 0.78125 × 2⁻³ = 0.09765625",
    }[value]
    shift = "right" if value.split()[1].startswith("0") else "left"
    stimulus = Stimulus(kind="bitgrid", title="Figure 1", headers=["Mantissa", "Exponent"], rows=[value.split()])
    parts = _parts([
        ("1", 1, "State whether the binary point is shifted left or right when the exponent in Figure 1 is applied.", [f"1 mark: the binary point is shifted {shift};"], "", 2),
        ("2", 1, "Convert the floating point number into denary. The mantissa and exponent are both stored in two's complement, the binary point is immediately after the mantissa sign bit, and value = mantissa × 2^exponent.", [f"1 mark: {conversion};"], "", 3),
        ("3", 1, "State whether the floating point number in Figure 1 is normalised. Give a reason for your answer.", ["1 mark: it is normalised because a two's-complement fractional mantissa starts 01 when positive or 10 when negative; equivalently, its first two bits differ;"], "", 2),
        ("4", 2, "Explain the effect of adding two bits to the mantissa while leaving the exponent unchanged.", ["1 mark: two additional fractional binary place values can be stored in the mantissa;", "1 mark: the smaller interval between adjacent representable values reduces quantisation / rounding error and therefore increases precision;"], "", 3),
        ("5", 3, "Explain the trade-off if a fixed-length floating point format assigns more bits to the exponent and fewer bits to the mantissa.", ["1 mark: the exponent can represent a wider set of powers of two;", "1 mark: the range of magnitudes that can be represented increases;", "1 mark: fewer mantissa bits reduce precision / increase rounding error;"], "", 4),
        ("6", 1, "Name the error that occurs when a non-zero value is too close to zero to be represented.", ["1 mark: underflow;"], "", 2),
    ])
    return _question(style, number, "Floating point representation", "A scientific sensor stores readings using the fixed-length floating point format shown.", stimulus, _fit_parts(parts, total))


def _logic_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    expr = rng.choice(["(A · B) + C", "A · (B + C̅)", "(A ⊕ B) · C", "(A ⊼ B) + C", "(A ⊽ B) ⊕ C"])
    stimulus = Stimulus(kind="code", title="Boolean expression", code=expr)
    parts = _parts([
        ("1", 2, "Draw a logic circuit for the expression shown in Figure 1.", ["Correct gates selected;", "Correct connections/order of gates;"], "", 5),
        ("2", 3, "Complete a truth table for the expression.", ["All input combinations attempted;", "Intermediate output correct;", "Final output correct;"], "", 7),
        ("3", 3, "Explain one benefit of using Boolean algebra to simplify a logic circuit.", ["Simplification can reduce number of gates;", "This can reduce cost/power/latency;", "Answer linked to maintaining same logical output;"], "", 5),
    ])
    return _question(style, number, "Logic gates", f"A logic circuit implements the expression {expr}.", stimulus, _fit_parts(parts, total))


def _boolean_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    expr = rng.choice(["A·B + A·C", "A + A·B", "(A + B)·(A + C)"])
    stimulus = Stimulus(kind="code", title="Expression", code=expr)
    parts = _parts([
        ("1", 2, "State the Boolean algebra law that could be used in the first simplification step.", ["Correct law named, such as absorption/distribution/identity;", "Law is relevant to the expression;"], "", 3),
        ("2", 2, "Simplify the expression as far as possible.", ["Valid simplification step;", "Final simplified expression correct;"], "", 5),
        ("3", 4, "Explain why simplifying Boolean expressions can improve a hardware design.", ["Fewer gates may be required;", "Circuit can be cheaper or use less power;", "Propagation delay may be reduced;", "Same output is preserved;"], "", 7),
    ])
    return _question(style, number, "Boolean algebra", "A designer wants to simplify a Boolean expression before implementing it as hardware.", stimulus, _fit_parts(parts, total))


def _truth_table_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    expression, rows, outputs = rng.choice(
        [
            ("(A · B) + C", [["0", "0", "0", ""], ["0", "1", "1", ""], ["1", "0", "0", ""], ["1", "1", "1", ""]], ["0", "1", "0", "1"]),
            ("A · (B + C̅)", [["0", "0", "0", ""], ["0", "1", "0", ""], ["1", "0", "1", ""], ["1", "1", "0", ""]], ["0", "0", "0", "1"]),
            ("(A ⊕ B) · C", [["0", "1", "1", ""], ["1", "0", "1", ""], ["1", "1", "1", ""], ["0", "0", "1", ""]], ["1", "1", "0", "0"]),
        ]
    )
    valid_rows = [row[:3] for row, output in zip(rows, outputs, strict=True) if output == "1"]
    valid_text = " or ".join(
        f"A={row[0]}, B={row[1]}, C={row[2]}" for row in valid_rows
    )
    stimulus = Stimulus(kind="truth_table", title="Figure 1", headers=["A", "B", "C", "X"], rows=rows)
    parts = _parts([
        ("1", 4, f"Complete Figure 1 for the Boolean expression {expression}.", [
            f"Row {row_index}: X = {output};"
            for row_index, output in enumerate(outputs, start=1)
        ], "", 7),
        ("2", 2, "State one input combination from Figure 1 for which X has the value 1.", [
            f"1 mark for A and B values matching one of these rows: {valid_text};",
            "1 mark for the corresponding C value from the same row;",
        ], "", 4),
        ("3", 1, "Explain one reason why a truth table is useful when testing a logic circuit.", [
            "Award 1 mark for one valid reason, such as comparing expected and actual outputs systematically or finding an incorrect circuit output;",
        ], "", 5),
    ])
    return _question(style, number, "Truth tables", "A logic circuit has three inputs, A, B and C, and one output, X.", stimulus, _fit_parts(parts, total))


def _translator_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "Describe the difference between source code and object code.", ["Source code is written by programmers / human-readable;", "Object code is machine code or translated code executable by the processor;"], "", 4),
        ("2", 2, "Explain the role of lexical analysis during compilation.", ["Input source code is split into tokens;", "Invalid tokens/lexical errors can be identified;"], "", 4),
        ("3", 2, "Explain why bytecode may be used instead of native machine code.", ["Bytecode is portable across platforms with a virtual machine;", "It can be interpreted/JIT compiled on the target machine;"], "", 4),
        ("4", 2, "State two advantages of using a high-level programming language.", ["Easier for humans to read/write/maintain;", "More portable than machine code;", "Provides abstractions/libraries;"], "", 4),
    ])
    return _question(style, number, "Programming languages and translators", "A program is written in a high-level language and translated before it is executed.", None, _fit_parts(parts, total))


def _security_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 4, "Describe four measures, other than anti-virus software, that can reduce the threat posed by malware.", ["Firewall can filter suspicious network traffic;", "Access rights limit damage to files/data;", "Regular updates patch vulnerabilities;", "Backups allow recovery after infection;", "User training reduces risky behaviour;"], "", 8),
        ("2", 2, "Explain why a sandbox may be used when opening an unknown file.", ["File runs in an isolated environment;", "This reduces risk to the host system or data;"], "", 4),
        ("3", 2, "Explain one limitation of relying only on user training.", ["Users can still make mistakes or ignore guidance;", "New threats may not be recognised by users;"], "", 4),
    ])
    return _question(style, number, "System security", "An organisation wants to reduce the risk of malware damaging its computer systems.", None, _fit_parts(parts, total))


def _processor_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "State the purpose of the address bus and the data bus.", ["Address bus carries the location/address being accessed;", "Data bus carries data/instructions between processor and memory/devices;"], "", 4),
        ("2", 2, "Explain why the control bus is needed.", ["It carries control signals such as read/write/interrupt;", "It coordinates components so operations happen at the correct time;"], "", 4),
        ("3", 2, "Describe the role of the program counter and memory address register in the fetch stage.", ["PC stores address of next instruction;", "Address is copied to MAR;", "PC is incremented/updated ready for next fetch;"], "", 5),
        ("4", 2, "Explain how increasing clock speed can affect processor performance.", ["More cycles per second can be completed;", "Instructions may execute faster if not limited by other factors;", "Heat/power consumption may increase or bottlenecks may limit improvement;"], "", 5),
    ])
    return _question(style, number, "Processor architecture", "A processor uses registers and buses during the fetch-execute cycle.", None, _fit_parts(parts, total))


def _stored_program_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "Explain the stored program concept.", ["Instructions and data are stored in main memory;", "The processor fetches instructions from memory to execute them;"], "", 4),
        ("2", 6, "Describe how one instruction is processed during the fetch-decode-execute cycle.", [
            "The program counter value is copied to the memory address register, then the address bus carries that address to memory;",
            "The control unit sends a memory-read signal on the control bus;",
            "The data bus carries the instruction from memory to the memory data register, and it is copied to the current instruction register;",
            "The program counter is incremented so that it identifies the next instruction;",
            "The control unit decodes the instruction in the current instruction register;",
            "The control unit issues control signals and the instruction is executed using the ALU, registers or memory as required;",
        ], "", 10),
        ("3", 1, "State the role of the current instruction register.", ["It stores the instruction currently being decoded or executed;"], "", 3),
        ("4", 1, "State one benefit of the stored program concept.", ["Because instructions are held as addressable data in memory, a different instruction sequence can be loaded and run without redesigning the processor's hardware circuits;"], "", 3),
    ])
    return _question(style, number, "Stored program concept", "A von Neumann architecture computer executes machine code instructions.", None, _fit_parts(parts, total))


def _packet_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    stimulus = Stimulus(kind="packet", title="Figure 1", headers=["Destination address", "Source address", "Payload", "Checksum"], rows=[["203.0.113.8", "198.51.100.4", "data", "A93F"]])
    parts = _parts([
        ("1", 2, "Name two fields typically found in a packet header that are not shown in Figure 1.", ["Sequence number;", "Time to live / hop limit;", "Protocol/port number;", "Packet length;"], "", 3),
        ("2", 2, "Explain what the checksum is used for.", ["Used to detect transmission errors;", "Receiver recalculates/checks value and compares it with the transmitted checksum;"], "", 4),
        ("3", 2, "Describe the role of a router in packet switching.", ["Router examines destination address;", "Router forwards packet along an appropriate next route/path;"], "", 4),
        ("4", 2, "Explain one advantage of packet switching compared with circuit switching.", ["No dedicated circuit is required;", "Network capacity can be shared more efficiently/resiliently;"], "", 4),
    ])
    return _question(style, number, "Packet switching", "Figure 1 shows selected fields from a packet transmitted across a packet-switched network.", stimulus, _fit_parts(parts, total))


def _network_topology_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    topology = rng.choice(["client-switch-router-server", "mesh-wan", "star-lan"])
    stimulus = Stimulus(kind="network", title="Figure 1", diagram=topology)
    parts = _parts([
        ("1", 2, "Name two devices shown in Figure 1 that are used to connect computers or networks.", ["Switch;", "Router;", "Wireless access point if shown;"], "", 4),
        ("2", 3, "Describe how data would be sent from a client to the server shown in Figure 1.", ["Data is split into packets or frames as appropriate;", "Switch forwards frames within the local network;", "Router forwards packets between networks using addresses/routing table;"], "", 7),
        ("3", 3, "Explain one advantage and one disadvantage of the topology shown in Figure 1.", ["Advantage linked to central management, scalability or fault isolation;", "Disadvantage linked to central device failure, cost or cabling;", "Explanation is applied to the network diagram;"], "", 7),
    ])
    return _question(style, number, "Network topology", "Figure 1 shows part of a computer network.", stimulus, _fit_parts(parts, total))


def _tcpip_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    stimulus = Stimulus(kind="table", title="Table 1", headers=["Layer", "Example protocol"], rows=[["Application", "HTTPS"], ["Transport", "TCP"], ["Internet", "IP"], ["Link", "Ethernet"]])
    parts = _parts([
        ("1", 1, "State the layer of the TCP/IP stack that is responsible for routing packets between networks.", ["Internet layer;"], "", 2),
        ("2", 2, "Explain the role of DNS when a user enters a URL.", ["DNS resolves a domain name;", "It returns an IP address used to contact the server;"], "", 4),
        ("3", 2, "Explain why TCP uses sequence numbers.", ["They allow packets/segments to be reordered;", "They help identify missing data for retransmission;"], "", 4),
        ("4", 3, "Describe how HTTPS helps protect data sent over the Internet.", ["Uses encryption/TLS;", "Certificates authenticate the server;", "Protects confidentiality/integrity of transmitted data;"], "", 6),
    ])
    return _question(style, number, "TCP/IP and the Internet", "A client communicates with a web server using the TCP/IP stack.", stimulus, _fit_parts(parts, total))


def _sql_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    stimulus = Stimulus(
        kind="code",
        title="Database schema",
        code=(
            "MEMBER(MemberID, FullName, Email)\n"
            "SESSION(SessionID, Activity, StartsAt, Capacity)\n"
            "BOOKING(MemberID*, SessionID*, BookedAt, Attended)\n"
            "Primary keys: MEMBER.MemberID; SESSION.SessionID\n"
            "BOOKING primary key: (MemberID, SessionID)\n"
            "Foreign keys: BOOKING.MemberID; BOOKING.SessionID"
        ),
    )
    parts = _parts([
        ("1", 2, "The following SQL contains an error. Identify the error and write the corrected condition.\nSELECT FullName FROM MEMBER WHERE Email = NULL;", ["The error is comparing NULL using =;", "Use WHERE Email IS NULL;"], "", 5),
        ("2", 3, "Write one SELECT query that lists each Activity and the number of bookings for it, including only activities with at least five bookings. Sort the result from most to fewest bookings.", ["JOIN SESSION to BOOKING using SessionID;", "GROUP BY Activity and use HAVING COUNT(*) >= 5;", "ORDER BY COUNT(*) DESC;"], "", 8),
        ("3", 2, "Write one INSERT statement to add member 1842, named 'Amira Khan', with email 'amira@example.org' to MEMBER.", ["INSERT INTO MEMBER (MemberID, FullName, Email) used;", "VALUES (1842, 'Amira Khan', 'amira@example.org') used in matching order;"], "", 5),
        ("4", 3, "Write one UPDATE statement that marks member 1842 as having attended session 27. Your statement must not change any other booking.", ["UPDATE BOOKING SET Attended = TRUE (or an equivalent valid Boolean value);", "WHERE MemberID = 1842 used;", "AND SessionID = 27 used in the same WHERE condition;"], "", 7),
        ("5", 2, "Write one DELETE statement that removes bookings for session 27 only where Attended is FALSE.", ["DELETE FROM BOOKING used;", "WHERE SessionID = 27 AND Attended = FALSE, or an equivalent valid Boolean comparison;"], "", 5),
    ])
    parts = [
        part.model_copy(
            update={
                "marking": part.marking.model_copy(update={"ao": "AO3 (programming)"})
            }
        )
        for part in parts
    ]
    return _question(
        style,
        number,
        "Relational databases",
        "A community fitness centre stores members, activity sessions and bookings in a relational database.",
        stimulus,
        _fit_parts(parts, total),
    )


def _erd_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    stimulus = Stimulus(kind="erd", title="Figure 1", diagram="CUSTOMER -< ORDER -< ORDER_ITEM >- PRODUCT")
    parts = _parts([
        ("1", 2, "State the cardinality of the relationship between CUSTOMER and ORDER.", ["One customer can place many orders;", "Each order belongs to one customer;"], "", 4),
        ("2", 2, "Explain why ORDER_ITEM is needed in the design.", ["It resolves the many-to-many relationship between ORDER and PRODUCT;", "It can store attributes such as quantity/price for each product in an order;"], "", 4),
        ("3", 2, "State two fields that would be suitable foreign keys.", ["CustomerID in ORDER;", "OrderID in ORDER_ITEM;", "ProductID in ORDER_ITEM;"], "", 3),
        ("4", 2, "Explain one benefit of using a relational database for this data.", ["Relationships can be enforced using keys;", "Queries can combine related data reliably;", "Redundancy can be reduced;"], "", 4),
    ])
    return _question(style, number, "Entity relationship modelling", "An online shop stores orders in a relational database.", stimulus, _fit_parts(parts, total))


def _big_data_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    parts = _parts([
        ("1", 2, "State two characteristics of Big Data.", ["Volume;", "Velocity;", "Variety;", "Veracity;"], "", 3),
        ("2", 4, "Explain why a distributed system may be used to process Big Data.", ["Data may be too large for one machine;", "Processing can be split across many nodes;", "Parallel processing can reduce processing time;", "Fault tolerance can be improved through replication;"], "", 8),
        ("3", 2, "Explain one reason why data quality is important when mining large datasets.", ["Poor quality data can produce misleading patterns;", "Decisions based on inaccurate data may be invalid/unfair;"], "", 4),
    ])
    return _question(style, number, "Big Data", "A company analyses a large stream of customer interaction data.", None, _fit_parts(parts, total))


def _functional_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    code = (
        "map (lambda x -> x * x)\n"
        "    (filter (lambda x -> x > 3)\n"
        "        [1, 4, 6, 2, 5])"
    )
    stimulus = Stimulus(kind="code", title="Program 1", code=code)
    parts = _parts([
        ("1", 2, "State the output of Program 1.", ["Filter keeps 4, 6 and 5;", "Map squares values to give 16, 36 and 25;"], "", 4),
        ("2", 2, "Explain what is meant by a higher-order function.", ["A function that takes a function as an argument;", "Or returns a function as its result;"], "", 4),
        ("3", 2, "Explain why immutability can make functional programs easier to reason about.", ["Values are not changed after creation;", "This reduces side effects/unexpected state changes;"], "", 4),
        ("4", 2, "Describe one use of recursion in functional programming.", ["A function calls itself;", "It processes a list/problem by reducing it to a base case;"], "", 4),
    ])
    return _question(style, number, "Functional programming", "A program uses higher-order functions.", stimulus, _fit_parts(parts, total))


def _recursion_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    code = "sum [] = 0\nsum (x:xs) = x + sum xs"
    stimulus = Stimulus(kind="code", title="Program 1", code=code)
    parts = _parts([
        ("1", 2, "Identify the base case and the recursive case in Program 1.", ["Base case is sum [] = 0;", "Recursive case is sum (x:xs) = x + sum xs;"], "", 4),
        ("2", 2, "State the result of evaluating sum [3, 5, 7]. Show the recursive accumulation.", ["The recursive cases produce 3 + 5 + 7 + sum [];", "The base case contributes 0, giving a final result of 15;"], "", 4),
        ("3", 4, "Explain how head and tail are used when processing a list recursively.", ["Head is the first item in a list;", "Tail is the remaining list;", "Recursive function processes head and calls itself on tail;", "Base case stops recursion when list is empty;"], "", 7),
    ])
    return _question(style, number, "Recursion in functional programming", "A recursive function processes a list.", stimulus, _fit_parts(parts, total))


def _assembly_trace_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    code = "\n".join(
        [
            "      MOV R0, #0",
            "      MOV R1, #13",
            "      MOV R2, #0",
            "loop: CMP R1, #0",
            "      BEQ end",
            "      ADD R0, R0, #1",
            "      AND R3, R1, #1",
            "      ADD R2, R2, R3",
            "      LSR R1, R1, #1",
            "      B loop",
            "end:  STR R2, 120",
            "      HALT",
        ]
    )
    stimulus = Stimulus(kind="code", title="Figure 1", code=code)
    parts = _parts([
        ("1", 6, "Complete a trace table to show the results of executing the assembly language program in Figure 1.", ["Initial register values copied correctly;", "Each loop iteration updates R0 and R1 correctly;", "AND result in R3 is recorded correctly;", "Running total in R2 is updated correctly;", "Loop stops when R1 is 0;", "Final value stored in memory location 120 is correct;"], "", 20),
        ("2", 2, "By considering your trace table, describe the purpose of the program.", ["Counts the number of 1 bits in the binary representation of the input value;", "Stores the count in memory location 120;"], "", 7),
        ("3", 2, "Describe two advantages of writing programs in assembly language rather than a high-level language.", ["Can directly control registers/hardware;", "Can produce efficient code for a specific processor;", "Useful for low-level embedded/system routines;"], "", 7),
        ("4", 1, "Some high-level languages are described as imperative. Explain what imperative means in this context.", ["The program is written as a sequence of commands/statements that change state;"], "", 4),
    ])
    return _question(style, number, "Assembly language trace", "Figure 1 shows an assembly language program for a processor using general purpose registers.", stimulus, parts)


def _functional_type_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    stimulus = Stimulus(kind="code", title="Function type", code="f: Natural -> Real")
    parts = _parts([
        ("1", 1, "Describe the co-domain of the function f.", ["The co-domain is the set of real numbers / possible output type Real;"], "", 4),
        ("2", 3, "Describe two features of functional programming languages that make it easier to write code that can be distributed to run across multiple servers.", ["Functions avoid side effects / use immutable data;", "This reduces shared-state conflicts between servers;", "Higher-order functions such as map/reduce can split processing across data items;", "Pure functions can be evaluated independently/in parallel;"], "", 10),
    ])
    return _question(style, number, "Functional programming function type", "A functional programming function f has the function type shown below.", stimulus, parts)


def _extended_part(prompt: str, points: list[str]) -> list[QuestionPart]:
    return [
        QuestionPart(
            label="1",
            prompt=prompt,
            marks=12,
            answer_lines=18,
            marking=MarkingGuidance(
                ao="AO1/AO2 extended response",
                points=points,
                levels=[
                    "Level 4, 10-12 marks: detailed and accurate technical knowledge is applied directly to the scenario. Analysis is sustained, competing considerations are weighed and the conclusion is fully justified.",
                    "Level 3, 7-9 marks: generally accurate knowledge is applied to the scenario. Several points are developed and both sides are considered, leading to a reasoned conclusion.",
                    "Level 2, 4-6 marks: some relevant knowledge is shown, but application or development is uneven. The response may consider more than one view, although its conclusion is only partly supported.",
                    "Level 1, 1-3 marks: limited relevant knowledge is presented as isolated or weakly developed points. Application is generic and any conclusion is asserted rather than justified.",
                    "0 marks: nothing creditworthy.",
                ],
            ),
        )
    ]


def _ethics_extended_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    return _question(
        style,
        number,
        "Consequences of computing",
        "A local authority plans to use automated decision-making software to prioritise applications for public services.",
        None,
        _extended_part(
            "Discuss the legal, moral and ethical issues that should be considered before the system is used.",
            [
                "Privacy concerns if sensitive personal data is collected or shared;",
                "Bias in training data may lead to unfair decisions;",
                "Transparency/explainability is needed so decisions can be challenged;",
                "Security and access controls are needed to protect stored data;",
                "Benefits may include consistency, speed and reduced administrative cost;",
                "Conclusion justified by reference to stakeholders and safeguards;",
            ],
        ),
    )


def _database_extended_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    question = _question(
        style,
        number,
        "Database design choice",
        "A music streaming company stores account, playlist and listening-history data for millions of users.",
        None,
        _extended_part(
            "Discuss whether a relational database or a NoSQL database would be more suitable for this system.",
            [
                "Relational database supports structured tables, keys and referential integrity;",
                "SQL makes complex joins/queries over accounts and playlists possible;",
                "NoSQL may scale horizontally for very large or fast-changing datasets;",
                "NoSQL can handle varied/semi-structured listening events;",
                "Trade-off between consistency, flexibility, scalability and query complexity;",
                "Conclusion linked to the company's data volume, variety and required operations;",
            ],
        ),
    )
    return question.model_copy(update={"parts": _fit_parts(question.parts, total)})


def _network_extended_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    return _question(
        style,
        number,
        "Network security",
        "A school allows students and staff to access services using personal devices connected to its wireless network.",
        None,
        _extended_part(
            "Discuss the measures that could be used to protect the network while still allowing convenient access.",
            [
                "Authentication and access rights can restrict services to authorised users;",
                "Encryption protects data transmitted over wireless links;",
                "Firewalls/proxy servers/filtering can monitor and block risky traffic;",
                "Network segmentation separates personal devices from sensitive systems;",
                "Monitoring and user policies can reduce misuse but may affect privacy/convenience;",
                "Conclusion balances security, usability, cost and management overhead;",
            ],
        ),
    )


def _functional_extended_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    question = _question(
        style,
        number,
        "Functional programming paradigm",
        "A team is deciding whether to use a functional programming language for a data-processing application.",
        None,
        _extended_part(
            "Discuss the advantages and disadvantages of using a functional programming approach for this application.",
            [
                "Immutability can reduce side effects and make reasoning/testing easier;",
                "Higher-order functions such as map/filter/reduce suit data-processing tasks;",
                "Recursion and function composition can produce concise solutions;",
                "Some programmers may find the paradigm harder to learn/read;",
                "Performance or memory use may be a concern depending on implementation;",
                "Conclusion linked to team experience and the nature of the data-processing task;",
            ],
        ),
    )
    return question.model_copy(update={"parts": _fit_parts(question.parts, total)})
