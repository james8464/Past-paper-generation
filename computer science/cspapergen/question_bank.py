from __future__ import annotations

import random
from dataclasses import dataclass

from cspapergen.models import MarkingGuidance, MultipleChoiceOption, Question, QuestionPart, Stimulus


@dataclass(frozen=True)
class QuestionStyle:
    id: str
    topic_id: str
    totals: tuple[int, ...]
    maker: str


QUESTION_STYLES = [
    QuestionStyle("short_security", "4.6", (4,), "short_security"),
    QuestionStyle("binary_arithmetic_short", "4.5", (4,), "binary_short"),
    QuestionStyle("unicode_ascii_short", "4.5", (4,), "unicode_short"),
    QuestionStyle("fde_register_short", "4.7", (4,), "fde_short"),
    QuestionStyle("protocol_layers_short", "4.9", (4,), "protocol_short"),
    QuestionStyle("database_key_short", "4.10", (4,), "database_key_short"),
    QuestionStyle("big_data_short", "4.11", (4,), "big_data_short"),
    QuestionStyle("bitmap_size", "4.5", (7, 8, 10, 14), "bitmap"),
    QuestionStyle("sound_sampling", "4.5", (7, 8, 10, 14), "sound"),
    QuestionStyle("rle_compression", "4.5", (7, 8, 9, 10, 14), "rle"),
    QuestionStyle("floating_point", "4.5", (8, 9, 10), "float"),
    QuestionStyle("logic_truth_table", "4.6", (8, 9, 14), "logic"),
    QuestionStyle("boolean_algebra", "4.6", (8, 9, 10, 14), "boolean"),
    QuestionStyle("translator_language", "4.6", (8, 10), "translator"),
    QuestionStyle("security_measures", "4.6", (8, 10), "security"),
    QuestionStyle("processor_buses", "4.7", (8, 10), "processor"),
    QuestionStyle("stored_program", "4.7", (8, 10), "stored"),
    QuestionStyle("packet_switching", "4.9", (7, 8, 9, 10, 14), "packet"),
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
        "bitmap": _bitmap_question,
        "short_security": _short_security_question,
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
        "boolean": _boolean_question,
        "translator": _translator_question,
        "security": _security_question,
        "processor": _processor_question,
        "stored": _stored_program_question,
        "packet": _packet_question,
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
    stimulus = Stimulus(kind="table", title="Table 1", headers=["Setting", "Value"], rows=[["Sampling rate", f"{rate} Hz"], ["Duration", f"{seconds} seconds"], ["Sample resolution", f"{resolution} bits"], ["Channels", str(channels)]])
    parts = _parts([
        ("1", 2, "Calculate the size of the recording in mebibytes. You should show your working.", [f"Samples = {rate} x {seconds} x {channels};", f"Each sample uses {resolution} bits;", "Convert bits to bytes and bytes to MiB;"], "mebibytes", 5),
        ("2", 1, "State the minimum sampling rate needed to accurately record a sound whose highest frequency is 18 kHz.", ["36 kHz / 36 000 Hz;"], "Hz", 2),
        ("3", 1, "Name the theorem used to justify your answer to the previous part.", ["Nyquist theorem;"], "", 2),
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
    stimulus = Stimulus(kind="bitgrid", title="Figure 1", headers=["Mantissa", "Exponent"], rows=[value.split()])
    parts = _parts([
        ("1", 2, "State the mantissa and exponent shown in Figure 1.", ["Correct mantissa copied;", "Correct exponent copied;"], "", 3),
        ("2", 2, "Convert the floating point number into denary.", ["Correct binary point movement shown;", "Correct denary value;"], "", 4),
        ("3", 2, "Explain the effect of increasing the number of bits used for the mantissa.", ["More significant bits can be stored;", "Precision/accuracy of represented values increases;", "Range may decrease if total bit length is fixed;"], "", 4),
        ("4", 2, "Explain the effect of increasing the number of bits used for the exponent.", ["Larger/smaller powers can be represented;", "Range of values increases;", "Precision may decrease if total bit length is fixed;"], "", 4),
    ])
    return _question(style, number, "Floating point representation", "A floating point representation uses two's complement for both mantissa and exponent.", stimulus, _fit_parts(parts, total))


def _logic_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    expr = rng.choice(["(A AND B) OR C", "A AND (B OR NOT C)", "(A XOR B) AND C"])
    stimulus = Stimulus(kind="logic", title="Figure 1", diagram=expr)
    parts = _parts([
        ("1", 2, "Draw a logic circuit for the expression shown in Figure 1.", ["Correct gates selected;", "Correct connections/order of gates;"], "", 5),
        ("2", 3, "Complete a truth table for the expression.", ["All input combinations attempted;", "Intermediate output correct;", "Final output correct;"], "", 7),
        ("3", 3, "Explain one benefit of using Boolean algebra to simplify a logic circuit.", ["Simplification can reduce number of gates;", "This can reduce cost/power/latency;", "Answer linked to maintaining same logical output;"], "", 5),
    ])
    return _question(style, number, "Logic gates", f"A logic circuit implements the expression {expr}.", stimulus, _fit_parts(parts, total))


def _boolean_question(style: QuestionStyle, number: int, total: int, rng: random.Random) -> Question:
    expr = rng.choice(["A.B + A.C", "A + A.B", "(A + B).(A + C)"])
    stimulus = Stimulus(kind="code", title="Expression", code=expr)
    parts = _parts([
        ("1", 2, "State the Boolean algebra law that could be used in the first simplification step.", ["Correct law named, such as absorption/distribution/identity;", "Law is relevant to the expression;"], "", 3),
        ("2", 2, "Simplify the expression as far as possible.", ["Valid simplification step;", "Final simplified expression correct;"], "", 5),
        ("3", 4, "Explain why simplifying Boolean expressions can improve a hardware design.", ["Fewer gates may be required;", "Circuit can be cheaper or use less power;", "Propagation delay may be reduced;", "Same output is preserved;"], "", 7),
    ])
    return _question(style, number, "Boolean algebra", "A designer wants to simplify a Boolean expression before implementing it as hardware.", stimulus, _fit_parts(parts, total))


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
        ("2", 2, "State the role of the current instruction register.", ["Stores the instruction currently being decoded/executed;", "Allows the control unit to interpret the instruction;"], "", 4),
        ("3", 4, "Describe the fetch-decode-execute cycle.", ["Fetch instruction from memory using address in PC/MAR;", "Decode instruction in control unit;", "Execute operation using ALU/registers/memory as required;", "Update PC/status registers as appropriate;"], "", 8),
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
    return _question(style, number, "Packet switching", "Data is transmitted across a packet-switched network.", stimulus, _fit_parts(parts, total))


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
    stimulus = Stimulus(kind="code", title="Table 1", code="Student(StudentID, Name, HouseID)\nHouse(HouseID, HouseName)")
    parts = _parts([
        ("1", 2, "Identify the primary key in Student and the foreign key in Student.", ["StudentID identified as primary key;", "HouseID identified as foreign key;"], "", 3),
        ("2", 2, "Explain why the data should be normalised.", ["Reduces data duplication/redundancy;", "Reduces update/insert/delete anomalies and improves consistency;"], "", 4),
        ("3", 3, "Write an SQL query to output the names of students in house 'Kepler'.", ["SELECT Name used;", "Correct tables/join condition used;", "WHERE HouseName = 'Kepler' used;"], "", 7),
        ("4", 1, "State the purpose of referential integrity in this database.", ["Ensures a foreign key refers to an existing primary key;", "Prevents orphan records/inconsistent relationships;", "Linked to Student and House tables;"], "", 3),
    ])
    return _question(style, number, "Relational databases", "A school stores student and house data in a relational database.", stimulus, _fit_parts(parts, total))


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
    code = "map (lambda x -> x * x) (filter (lambda x -> x > 3) [1, 4, 6, 2, 5])"
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
        ("2", 2, "State the result of evaluating sum [3, 5, 7].", ["15;"], "", 3),
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
    stimulus = Stimulus(kind="code", title="Function type", code="f: \u2115 -> \u211d")
    parts = _parts([
        ("1", 1, "Describe the co-domain of the function f.", ["The co-domain is the set of real numbers / possible output type \u211d;"], "", 4),
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
                    "9-12 marks: coherent, balanced answer with well-developed technical points and a justified conclusion.",
                    "5-8 marks: relevant explanation with some development and some balance.",
                    "1-4 marks: limited knowledge or isolated points with little development.",
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
    return _question(
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
    return _question(
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
