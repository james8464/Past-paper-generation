from __future__ import annotations

import random
import secrets
from collections import Counter

from cspapergen.models import PaperBlueprint, Syllabus
from cspapergen.question_bank import QUESTION_STYLES, build_question, styles_for_total

QUESTION_TOTALS = [8, 8, 9, 9, 10, 8, 8, 10, 8, 10, 12]


def build_paper2_blueprint(syllabus: Syllabus, seed: int | None = None) -> PaperBlueprint:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    totals = list(QUESTION_TOTALS)
    rng.shuffle(totals)
    if totals[-1] != 12:
        totals.remove(12)
        totals.append(12)

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
