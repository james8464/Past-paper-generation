from __future__ import annotations

import random
import secrets
from collections import Counter

from cspapergen.models import PaperBlueprint, Syllabus
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
