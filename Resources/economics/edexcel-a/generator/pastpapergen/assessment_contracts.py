"""One instance supplies the paper's source, credit, solver and review views."""

from __future__ import annotations

import random
import re
from decimal import Decimal

from Backend.Core.subjects.economics_contracts import (
    ECONOMICS_CONTRACT_VERSION,
    EconomicsSource,
    SourceCell,
    calculation,
    calculation_label,
    calculation_prompt,
    calculation_working,
)
from pastpapergen.credit_contracts import (
    TOPIC_CHAINS,
    drawing_contract,
    extended_credit,
    short_credit,
)
from pastpapergen.extended_scenarios import concrete_fallback
from pastpapergen.selection_contracts import selection_contract
from pastpapergen.stimulus_data import LINE_CHART_SERIES, TABLE_ROWS, line_chart_data


def source_instance(question, seed: int) -> EconomicsSource:
    kind = question.stimulus_kind
    source = EconomicsSource(
        source_id=f"{seed}-{question.section}-{question.number}",
        kind=kind,
        context=question.source_text,
    )
    if kind == "context_extract" and question.parts and question.topic_id != "1.2.1":
        source = source.model_copy(
            update={
                "context": "In this illustrative scenario, "
                + TOPIC_CHAINS[question.topic_id][0][:1].lower()
                + TOPIC_CHAINS[question.topic_id][0][1:]
            }
        )
    if not question.parts and question.number.startswith(("1(", "2(")):
        patterns = {
            "Price change": (r"prices .*?increased by (\d+(?:\.\d+)?)%", "%"),
            "Quantity supplied change": (
                r"quantity supplied increased by (\d+(?:\.\d+)?)%",
                "%",
            ),
            "Capital spending change": (
                r"increased capital spending by (\d+(?:\.\d+)?)%",
                "%",
            ),
            "Unit input cost reduction": (
                r"reduced unit input costs by (\d+(?:\.\d+)?)%",
                "%",
            ),
            "Market output (million doses)": (
                r"market produced (\d+) million doses",
                "units",
            ),
            "Socially efficient output (million doses)": (
                r"was (\d+) million doses",
                "units",
            ),
            "External marginal cost per dose": (
                r"health cost of £(\d+(?:\.\d+)?) per dose",
                "GBP",
            ),
            "Vacancy growth": (r"vacancies .*?rose by (\d+(?:\.\d+)?)%", "%"),
            "Median vacancy duration (weeks)": (
                r"median vacancy duration of (\d+) weeks",
                "1",
            ),
            "Pay growth": (r"increased average pay by (\d+(?:\.\d+)?)%", "%"),
            "Annual staff turnover": (r"annual staff turnover reached (\d+(?:\.\d+)?)%", "%"),
            "Later-period price change": (r"prices changed by (\d+(?:\.\d+)?)%", "%"),
            "Sector output change": (
                r"Output in the sector changed by (\d+(?:\.\d+)?)%",
                "%",
            ),
            "Planned investment change": (
                r"planned investment by (\d+(?:\.\d+)?)%",
                "%",
            ),
            "International price change": (
                r"international prices moved by (\d+(?:\.\d+)?)%",
                "%",
            ),
        }
        givens = {
            label: SourceCell(
                number=Decimal(match.group(1)),
                unit=unit,
            )
            for label, (pattern, unit) in patterns.items()
            if (match := re.search(pattern, question.source_text))
        }
        rows = (
            [
                [SourceCell(text="Indicator"), SourceCell(text="Value")],
                *[[SourceCell(text=name), cell] for name, cell in givens.items()],
            ]
            if givens and "Figure" in question.source_reference
            else []
        )
        return source.model_copy(update={"givens": givens, "rows": rows})
    if kind in {"pes_data_table", "elasticity_data_table"}:
        name, value = (
            ("quantity_supply_change", "3.6")
            if kind == "pes_data_table"
            else ("price_change", "-5")
        )
        source = source.model_copy(
            update={"givens": {name: SourceCell(number=Decimal(value), unit="%")}}
        )
    if kind == "income_tax_schedule_table":
        source = source.model_copy(
            update={
                "givens": {
                    "Additional taxable income": SourceCell(
                        number=Decimal("200"), unit="GBP"
                    )
                }
            }
        )
    if kind in TABLE_ROWS:
        rows = []
        for row in TABLE_ROWS[kind]:
            cells = []
            for column, text in enumerate(row):
                token = (
                    text.replace("£", "")
                    .replace("%", "")
                    .replace(" ", "")
                    .replace(",", "")
                )
                if re.fullmatch(r"[+\-]?\d+(?:\.\d+)?", token):
                    unit = "GBP" if "£" in text else "%" if "%" in text else "1"
                    if (
                        kind in {"data_table", "inflation_index_table"}
                        and column > 0
                        and "%" not in text
                    ):
                        unit = "index"
                    if kind == "opportunity_cost_ppc_table" or (
                        kind == "shutdown_cost_table" and column == 0
                    ):
                        unit = "units"
                    cells.append(SourceCell(number=Decimal(token), unit=unit))
                else:
                    cells.append(SourceCell(text=text))
            rows.append(cells)
        return source.model_copy(update={"rows": rows})
    if kind in {*LINE_CHART_SERIES, "line_graph", "index_number_chart"}:
        y, x, values = line_chart_data(kind)
        values = [Decimal(str(v)) for v in values]
        if kind in {
            "household_savings_line_chart",
            "current_account_line_chart",
            "terms_of_trade_index_chart",
            "exchange_rate_index_chart",
        }:
            rng = random.Random(f"{seed}:{question.number}:{kind}")
            offset = Decimal(rng.choice([1, 2, 3, 4, 5])) / (10 if "%" in y else 1)
            values = [
                v + offset if kind != "current_account_line_chart" else v - offset
                for v in values
            ]
            # Change extrema/endpoint differences too, not just the origin.
            position = (
                values.index(max(values))
                if kind == "household_savings_line_chart"
                else len(values) - 1
            )
            values[position] += (
                offset if kind != "current_account_line_chart" else -offset
            )
        return source.model_copy(
            update={
                "values": values,
                "y_label": y,
                "x_label": x,
                "unit": "%" if "%" in y else "index" if y == "Index" else "1",
                "labels": [f"{x} {i + 1}" for i in range(len(values))],
            }
        )
    if kind in {
        "bar_chart",
        "market_share_bar_chart",
        "gdp_growth_bar_chart",
        "unemployment_rate_bar_chart",
    }:
        values, labels, axis = {
            "market_share_bar_chart": (
                [26.6, 19.5, 12.7, 11.7, 10.9],
                ["Firm A", "Firm B", "Firm C", "Firm D", "Firm E"],
                "Firm",
            ),
            "gdp_growth_bar_chart": (
                [0.4, 0.1, -0.1, 0.1, 0.1],
                [f"Q{i}" for i in range(1, 6)],
                "Quarter",
            ),
            "unemployment_rate_bar_chart": (
                [3.9, 5.8, 7.1, 4.6],
                ["Economy A", "Economy B", "Economy C", "Economy D"],
                "Economy",
            ),
            "bar_chart": (
                [52, 80, 38, 96],
                ["Firm A", "Firm B", "Firm C", "Firm D"],
                "Firm",
            ),
        }[kind]
        return source.model_copy(
            update={
                "values": [Decimal(str(v)) for v in values],
                "labels": labels,
                "unit": "%",
                "y_label": "%",
                "x_label": axis,
            }
        )
    if kind == "payoff_matrix":
        rows = [
            ["Firm A / Firm B", "High price", "Low price"],
            ["High price", "8, 8", "4, 10"],
            ["Low price", "10, 4", "6, 6"],
        ]
        return source.model_copy(
            update={
                "context": source.context
                + " Each cell lists Firm A's payoff, then Firm B's payoff.",
                "rows": [[SourceCell(text=cell) for cell in row] for row in rows],
            }
        )
    return source


