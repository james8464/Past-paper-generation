from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelRow:
    level: int
    mark_range: str
    description: str


_ZERO = LevelRow(0, "0", "No creditworthy material.")


def level_rows(marks: int) -> tuple[LevelRow, ...]:
    """Return the AQA Economics response bands for a supported tariff."""
    if marks == 9:
        return (
            LevelRow(
                3,
                "7–9",
                "A focused, contextual explanation with a clear analytical chain and an accurate, appropriately used diagram.",
            ),
            LevelRow(
                2,
                "4–6",
                "A relevant explanation with reasonable application and analysis; the diagram or chain may be incomplete.",
            ),
            LevelRow(
                1,
                "1–3",
                "A brief response containing limited relevant knowledge, application or diagram use.",
            ),
            _ZERO,
        )
    if marks == 10:
        return (
            LevelRow(
                3,
                "8–10",
                "A well-organised assessment using several relevant data comparisons, their limitations and a supported conclusion.",
            ),
            LevelRow(
                2,
                "4–7",
                "A reasonable assessment using relevant data, with some recognition of limitations or a partly supported conclusion.",
            ),
            LevelRow(
                1,
                "1–3",
                "A limited response with isolated data use or unsupported assertions.",
            ),
            _ZERO,
        )
    if marks == 15:
        return (
            LevelRow(
                3,
                "11–15",
                "A well-organised answer with accurate knowledge, effective application and clear, developed analytical chains.",
            ),
            LevelRow(
                2,
                "6–10",
                "A relevant answer with reasonable knowledge, application and analysis, though development may be uneven.",
            ),
            LevelRow(
                1,
                "1–5",
                "A limited answer with partial knowledge and short or confused analytical links.",
            ),
            _ZERO,
        )
    if marks == 25:
        return (
            LevelRow(
                5,
                "21–25",
                "Precise, sustained and contextual analysis with supported evaluation throughout and a fully justified conclusion.",
            ),
            LevelRow(
                4,
                "16–20",
                "Sound, focused analysis with relevant supported evaluation and a reasoned conclusion.",
            ),
            LevelRow(
                3,
                "11–15",
                "Reasonable analysis with some evaluation, but support, focus or development is uneven.",
            ),
            LevelRow(
                2,
                "6–10",
                "Limited application and analysis with weak or largely unsupported evaluation.",
            ),
            LevelRow(
                1,
                "1–5",
                "Fragmentary knowledge with little development and no effective evaluation.",
            ),
            _ZERO,
        )
    raise ValueError(f"unsupported AQA Economics level tariff: {marks}")


def level_guidance(marks: int) -> list[str]:
    return [
        "Levels-based marking",
        *[
            f"Level {row.level} ({row.mark_range}): {row.description}"
            for row in level_rows(marks)
        ],
    ]
