"""Bounded CS source templates. Inputs are candidate data, never answer keys.

No generated program is executed. Each declared template has fixed semantics;
the independent solver derives every requested output from these typed inputs.
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from Backend.Core.numeric_integrity import (
    NUMBER,
    CheckedTextOutput,
    NumericOutput,
    numeric_result,
)


class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SumTrace(Inputs):
    kind: Literal["bounded-sum-trace"] = "bounded-sum-trace"
    values: list[int] = Field(min_length=3, max_length=7)
    initial_total: int
    threshold: int

    def code(self) -> str:
        return "\n".join([
            f"01 total = {self.initial_total}",
            f"02 for index = 0 to {len(self.values) - 1}",
            f"03     if values[index] > {self.threshold} then",
            "04         total = total + values[index]",
            "05     endif", "06 next index", "07 print(total)",
        ])


class DenaryHex(Inputs):
    kind: Literal["denary-hex"] = "denary-hex"
    value: int = Field(ge=0, le=255)


class BitmapBytes(Inputs):
    kind: Literal["bitmap-bytes"] = "bitmap-bytes"
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    depth: int = Field(gt=0)


class SoundBytes(Inputs):
    kind: Literal["sound-bytes"] = "sound-bytes"
    sample_rate: int = Field(gt=0)
    sample_depth: int = Field(gt=0)
    duration: int = Field(gt=0)
    channels: int = Field(gt=0)


class UnsignedSum(Inputs):
    kind: Literal["unsigned-sum"] = "unsigned-sum"
    left: int = Field(ge=0, le=255)
    right: int = Field(ge=0, le=255)


class FloatingEncode(Inputs):
    kind: Literal["floating-encode"] = "floating-encode"
    value: str
    mantissa_bits: int = Field(ge=2, le=16)
    exponent_bits: int = Field(ge=2, le=8)


class BooleanEvaluation(Inputs):
    kind: Literal["boolean-evaluation"] = "boolean-evaluation"
    expression: Literal["A OR B", "(NOT A) AND B", "A XOR B"]
    inputs: list[dict[str, Literal[0, 1]]] = Field(min_length=1, max_length=8)


CS_INPUTS = TypeAdapter(Annotated[SumTrace | DenaryHex | BitmapBytes | SoundBytes |
    UnsignedSum | FloatingEncode | BooleanEvaluation, Field(discriminator="kind")])


def solve_computer_science_contract(item: dict[str, Any]) -> dict[str, Any] | None:
    raw = (item.get("authoring_context") or {}).get("cs_input_contract")
    if raw is None:
        return None
    source = CS_INPUTS.validate_python(raw)
    numbers: dict[str, Decimal] = {}
    outputs: list[NumericOutput] = []
    texts: list[CheckedTextOutput] = []

    def number(role: str, label: str, value: int | Decimal, unit: str = "1") -> None:
        numbers[role] = Decimal(value)
        outputs.append(NumericOutput(role=role, unit=unit, decimal_places=0,
            scheme_pattern=rf"^{re.escape(label)}:[ \t]*(?P<value>{NUMBER})"))

    def text(role: str, label: str, value: str) -> None:
        texts.append(CheckedTextOutput(role=role, value=value,
            whole_statement=True,
            scheme_pattern=rf"^{re.escape(label)}:[ \t]*(.*?)\.[ \t]*$"))

    steps: list[str]
    if isinstance(source, SumTrace):
        total = source.initial_total
        for index, value in enumerate(source.values):
            if value > source.threshold:
                total += value
            number(f"iteration-{index + 1}-total", f"After iteration {index + 1}, total", total)
        number("output", "Final output", total)
        steps = ["Initialise total; use zero-based indexing and the inclusive loop bound.",
                 "Apply the strict greater-than test and conditional accumulation at each iteration.",
                 "Print once, after the complete loop; intermediate totals are not printed outputs."]
    elif isinstance(source, DenaryHex):
        text("hexadecimal", "Hexadecimal", f"{source.value:02X}")
        steps = ["Divide the denary value by sixteen; encode the quotient and remainder as hexadecimal digits."]
    elif isinstance(source, BitmapBytes):
        bits = source.width * source.height * source.depth
        if bits % 8:
            raise ValueError("bitmap source must occupy a whole number of bytes")
        number("file-size", "File size", bits // 8, "bytes")
        steps = ["Multiply width by height and bits per pixel.", "Divide bits by eight to obtain bytes."]
    elif isinstance(source, SoundBytes):
        bits = source.sample_rate * source.sample_depth * source.duration * source.channels
        if bits % 8:
            raise ValueError("sound source must occupy a whole number of bytes")
        number("file-size", "File size", bits // 8, "bytes")
        steps = ["Multiply sample rate, duration, depth and channel count.", "Convert bits to bytes by dividing by eight."]
    elif isinstance(source, UnsignedSum):
        total = source.left + source.right
        text("8-bit-result", "8-bit result", f"{total % 256:08b}")
        text("overflow", "Overflow", "yes" if total > 255 else "no")
        steps = ["Add corresponding binary place values with carries.", "Retain the low eight bits and check for a carry beyond the unsigned range."]
    elif isinstance(source, FloatingEncode):
        value = Decimal(source.value)
        if not value.is_finite() or value <= 0:
            raise ValueError("floating template requires a finite positive value")
        exponent = 0
        mantissa = value
        while mantissa >= 1:
            mantissa /= 2
            exponent += 1
        while mantissa < Decimal("0.5"):
            mantissa *= 2
            exponent -= 1
        scaled = mantissa * (2 ** (source.mantissa_bits - 1))
        if scaled != scaled.to_integral_value() or not -(2 ** (source.exponent_bits - 1)) <= exponent < 2 ** (source.exponent_bits - 1):
            raise ValueError("floating source is not exactly representable")
        bits = f"{int(scaled):0{source.mantissa_bits}b}" + f"{exponent % (2 ** source.exponent_bits):0{source.exponent_bits}b}"
        text("representation", "Floating representation", bits)
        steps = ["Normalise the positive binary fraction to a leading 01 mantissa.", "Encode the exact signed mantissa and two's-complement exponent in the declared widths."]
    else:
        operation = {
            "A OR B": lambda a, b: a or b,
            "(NOT A) AND B": lambda a, b: (not a) and b,
            "A XOR B": lambda a, b: a != b,
        }[source.expression]
        for index, inputs in enumerate(source.inputs, 1):
            if set(inputs) != {"A", "B"}:
                raise ValueError("Boolean input rows must bind every variable")
            number(f"case-{index}", f"Case {index} output", int(operation(inputs["A"], inputs["B"])))
        steps = ["Apply operator precedence to each separately supplied input case; equal results are permitted."]
    result = numeric_result(numbers, outputs, steps) if outputs else {
        "answer": {}, "mark_points": {}, "numeric_results": {}, "numeric_checks": [],
        "steps": steps, "evidence_ids": [],
    }
    for check in texts:
        result["answer"][check.role] = result["mark_points"][check.role] = check.value
    result["text_checks"] = [check.model_dump(mode="json") for check in texts]
    return result