def objective_budget(marks: int, command: str) -> dict[str, int]:
    if command == "mcq":
        return {
            "AO2": 1
        }  # generated contextual selection, not claimed official MCQ metadata
    if command == "calculate":
        return {"AO2": 2} if marks == 2 else {"AO1": 2, "AO2": 2}
    if command == "draw":
        return {"AO1": 2, "AO2": 2}
    return {
        2: {"AO1": 1, "AO3": 1},
        4: {"AO1": 2, "AO2": 1, "AO3": 1},
        5: {"AO1": 2, "AO2": 2, "AO3": 1},
        8: {"AO1": 2, "AO2": 2, "AO3": 2, "AO4": 2},
        10: {"AO1": 2, "AO2": 2, "AO3": 2, "AO4": 4},
        12: {"AO1": 2, "AO2": 2, "AO3": 4, "AO4": 4},
        15: {"AO1": 3, "AO2": 3, "AO3": 3, "AO4": 6},
        25: {"AO1": 4, "AO2": 4, "AO3": 8, "AO4": 9},
    }[marks]


def bind_question(question, seed: int):
    question = concrete_fallback(question)
    if not question.parts and question.number.startswith(("1(", "2(")):
        question = question.model_copy(
            update={
                "source_title": "Fictional regional economy: "
                + question.source_title
                + " and related markets"
            }
        )
    source = source_instance(question, seed)
    updates = {"source_instance": source, "source_text": source.context}
    if question.parts:
        parts = []
        for part in question.parts:
            budget = objective_budget(part.marks, part.command_word)
            scheme = part.mark_scheme
            prompt = part.prompt
            options = part.options
            if part.command_word == "calculate":
                result = calculation(source, part.marks)
                _role, answer = next(iter(result["answer"].items()))
                prompt = calculation_prompt(source, part.marks)
                scheme = [
                    f"{calculation_label(source, part.marks)}: {answer}",
                    f"Full {part.marks} marks for the correct final answer with its unit.",
                    f"Working: {calculation_working(source, part.marks)}",
                    f"Method: {result['steps'][0]}",
                ]
                if part.marks == 2:
                    scheme.append(
                        "If the final answer is incorrect, award 1 AO2 mark for the correct source substitution and operation; no credit for an unrelated operation."
                    )
                else:
                    scheme.append(
                        "If the final answer is incorrect: AO1, up to 2 marks for identifying the appropriate measure and method; AO2, 1 mark for correct source substitution. The remaining AO2 mark requires the correct final answer. Do not add these marks to full-answer credit."
                    )
            elif (
                part.command_word == "mcq"
                and source.kind == "household_savings_line_chart"
            ):
                peak = source.labels[source.values.index(max(source.values))]
                near = sorted(
                    range(len(source.values)),
                    key=lambda i: source.values[i],
                    reverse=True,
                )[1:4]
                distractors = iter(source.labels[i] for i in near)
                options = [
                    o.model_copy(
                        update={
                            "text": f"The saving rate reached its maximum in {peak if o.label == part.correct_option else next(distractors)}"
                        }
                    )
                    for o in options
                ]
                prompt = "Which statement correctly identifies the quarter with the highest saving rate?"
                scheme = [
                    f"The only correct answer is {part.correct_option}: "
                    + next(o.text for o in options if o.label == part.correct_option),
                    "Do not award a mark for any other option.",
                ]
                scheme.extend(
                    f"Reject {o.label}: the rate in {o.text.rsplit(' in ', 1)[1]} is below the maximum {max(source.values)}% in {peak}."
                    for o in options
                    if o.label != part.correct_option
                )
            elif (
                part.command_word == "mcq"
                and source.kind == "terms_of_trade_index_chart"
            ):
                answer = next(iter(calculation(source, 2)["answer"].values()))
                first, final = source.values[0], source.values[-1]
                wrong = [
                    final - first,
                    (final - first) / final * 100,
                    final / first * 100,
                ]
                wrong_text = [f"{value:.1f}%" for value in wrong]
                if len(set([answer, *wrong_text])) != 4:
                    raise ValueError(
                        "terms-of-trade distractors collide after rounding"
                    )
                distractors = iter(wrong_text)
                options = [
                    o.model_copy(
                        update={
                            "text": answer
                            if o.label == part.correct_option
                            else next(distractors)
                        }
                    )
                    for o in options
                ]
                prompt = f"What is the percentage increase in the terms-of-trade index from {source.labels[0]} to {source.labels[-1]}? Give your answer to 1 decimal place."
                scheme = [
                    f"The only correct answer is {part.correct_option}: {answer}",
                    "Do not award a mark for any other option.",
                ]
                reasons = iter(
                    [
                        "reports the index-point difference as a percentage",
                        "uses the final index as the denominator",
                        "reports the final-to-initial ratio rather than the percentage increase",
                    ]
                )
                scheme.extend(
                    f"Reject {o.label}: it {next(reasons)}."
                    for o in options
                    if o.label != part.correct_option
                )
            elif (
                source.kind == "contestability_barrier_table"
                and part.command_word == "explain"
            ):
                scheme = [
                    "AO1 (2 marks): Identify sunk entry costs as a barrier and explain that these cannot be recovered on exit.",
                    "AO2 (1 mark): Apply the high sunk costs in the table to a potential entrant's risk.",
                    "AO3 (1 mark): Explain that the risk of unrecoverable losses deters entry, weakening the competitive threat to incumbent firms.",
                    "Accept a developed alternative using the table's switching-cost or legal-barrier evidence; award the same four-mark budget, not extra marks.",
                ]
            elif (
                source.kind == "elasticity_data_table"
                and part.command_word == "explain"
            ):
                prompt = (
                    "Using the YED figures in the table, explain why an increase in "
                    "consumer income is likely to raise demand for one of the goods shown."
                )
                scheme = [
                    "AO1 (2 marks): Define income elasticity of demand as the responsiveness of demand to a change in income, and explain that a positive YED identifies a normal good.",
                    "AO2 (1 mark): Apply one positive YED from the table: Bus travel (0.2), Cinema (1.8) or Fuel (0.1).",
                    "AO3 (1 mark): Higher income increases demand for the selected normal good, so its demand curve shifts right; ceteris paribus this raises equilibrium price and quantity.",
                    "Accept any one correctly identified positive-YED good and its developed demand link; do not award extra credit for naming more than one good.",
                ]
            elif part.command_word == "draw":
                prompt, scheme = drawing_contract(question, part)
            elif part.command_word != "mcq":
                scheme = short_credit(question, part, source)
                if source.kind == "investment_line_chart":
                    prompt = f"Using {source.labels[3]} and {source.labels[6]}, explain one likely effect of the fall in investment on aggregate demand."
                if source.kind == "unemployment_rate_bar_chart":
                    prompt = "Suppose unemployment rises in one of the economies shown. Explain one likely macroeconomic effect."
            else:
                prompt, options, scheme = selection_contract(part, source)
            contract = {
                "version": ECONOMICS_CONTRACT_VERSION,
                "source_fingerprint": source.fingerprint(),
                "task": part.command_word,
                "marks": part.marks,
                "assessment_objectives": budget,
                "objective_basis": "declared generated task design; published MCQ allocation unknown"
                if options
                else "task-specific reference style",
                "scheme_mode": "points",
                "credit": scheme,
                "published_scheme": scheme,
            }
            parts.append(
                part.model_copy(
                    update={
                        "prompt": prompt,
                        "options": options,
                        "assessment_objectives": budget,
                        "assessment_contract": contract,
                        "mark_breakdown": ", ".join(
                            f"{key} {value}" for key, value in budget.items()
                        ),
                        "mark_scheme": scheme,
                        "indicative_content": scheme,
                    }
                )
            )
        updates.update(
            parts=parts, mark_scheme=[], indicative_content=[], mark_breakdown=""
        )
    else:
        budget = objective_budget(question.marks, question.command_word)
        scheme, credit = extended_credit(question, budget, source)
        updates.update(
            assessment_objectives=budget,
            assessment_contract={
                "version": ECONOMICS_CONTRACT_VERSION,
                "source_fingerprint": source.fingerprint(),
                "marks": question.marks,
                "assessment_objectives": budget,
                **credit,
                "published_scheme": scheme,
            },
            mark_scheme=scheme,
            indicative_content=scheme,
            scheme_mode=credit["scheme_mode"],
            mark_breakdown=", ".join(f"{key} {value}" for key, value in budget.items()),
        )
        if question.topic_id == "3.1" and question.marks == 5:
            updates["prompt"] = (
                "With reference to Extract A, explain one way in which business expansion "
                "may affect a firm's average costs and, consequently, its consumers."
            )
    return question.model_copy(update=updates)


def validate_assessment_contract(question, item):
    if question.source_instance is None:
        return  # Legacy in-memory callers; persisted generation has a new version.
    contract = item.assessment_contract
    expected = {
        "version": ECONOMICS_CONTRACT_VERSION,
        "source_fingerprint": question.source_instance.fingerprint(),
        "marks": item.marks,
        "assessment_objectives": item.assessment_objectives,
        "published_scheme": item.mark_scheme,
    }
    if any(contract.get(key) != value for key, value in expected.items()):
        raise ValueError("Edexcel source, credit or AO contract changed")
    if sum(item.assessment_objectives.values()) != item.marks or not contract.get(
        "credit"
    ):
        raise ValueError("Edexcel assessment contract has an incomplete tariff")
    if item.mark_breakdown != ", ".join(
        f"{key} {value}" for key, value in item.assessment_objectives.items()
    ):
        raise ValueError("Edexcel printed allocation differs from its credit contract")
