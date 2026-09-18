"""Source-reading repairs; not a generic selected-response demand policy."""

from __future__ import annotations


def selection_contract(part, source):
    kind = source.kind
    prompt = part.prompt
    answers = None
    reasons = []
    if kind == "market_share_bar_chart":
        ranked = sorted(source.values, reverse=True)
        answers = [f"{value:.1f}%" for value in ranked[:4]]
        reasons = ["This is a smaller firm's share, not the largest share."] * 3
    elif kind == "current_account_line_chart":
        if not source.values or not all(value < 0 for value in source.values):
            raise ValueError("current-account source must show a deficit in every year")
        narrowing_index = next(
            (
                index
                for index in range(1, len(source.values))
                if source.values[index] > source.values[index - 1]
            ),
            None,
        )
        if narrowing_index is None:
            raise ValueError("current-account source needs a non-widening interval")
        answers = [
            "The current account was in deficit in every year shown",
            "The current account deficit widened in every year shown",
            "The current account was in surplus in the final year shown",
            "The current account balance was positive in every year shown",
        ]
        reasons = [
            "The deficit narrows between "
            f"{source.labels[narrowing_index - 1]} and {source.labels[narrowing_index]}; "
            "the line moves towards zero rather than widening throughout.",
            f"The final reading is {source.values[-1]}, which is below zero and therefore a deficit.",
            "Every plotted reading is below zero, so the balance is never positive.",
        ]
    elif kind == "opportunity_cost_ppc_table":
        # Read the transposed table by the requested capital-output labels.
        initial = next(i for i, c in enumerate(source.rows[1]) if c.number == 20)
        final = next(i for i, c in enumerate(source.rows[1]) if c.number == 40)
        cost = source.cell(0, initial, "units") - source.cell(0, final, "units")
        answers = [
            f"{cost:f} consumer goods",
            "20 consumer goods",
            "40 consumer goods",
            "85 consumer goods",
        ]
        reasons = [
            "This uses the capital-goods increase instead of consumer goods forgone.",
            "This uses final capital output instead of the opportunity cost.",
            "This is initial consumer output, not its reduction.",
        ]
    elif kind == "investment_line_chart":
        first, final = source.values[3], source.values[6]
        answers = [
            f"{first - final:.1f} percentage points",
            f"{(first - final) / first * 100:.1f} percentage points",
            f"{final:.1f} percentage points",
            f"{final - first:.1f} percentage points",
        ]
        prompt = f"What is the fall in investment as a share of GDP from {source.labels[3]} to {source.labels[6]}, in percentage points?"
        reasons = [
            "This is the relative percentage fall, not the percentage-point difference.",
            "This is the final investment share, not the fall.",
            "The requested fall is a positive size, not the signed final-minus-initial change.",
        ]
    elif kind == "business_objective_context":
        prompt = "For the firm with a downward-sloping demand curve, which one of the following conditions identifies unconstrained revenue maximisation?"
        answers = ["MR = 0", "MC = MR", "AC = AR", "MC = AC"]
        reasons = [
            "MC = MR identifies profit maximisation, not revenue maximisation.",
            "AC = AR identifies normal profit, not maximum revenue.",
            "MC = AC identifies minimum average cost, not maximum revenue.",
        ]
    elif kind == "xed_context":
        prompt = "Goods A and B have positive cross elasticity of demand. If the price of B falls, what is the likely effect on demand for A, other things equal?"
        answers = [
            "Demand for A shifts left",
            "Demand for A shifts right",
            "Supply of A shifts left",
            "Supply of A shifts right",
        ]
        reasons = [
            "A cheaper substitute attracts buyers away from A, not towards it.",
            "The change affects demand for A rather than A's production costs.",
            "The change affects demand for A rather than A's production costs.",
        ]
    elif kind == "imperfect_information_context":
        prompt = (
            "Which feature explains the information failure described in the source?"
        )
        answers = [
            "Buyers cannot assess quality accurately before purchase",
            "Buyers know quality but prefer cheaper products",
            "All buyers and sellers possess the same complete quality information",
            "Production uses scarce resources",
        ]
        reasons = [
            "An informed preference is not itself information failure.",
            "Complete shared information removes this particular asymmetry.",
            "Scarcity does not explain buyers' missing quality information.",
        ]
    elif kind == "minimum_wage_context":
        prompt = "Which change is most likely to shift labour supply away from this occupation, other things equal?"
        answers = [
            "Higher wages in competing occupations",
            "More suitably trained migrants enter this occupation",
            "More workers qualify for this occupation",
            "More flexible hours make this occupation attractive",
        ]
        reasons = [
            "Additional qualified workers increase this occupation's labour supply.",
            "More qualified workers increase labour supply.",
            "Greater non-wage attractiveness increases labour supply.",
        ]
    elif kind == "contestability_barrier_table":
        prompt = (
            "Based on the table, which change directly reduces the barrier currently "
            "classified as High?"
        )
        answers = [
            "Lower sunk costs",
            "Higher legal barriers to entry",
            "Exclusive access to key inputs",
            "Stronger brand loyalty for incumbents",
        ]
        reasons = [
            "The table classifies legal barriers as Low, and raising them increases rather than reduces a barrier.",
            "Exclusive input access creates a barrier but is not the High row identified in the table.",
            "Brand loyalty creates a barrier but is not the High row identified in the table.",
        ]
    elif kind == "multiplier_context":
        prompt = "Which phase of the economic cycle is associated with output near a peak and strong demand pressure?"
        answers = ["Boom", "Trough", "Recession", "Early recovery from a trough"]
        reasons = [
            "A trough is a low point in output.",
            "A recession involves falling output, not a peak.",
            "Early recovery starts from depressed output rather than the cycle's peak.",
        ]
    elif kind == "unemployment_rate_bar_chart":
        prompt = "Suppose unemployment rises in one of the economies shown. Which consequence is most likely, other things equal?"
    if answers is None:
        return prompt, part.options, part.mark_scheme
    if len(set(answers)) != 4:
        raise ValueError(f"{kind} has colliding source-derived options")
    wrong = iter(zip(answers[1:], reasons, strict=True))
    options, rejected = [], []
    for option in part.options:
        if option.label == part.correct_option:
            answer = answers[0]
        else:
            answer, reason = next(wrong)
            rejected.append(f"Reject {option.label}: {reason}")
        options.append(option.model_copy(update={"text": answer}))
    return (
        prompt,
        options,
        [
            f"The only correct answer is {part.correct_option}: {answers[0]}",
            *rejected,
            (
                "Do not award a mark for any other option."
                if kind == "current_account_line_chart"
                else "Award one mark for the keyed response only; explanations do not create extra credit."
            ),
        ],
    )
