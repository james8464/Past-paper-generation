from argparse import Namespace

import pytest


def _pin_v17_generation(monkeypatch, runtime):
    generate = runtime.generate_assessment
    monkeypatch.setattr(
        runtime,
        "generate_assessment",
        lambda **kwargs: generate(**{**kwargs, "contract_authoring_version": "v17"}),
    )


def _pin_v19_generation(monkeypatch, runtime):
    generate = runtime.generate_assessment
    monkeypatch.setattr(
        runtime,
        "generate_assessment",
        lambda **kwargs: generate(**{**kwargs, "contract_authoring_version": "v19"}),
    )


def _pin_v20_generation(monkeypatch, runtime):
    generate = runtime.generate_assessment
    monkeypatch.setattr(
        runtime,
        "generate_assessment",
        lambda **kwargs: generate(**{**kwargs, "contract_authoring_version": "v20"}),
    )


@pytest.mark.parametrize("large_print", [False, True])
def test_v21_audit_pdf_stages_work_tables_and_uses_explicit_dispatch(
    tmp_path, large_print
):
    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.database_audit_contract import (
        build_database_audit_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledDatabaseAuditFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledDatabaseAuditFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v21",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_database_audit_contract(270100)
    assert (
        runtime.database_pdf_contract_version(package["identity"]["prompt_version"])
        == "v21"
    )
    for correction in (False, True):
        path = tmp_path / ("correction.pdf" if correction else "subject.pdf")
        render_assessment(
            path, exercises, correction=correction, large_print=large_print
        )
        runtime.validate_database_audit_pdf(
            path, contract, correction=correction, exercise=exercises[1]
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            lower, upper = (
                (21, 28)
                if correction and large_print
                else (15, 21)
                if correction
                else (10, 14)
                if large_print
                else (8, 11)
            )
            assert lower <= len(pdf) <= upper
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            raw = "\n".join(pages)
            for title, task_id, previous_id in (
                ("Table de travail — jointures (2c–2e)", "2c", "2b"),
                ("Table de travail — états (2g–2h)", "2g", "2f"),
                ("Table de travail — fonction (2i)", "2h", "2g"),
            ):
                assert raw.index(f"\n{previous_id}.") < raw.index(title)
                assert raw.index(title) < raw.index(f"\n{task_id}.")


def test_v21_pdf_rejects_mutated_incident_and_working_tables(tmp_path):
    from Backend.Core.france import runtime
    from Backend.Core.france.database_audit_contract import (
        build_database_audit_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledDatabaseAuditFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledDatabaseAuditFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v21",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    for material_id, changed_cell in (("incident", "901"), ("audit_jointure", "102")):
        materials = []
        for material in exercises[1].materials:
            if material.id == material_id:
                rows = [list(row) for row in material.rows]
                rows[0][0] = changed_cell
                material = material.model_copy(
                    update={"rows": tuple(tuple(row) for row in rows)}
                )
            materials.append(material)
        altered = exercises[1].model_copy(update={"materials": materials})
        path = tmp_path / f"{material_id}.pdf"
        render_assessment(path, [exercises[0], altered, exercises[2]], correction=False)
        with pytest.raises(ValueError, match="differs from contract"):
            runtime.validate_database_audit_pdf(
                path,
                build_database_audit_contract(270100),
                correction=False,
                exercise=altered,
            )


def test_v21_pdf_rejects_missing_shifted_or_leaked_material(tmp_path, monkeypatch):
    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.database_audit_contract import (
        build_database_audit_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import ControlledDatabaseAuditFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledDatabaseAuditFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v21",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_database_audit_contract(270100)
    path = tmp_path / "subject.pdf"
    render_assessment(path, exercises, correction=False)
    with pymupdf.open(path) as pdf:
        pages = [page.get_text() for page in pdf]

    class TextDocument:
        def __init__(self, text):
            self.pages = text if isinstance(text, list) else [text]

        def __enter__(self):
            return [
                type("Page", (), {"get_text": lambda self, value=text: value})()
                for text in self.pages
            ]

        def __exit__(self, *_):
            return False

    original = "\n".join(pages)
    title = "Table de travail — états (2g–2h)"
    assert title in original
    faulty_sql = contract.to_dict()["faulty_sql"]
    faulty_python = contract.to_dict()["faulty_python"]
    assert faulty_sql in original and faulty_python in original
    mutants = (
        original.replace(title, "Table absente", 1),
        original.replace(title, "Table absente", 1) + "\n" + title,
        original + "\n" + " ".join(contract.to_dict()["correct_sql"].split()),
        original.replace(faulty_sql, "", 1) + "\n" + faulty_sql,
        original.replace(faulty_python, "", 1) + "\n" + faulty_python,
        original + "\nRéponse attendue",
        original + "\nBarème indicatif — question 2a",
        original + "\nS0, S1, S2 : 3, 4, 5",
        original + "\nincident.id_cat = categorie.id_cat",
    )
    for index, mutated in enumerate(mutants):
        with monkeypatch.context() as patch:
            patch.setattr(
                runtime.pymupdf, "open", lambda _, text=mutated: TextDocument(text)
            )
            try:
                runtime.validate_database_audit_pdf(
                    path, contract, correction=False, exercise=exercises[1]
                )
            except ValueError:
                continue
            pytest.fail(f"Subject mutation {index} passed the V21 PDF gate")
    correction_path = tmp_path / "correction.pdf"
    render_assessment(correction_path, exercises, correction=True)
    with pymupdf.open(correction_path) as pdf:
        correction_text = "\n".join(page.get_text() for page in pdf)
    changed = correction_text.replace(
        "Barème indicatif — question 2a", "Barème indicatif — question 2b", 1
    )
    assert changed != correction_text
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _: TextDocument(changed))
        with pytest.raises(ValueError, match="answer/rubric"):
            runtime.validate_database_audit_pdf(
                correction_path, contract, correction=True, exercise=exercises[1]
            )
    split_after_rubric = correction_text.index(
        "Barème indicatif — question 2a\n"
    ) + len("Barème indicatif — question 2a\n")
    with monkeypatch.context() as patch:
        patch.setattr(
            runtime.pymupdf,
            "open",
            lambda _: TextDocument(
                [
                    correction_text[:split_after_rubric],
                    correction_text[split_after_rubric:],
                ]
            ),
        )
        with pytest.raises(ValueError, match=r"credit.*separated"):
            runtime.validate_database_audit_pdf(
                correction_path, contract, correction=True, exercise=exercises[1]
            )
    question_2a = correction_text.index("\n2a.")
    answer_start = correction_text.index("Réponse attendue\n", question_2a) + len(
        "Réponse attendue\n"
    )
    answer_end = correction_text.index("Barème indicatif — question 2a", answer_start)
    answer_block = correction_text[answer_start:answer_end]
    reordered = correction_text.replace(answer_block, "", 1).replace(
        "Barème indicatif — question 2a\n",
        "Barème indicatif — question 2a\n" + answer_block,
        1,
    )
    assert reordered != correction_text
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _: TextDocument(reordered))
        with pytest.raises(ValueError, match=r"answer/rubric.*order"):
            runtime.validate_database_audit_pdf(
                correction_path, contract, correction=True, exercise=exercises[1]
            )


@pytest.mark.parametrize("large_print", [False, True])
def test_v20_runtime_stages_graph_and_tree_and_validates_pdf(
    tmp_path, monkeypatch, large_print
):
    import json

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.graph_resilience_contract import (
        build_graph_resilience_contract,
    )
    from Backend.Core.france.graph_tree_binding import graph_edge_manifest
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import (
        ControlledGraphResilienceFrenchClient,
        make_index,
    )

    index = tmp_path / "references.sqlite"
    make_index(index)
    _pin_v20_generation(monkeypatch, runtime)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledGraphResilienceFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v20"
    exercise = NSIExercise.model_validate(package["exercises"][0])
    contract = build_graph_resilience_contract(args.seed)
    for name, correction in (("sujet.pdf", False), ("corrige.pdf", True)):
        path = bundle / name
        runtime.validate_graph_resilience_pdf(
            path, contract, correction=correction, exercise=exercise
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )

        class ExtractedDocument:
            def __init__(self, values):
                self.values = values

            def __enter__(self):
                return [
                    type("Page", (), {"get_text": lambda _self, value=text: value})()
                    for text in self.values
                ]

            def __exit__(self, *_):
                return False

        facts = contract.to_dict()
        for source in (
            facts["debug_case"]["faulty_code"],
            facts["search_code"],
        ):
            assert sum(page.count(source) for page in pages) == 1
            shifted = [page.replace(source, "", 1) for page in pages]
            shifted[-1] += "\n" + source
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf,
                    "open",
                    lambda _, values=shifted: ExtractedDocument(values),
                )
                with pytest.raises(ValueError, match="source or working facts"):
                    runtime.validate_graph_resilience_pdf(
                        path, contract, correction=correction, exercise=exercise
                    )
        search_code = facts["search_code"]
        shifted = [page.replace(search_code, "", 1) for page in pages]
        first_question_page = next(
            index for index, page in enumerate(shifted) if "1a." in page
        )
        shifted[first_question_page] = shifted[first_question_page].replace(
            "1a.", "1a.\n" + search_code, 1
        )
        with monkeypatch.context() as patch:
            patch.setattr(
                runtime.pymupdf,
                "open",
                lambda _, values=shifted: ExtractedDocument(values),
            )
            with pytest.raises(ValueError, match="source or working facts"):
                runtime.validate_graph_resilience_pdf(
                    path, contract, correction=correction, exercise=exercise
                )
        flat = " ".join(" ".join(pages).split())
        assert " ".join(graph_edge_manifest(facts["graph"]).split()) in flat
        assert flat.index("Réseau pondéré des postes") < flat.index("1a.")
        assert flat.index("1g.") < flat.index("Arbre des identifiants — arbre")
        assert flat.index("Arbre des identifiants — arbre") < flat.index("1h.")
        assert ("La liaison fermée est exclue" in flat) == correction
        if correction:
            first_answer = exercise.questions[0].answer
            assert sum(page.count(first_answer) for page in pages) == 1
            shifted = [page.replace(first_answer, "", 1) for page in pages]
            for index, page in enumerate(shifted):
                if "1b." in page:
                    shifted[index] = page.replace("1b.", "1b. " + first_answer, 1)
                    break

            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf,
                    "open",
                    lambda _, values=shifted: ExtractedDocument(values),
                )
                with pytest.raises(ValueError, match="answer 1a"):
                    runtime.validate_graph_resilience_pdf(
                        path, contract, correction=True, exercise=exercise
                    )


@pytest.mark.parametrize("large_print", [False, True])
def test_v19_publication_prints_locked_database_reasoning_and_keeps_its_phases(
    tmp_path, monkeypatch, large_print
):
    import json
    import re

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.database_depth_contract import (
        build_database_depth_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import (
        ControlledDatabaseReasoningFrenchClient,
        make_index,
    )

    _pin_v19_generation(monkeypatch, runtime)

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledDatabaseReasoningFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v19"
    exercise = NSIExercise.model_validate(package["exercises"][1])
    contract = build_database_depth_contract(args.seed)
    assert (
        runtime.database_pdf_contract_version(package["identity"]["prompt_version"])
        == "v19"
    )
    for name, correction in (("sujet.pdf", False), ("corrige.pdf", True)):
        path = bundle / name
        runtime.validate_database_reasoning_pdf(
            path, contract, correction=correction, exercise=exercise
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            assert 8 <= len(pdf) <= (24 if large_print and correction else 19)
            flat = " ".join(" ".join(pages).split())
            for phase in ("Partie A", "Partie B", "Partie C"):
                assert phase in flat
            for question in exercise.questions:
                assert flat.count(" ".join(question.prompt.split())) == 1
                for credit in question.marking:
                    assert (credit.criterion in flat) == correction

        class ExtractedDocument:
            def __init__(self, values):
                self.values = values

            def __enter__(self):
                return [
                    type("Page", (), {"get_text": lambda _self, text=text: text})()
                    for text in self.values
                ]

            def __exit__(self, *_):
                return False

        if correction:
            swapped = [
                page.replace("Barème indicatif — question 2a", "SWAP-RUBRIC")
                .replace(
                    "Barème indicatif — question 2b", "Barème indicatif — question 2a"
                )
                .replace("SWAP-RUBRIC", "Barème indicatif — question 2b")
                for page in pages
            ]
            assert swapped != pages

            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf,
                    "open",
                    lambda _, values=swapped: ExtractedDocument(values),
                )
                with pytest.raises(ValueError, match=r"rubric|answer"):
                    runtime.validate_database_reasoning_pdf(
                        path, contract, correction=True, exercise=exercise
                    )
            first = exercise.questions[0].marking[0].criterion
            second = exercise.questions[1].marking[0].criterion

            def swap_credits(page, first_criterion, second_criterion):
                first_pattern = r"\s+".join(map(re.escape, first_criterion.split()))
                second_pattern = r"\s+".join(map(re.escape, second_criterion.split()))
                page = re.sub(first_pattern, "SWAP-CREDIT", page)
                page = re.sub(second_pattern, first_criterion, page)
                return page.replace("SWAP-CREDIT", second_criterion)

            swapped_credits = [swap_credits(page, first, second) for page in pages]
            assert swapped_credits != pages
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf,
                    "open",
                    lambda _, values=swapped_credits: ExtractedDocument(values),
                )
                runtime.validate_database_depth_contract_pdf(
                    path, contract, correction=True, exercise=exercise
                )
                with pytest.raises(ValueError, match=r"credit|rubric"):
                    runtime.validate_database_reasoning_pdf(
                        path, contract, correction=True, exercise=exercise
                    )
        else:
            leaked_result = (
                exercise.questions[2].answer.split(" ; ")[0].split(": ", 1)[1]
            )
            for leak in (
                leaked_result,
                "incident.id_cat = categorie.id_cat",
                "assert nombre_clos(incidents) == 2",
                "incident['statut'] == 'clos'",
                "2 incidents clos",
                contract.to_dict()["update_sql"],
            ):
                assert leak in " ".join(
                    question.answer for question in exercise.questions
                )
                assert " ".join(leak.split()) not in " ".join(" ".join(pages).split())
                leaked_pages = [*pages]
                leaked_pages[-1] += "\n" + leak + "\n"
                with monkeypatch.context() as patch:
                    patch.setattr(
                        runtime.pymupdf,
                        "open",
                        lambda _, values=leaked_pages: ExtractedDocument(values),
                    )
                    runtime.validate_database_depth_contract_pdf(
                        path, contract, correction=False, exercise=exercise
                    )
                    try:
                        runtime.validate_database_reasoning_pdf(
                            path, contract, correction=False, exercise=exercise
                        )
                    except ValueError as exc:
                        assert "leak" in str(exc) or "answer" in str(exc)
                    else:
                        pytest.fail(f"V19 subject accepted leaked answer value: {leak}")


@pytest.mark.parametrize("large_print", [False, True])
def test_v18_network_reasoning_pdf_requires_exact_printed_facts_and_roles(
    tmp_path, monkeypatch, large_print
):
    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.network_reasoning_contract import (
        build_network_reasoning_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import generate_assessment
    from Backend.Core.france.rendering import render_assessment
    from tests.test_nsi_pipeline import (
        ControlledNetworkReasoningFrenchClient,
        make_index,
    )

    index = tmp_path / "references.sqlite"
    make_index(index)
    package = generate_assessment(
        index_path=index,
        client=ControlledNetworkReasoningFrenchClient(),
        seed=270100,
        checkpoint=tmp_path / "checkpoint.json",
        contract_graph_tree=True,
        contract_authoring_version="v18",
    )
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    contract = build_network_reasoning_contract(270100)
    assert (
        runtime.network_pdf_contract_version(package["identity"]["prompt_version"])
        == "v18"
    )
    assert (
        runtime.database_pdf_contract_version(package["identity"]["prompt_version"])
        == "v2"
    )
    for correction in (False, True):
        path = tmp_path / ("correction.pdf" if correction else "subject.pdf")
        render_assessment(
            path, exercises, correction=correction, large_print=large_print
        )
        runtime.validate_network_reasoning_contract_pdf(
            path, contract, correction=correction, exercise=exercises[2]
        )
        with pymupdf.open(path) as pdf:
            pages = [page.get_text() for page in pdf]
            lower, upper = (
                (18, 25)
                if correction and large_print
                else (13, 18)
                if correction
                else (10, 15)
                if large_print
                else (8, 12)
            )
            assert lower <= len(pdf) <= upper
            assert all(
                0 <= word[0] <= word[2] <= page.rect.width
                and 0 <= word[1] <= word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            for title, task_id in (
                ("Tableau de travail Dijkstra avant et après la hausse", "3a"),
                ("États simultanés et reprise à compléter", "3e"),
                ("Situations de sécurité à analyser", "3i"),
            ):
                material_page = next(i for i, page in enumerate(pages) if title in page)
                question_page = next(
                    i for i, page in enumerate(pages) if f"{task_id}." in page
                )
                assert 0 <= question_page - material_page <= 1
            if correction:
                for exercise in exercises:
                    for question in exercise.questions:
                        question_pages = [
                            i
                            for i, page in enumerate(pages)
                            if f"{question.id}." in page
                        ]
                        rubric_pages = [
                            i
                            for i, page in enumerate(pages)
                            if f"Barème indicatif — question {question.id}" in page
                        ]
                        assert question_pages == rubric_pages, question.id

        class PageText:
            def __init__(self, value):
                self.value = value

            def get_text(self):
                return self.value

        class DocumentText:
            def __init__(self, values):
                self.values = values

            def __enter__(self):
                return [PageText(value) for value in self.values]

            def __exit__(self, *_):
                return False

        with monkeypatch.context() as patch:
            patch.setattr(
                runtime.pymupdf, "open", lambda _, values=pages: DocumentText(values)
            )
            original = pages[:]
            pages[:] = [page.replace("M2", "M4", 1) for page in original]
            with pytest.raises(ValueError):
                runtime.validate_network_reasoning_contract_pdf(
                    path, contract, correction=correction, exercise=exercises[2]
                )
            pages[:] = [
                page.replace(
                    "Central\nR1\n5\nCentral\nR2\n8",
                    "Central\nR1\n8\nCentral\nR2\n5",
                    1,
                )
                for page in original
            ]
            assert pages != original
            with pytest.raises(ValueError):
                runtime.validate_network_reasoning_contract_pdf(
                    path, contract, correction=correction, exercise=exercises[2]
                )
            pages[:] = [page.replace("3l.", "3k.", 1) for page in original]
            with pytest.raises(ValueError):
                runtime.validate_network_reasoning_contract_pdf(
                    path, contract, correction=correction, exercise=exercises[2]
                )
            pages[:] = original[:]
            pages[-1] += "\n3a."
            with pytest.raises(ValueError):
                runtime.validate_network_reasoning_contract_pdf(
                    path, contract, correction=correction, exercise=exercises[2]
                )
            if correction:
                pages[:] = [
                    page.replace(
                        "0,25 point\nAccorder pour les deux coûts directs",
                        "0,20 point\nAccorder pour les deux coûts directs",
                        1,
                    )
                    for page in original
                ]
                assert pages != original
                with pytest.raises(ValueError):
                    runtime.validate_network_reasoning_contract_pdf(
                        path, contract, correction=True, exercise=exercises[2]
                    )


def test_runtime_publishes_v21_even_if_caller_requests_older_contract(
    tmp_path, monkeypatch
):
    import json

    from Backend.Core.france import runtime
    from tests.test_nsi_pipeline import (
        ControlledDatabaseAuditFrenchClient,
        make_index,
    )

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledDatabaseAuditFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=False,
    )
    args.contract_authoring_version = "v17"  # Caller cannot downgrade new publication.
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v21"
    assert len(package["exercises"][2]["questions"]) == 12
    assert (bundle / "sujet.pdf").is_file()
    assert (bundle / "corrige.pdf").is_file()


@pytest.mark.parametrize("failure", [None, "render", "cancel"])
@pytest.mark.parametrize("large_print", [False, True])
def test_publication_is_complete_or_absent(tmp_path, monkeypatch, failure, large_print):
    import json
    from hashlib import sha256

    from Backend.Core.france import runtime
    from Backend.Core.france.pipeline import (
        generate_assessment as real_generate_assessment,
    )
    from tests.test_nsi_pipeline import ControlledNetworkFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    output = tmp_path / "output"
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(output),
        seed=5,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    monkeypatch.setattr(runtime, "model_identity", lambda *args: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "generate_assessment",
        lambda **kwargs: real_generate_assessment(
            **{**kwargs, "contract_authoring_version": "v14"}
        ),
    )
    monkeypatch.setattr(
        runtime, "FrenchOllamaClient", lambda **kwargs: ControlledNetworkFrenchClient()
    )
    if failure == "render":

        def broken(*args, **kwargs):
            raise ValueError("fixture rendering failure")

        monkeypatch.setattr(runtime, "render_assessment", broken)
    elif failure == "cancel":

        def cancelled(**kwargs):
            raise InterruptedError("fixture cancellation")

        monkeypatch.setattr(runtime, "generate_assessment", cancelled)
    assert (
        runtime.handle_generate_assessment(args)
        == {None: 0, "render": 1, "cancel": 130}[failure]
    )
    bundles = list(output.glob("nsi-*"))
    assert not list(output.glob(".nsi-*"))
    if failure:
        assert bundles == []
    else:
        assert len(bundles) == 1
        manifest = json.loads((bundles[0] / "manifest.json").read_text())
        for artifact in manifest["artifacts"].values():
            assert (
                sha256((bundles[0] / artifact["file"]).read_bytes()).hexdigest()
                == artifact["sha256"]
            )
        assert manifest["status"] == "unreviewed_draft"
        assert (
            manifest["reference_index_sha256"] == sha256(index.read_bytes()).hexdigest()
        )
        assert manifest["identity"]["prompt_version"] == "fr-nsi-written-2027-v14"
        import pymupdf

        package = json.loads((bundles[0] / "assessment.json").read_text())
        part_evidence = package["evidence"][0]["part_evidence"]
        assert (
            part_evidence["contract_sha256"]
            == manifest["identity"]["graph_tree_contract_sha256"]
        )
        from Backend.Core.france.database_contract import build_database_contract
        from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
        from Backend.Core.france.network_contract import build_network_contract
        from Backend.Core.france.nsi import NSIExercise
        from Backend.Core.france.runtime import (
            validate_contract_pdf,
            validate_database_contract_pdf,
            validate_network_contract_pdf,
        )

        contract = build_graph_tree_contract(args.seed, "1")
        exercise = NSIExercise.model_validate(package["exercises"][0])
        validate_contract_pdf(
            bundles[0] / "sujet.pdf", contract, correction=False, exercise=exercise
        )
        validate_contract_pdf(
            bundles[0] / "corrige.pdf", contract, correction=True, exercise=exercise
        )
        database_contract = build_database_contract(args.seed)
        database_exercise = NSIExercise.model_validate(package["exercises"][1])
        validate_database_contract_pdf(
            bundles[0] / "sujet.pdf",
            database_contract,
            correction=False,
            exercise=database_exercise,
        )
        validate_database_contract_pdf(
            bundles[0] / "corrige.pdf",
            database_contract,
            correction=True,
            exercise=database_exercise,
        )
        network_contract = build_network_contract(args.seed)
        network_exercise = NSIExercise.model_validate(package["exercises"][2])
        validate_network_contract_pdf(
            bundles[0] / "sujet.pdf",
            network_contract,
            correction=False,
            exercise=network_exercise,
        )
        validate_network_contract_pdf(
            bundles[0] / "corrige.pdf",
            network_contract,
            correction=True,
            exercise=network_exercise,
        )
        import copy

        altered = copy.deepcopy(package["exercises"][0])
        altered["questions"][0]["prompt"] = "Le graphe contient une arête A-F."
        with pytest.raises(ValueError):
            validate_contract_pdf(
                bundles[0] / "sujet.pdf",
                contract,
                correction=False,
                exercise=NSIExercise.model_validate(altered),
            )
        altered = copy.deepcopy(package["exercises"][0])
        altered["questions"][1]["marking"][0]["points"] = "0.25"
        altered["questions"][1]["marking"][1]["points"] = "0.75"
        with pytest.raises(ValueError):
            validate_contract_pdf(
                bundles[0] / "corrige.pdf",
                contract,
                correction=True,
                exercise=NSIExercise.model_validate(altered),
            )
        original_open = pymupdf.open

        class ExtractedPage:
            def __init__(self, content):
                self.content = content

            def get_text(self):
                return self.content

        class ExtractedDocument:
            def __init__(self, pages):
                self.pages = [ExtractedPage(page) for page in pages]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def __iter__(self):
                return iter(self.pages)

        def reject_tampered_extraction(role, before, after, *, correction):
            with original_open(bundles[0] / role) as pdf:
                pages = [page.get_text() for page in pdf]
            matching = [index for index, page in enumerate(pages) if before in page]
            assert len(matching) == 1
            pages[matching[0]] = pages[matching[0]].replace(before, after, 1)
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf, "open", lambda _path: ExtractedDocument(pages)
                )
                with pytest.raises(ValueError):
                    validate_contract_pdf(
                        bundles[0] / role,
                        contract,
                        correction=correction,
                        exercise=exercise,
                    )

        reject_tampered_extraction(
            "sujet.pdf",
            "Réseau pondéré des postes\n7\n",
            "Réseau pondéré des postes\n8\n",
            correction=False,
        )
        reject_tampered_extraction(
            "sujet.pdf",
            "Arbre des identifiants d'intervention — arbre\ncle\ngauche\ndroite\n78\n",
            "Arbre des identifiants d'intervention — arbre\ncle\ngauche\ndroite\n79\n",
            correction=False,
        )
        reject_tampered_extraction(
            "sujet.pdf",
            "Déterminez dans `reseau`",
            "Consigne manquante",
            correction=False,
        )
        reject_tampered_extraction(
            "sujet.pdf",
            "Déterminez dans `reseau`",
            "Déterminez dans `reseau` " + exercise.questions[0].answer,
            correction=False,
        )
        reject_tampered_extraction(
            "corrige.pdf",
            exercise.questions[1].marking[0].criterion,
            "Critère manquant.",
            correction=True,
        )

        def reject_tampered_database(role, before, after, *, correction):
            with original_open(bundles[0] / role) as pdf:
                pages = [page.get_text() for page in pdf]
            matching = [index for index, page in enumerate(pages) if before in page]
            assert len(matching) == 1
            pages[matching[0]] = pages[matching[0]].replace(before, after, 1)
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf, "open", lambda _path: ExtractedDocument(pages)
                )
                with pytest.raises(ValueError):
                    validate_database_contract_pdf(
                        bundles[0] / role,
                        database_contract,
                        correction=correction,
                        exercise=database_exercise,
                    )

        reject_tampered_database(
            "sujet.pdf",
            "101\n1\n2\nouvert\n",
            "101\n1\n2\nclos\n",
            correction=False,
        )
        reject_tampered_database(
            "sujet.pdf",
            "incident.id_agent = categorie.id_cat",
            "incident.id_cat = categorie.id_cat",
            correction=False,
        )
        reject_tampered_database(
            "sujet.pdf",
            "if incident['statut'] == 'ouvert':",
            "if incident['statut'] == 'clos':",
            correction=False,
        )
        reject_tampered_database(
            "sujet.pdf",
            "Écrivez une requête UPDATE",
            "Consigne de base de données manquante",
            correction=False,
        )
        reject_tampered_database(
            "corrige.pdf",
            "Points accordés pour la jointure",
            "Critère de jointure manquant",
            correction=True,
        )
        reject_tampered_database(
            "sujet.pdf",
            "Exercice 2 (5,5 points)",
            "Exercice 2 (6,5 points)",
            correction=False,
        )
        reject_tampered_database(
            "sujet.pdf", "agent.id_agent", "agent.id_inconnu", correction=False
        )
        reject_tampered_database("sujet.pdf", "2e.", "2x.", correction=False)
        reject_tampered_database("corrige.pdf", "2f.", "2x.", correction=True)

        def reject_tampered_network(role, before, after, *, correction):
            with original_open(bundles[0] / role) as pdf:
                pages = [page.get_text() for page in pdf]
            matching = [index for index, page in enumerate(pages) if before in page]
            assert len(matching) == 1
            pages[matching[0]] = pages[matching[0]].replace(before, after, 1)
            with monkeypatch.context() as patch:
                patch.setattr(
                    runtime.pymupdf, "open", lambda _path: ExtractedDocument(pages)
                )
                with pytest.raises(ValueError):
                    validate_network_contract_pdf(
                        bundles[0] / role,
                        network_contract,
                        correction=correction,
                        exercise=network_exercise,
                    )

        reject_tampered_network(
            "sujet.pdf", "Central\nR1\n4\n", "Central\nR1\n9\n", correction=False
        )
        reject_tampered_network("sujet.pdf", "C\nB\nA\n", "C\nB\nB\n", correction=False)
        reject_tampered_network(
            "sujet.pdf",
            "secret partagé initial",
            "secret partagé certain",
            correction=False,
        )
        reject_tampered_network("sujet.pdf", "3e.", "3x.", correction=False)
        reject_tampered_network(
            "corrige.pdf",
            "Points accordés pour les limites",
            "Critère absent",
            correction=True,
        )
        original_manifest = runtime.graph_edge_manifest
        monkeypatch.setattr(
            runtime, "graph_edge_manifest", lambda graph: "Arêtes incorrectes"
        )
        with pytest.raises(ValueError, match=r"arêtes|Arêtes"):
            validate_contract_pdf(bundles[0] / "sujet.pdf", contract, correction=False)
        monkeypatch.setattr(runtime, "graph_edge_manifest", original_manifest)
        with pytest.raises(ValueError, match=r"contrat|figure|graphe"):
            validate_contract_pdf(
                bundles[0] / "sujet.pdf",
                build_graph_tree_contract(args.seed + 1, "1"),
                correction=False,
            )
        with pymupdf.open(bundles[0] / "sujet.pdf") as question_pdf:
            question_text = "\n".join(page.get_text() for page in question_pdf)
            spans = [
                span
                for page in question_pdf
                for block in page.get_text("dict")["blocks"]
                if "lines" in block
                for line in block["lines"]
                for span in line["spans"]
            ]
            assert any(
                "Exercice 3" in span["text"] and "Bold" in span["font"]
                for span in spans
            )
            assert any(
                "Un campus relie" in span["text"] and "Regular" in span["font"]
                for span in spans
            )
            assert (
                "Sujet d'entraînement" in question_text
                or "SUJET D’ENTRAÎNEMENT" in question_text
            )
            assert "class Noeud:" in question_text
            assert "self.gauche = None" in question_text
            assert "Arbre des identifiants" in question_text
            assert "Réseau pondéré des postes" in question_text
            assert "— links" not in question_text
            assert "— processes" not in question_text
            assert "Réponse attendue" not in question_text
        with pymupdf.open(bundles[0] / "corrige.pdf") as pdf:
            # Structured resources add space, but every exercise remains present
            # with its final marking entry and no empty trailing page.
            assert 5 <= len(pdf) <= (13 if large_print else 10)
            last_page = pdf[-1].get_text()
            assert "3e." in last_page and "3f." in last_page
            text = " ".join(page.get_text() for page in pdf)
            assert all(f"Exercice {exercise} (" in text for exercise in range(1, 4))
            assert text.count("Réponse attendue") == 18
            assert text.count("Barème indicatif") >= 18
            assert pdf[-1].get_text().strip()


def test_runtime_rejects_remote_ollama_without_explicit_consent():
    from Backend.Core.france.runtime import validate_endpoint

    validate_endpoint("http://127.0.0.1:11434", allow_remote=False)
    with pytest.raises(ValueError, match="distant"):
        validate_endpoint("https://school.example.fr", allow_remote=False)
    validate_endpoint("https://school.example.fr", allow_remote=True)
    with pytest.raises(ValueError):
        validate_endpoint("https://key:password@school.example.fr", allow_remote=True)


def test_network_pdf_version_dispatch_has_no_implicit_legacy_fallback():
    from Backend.Core.france.runtime import (
        database_pdf_contract_version,
        network_pdf_contract_version,
    )

    assert network_pdf_contract_version("fr-nsi-written-2027-v16") == "v15"
    assert network_pdf_contract_version("fr-nsi-written-2027-v15") == "v15"
    assert network_pdf_contract_version("fr-nsi-written-2027-v14") == "v14"
    assert database_pdf_contract_version("fr-nsi-written-2027-v16") == "v2"
    assert database_pdf_contract_version("fr-nsi-written-2027-v15") == "v1"
    with pytest.raises(ValueError, match="Version"):
        network_pdf_contract_version("fr-nsi-written-2027-v13")
    with pytest.raises(ValueError, match="Version"):
        database_pdf_contract_version("fr-nsi-written-2027-v12")


@pytest.mark.parametrize("large_print", [False, True])
def test_runtime_publishes_v17_graph_tree_depth_with_locked_pdf_facts(
    tmp_path, monkeypatch, large_print
):
    import json

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.graph_tree_depth_contract import (
        build_graph_tree_depth_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import ControlledGraphTreeDepthFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledGraphTreeDepthFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    _pin_v17_generation(monkeypatch, runtime)
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v17"
    contract = build_graph_tree_depth_contract(args.seed)
    exercise = NSIExercise.model_validate(package["exercises"][0])
    for name, correction in (("sujet.pdf", False), ("corrige.pdf", True)):
        path = bundle / name
        runtime.validate_graph_tree_depth_contract_pdf(
            path, contract, correction=correction, exercise=exercise
        )
        with pymupdf.open(path) as pdf:
            text = " ".join(page.get_text() for page in pdf)
            assert "1j." in text
            assert "A–C–E–F" in text
            assert all(
                word[0] >= 0
                and word[2] <= page.rect.width
                and word[1] >= 0
                and word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            if correction:
                page_text = [page.get_text() for page in pdf]
                if large_print:
                    assert "0,25\npoint" not in "\n".join(page_text)
                for task_id in ("1b", "1e", "1f", "1h", "1j"):
                    assert any(
                        f"{task_id}." in page
                        and f"Barème indicatif — question {task_id}" in page
                        for page in page_text
                    ), f"Keep V17 answer and rubric for {task_id} on one page"
    with pymupdf.open(bundle / "sujet.pdf") as pdf:
        extracted = [page.get_text() for page in pdf]

    class ExtractedDocument:
        def __init__(self, pages):
            self.pages = pages

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def __iter__(self):
            return (
                type("Page", (), {"get_text": lambda _self, value=text: value})()
                for text in self.pages
            )

    missing = extracted.copy()
    graph_page = next(
        i for i, text in enumerate(missing) if "Réseau pondéré des postes" in text
    )
    missing[graph_page] = missing[graph_page].replace(
        "Réseau pondéré des postes", "Réseau absent", 1
    )
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _path: ExtractedDocument(missing))
        with pytest.raises(ValueError, match=r"figure|Figure|graphe"):
            runtime.validate_graph_tree_depth_contract_pdf(
                bundle / "sujet.pdf", contract, correction=False, exercise=exercise
            )
    leaked = extracted.copy()
    leaked[-1] += "\n" + exercise.questions[3].answer
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _path: ExtractedDocument(leaked))
        with pytest.raises(ValueError, match=r"révélée|leaked"):
            runtime.validate_graph_tree_depth_contract_pdf(
                bundle / "sujet.pdf", contract, correction=False, exercise=exercise
            )
    for corrected_fragment in (
        "if cle < noeud.valeur:",
        "if  cle < noeud.valeur :",
        "if voisin not in visites:",
    ):
        leaked_fragment = extracted.copy()
        leaked_fragment[-1] += "\n" + corrected_fragment
        with monkeypatch.context() as patch:
            patch.setattr(
                runtime.pymupdf,
                "open",
                lambda _path, pages=leaked_fragment: ExtractedDocument(pages),
            )
            with pytest.raises(ValueError, match=r"révélée"):
                runtime.validate_graph_tree_depth_contract_pdf(
                    bundle / "sujet.pdf", contract, correction=False, exercise=exercise
                )


@pytest.mark.parametrize("large_print", [False, True])
def test_runtime_v17_preserves_v16_database_depth_with_locked_pdf_facts(
    tmp_path, monkeypatch, large_print
):
    import json

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.database_depth_contract import (
        build_database_depth_contract,
    )
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import ControlledGraphTreeDepthFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledGraphTreeDepthFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    _pin_v17_generation(monkeypatch, runtime)
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v17"
    contract = build_database_depth_contract(args.seed)
    exercise = NSIExercise.model_validate(package["exercises"][1])
    for name, correction in (("sujet.pdf", False), ("corrige.pdf", True)):
        path = bundle / name
        runtime.validate_database_depth_contract_pdf(
            path, contract, correction=correction, exercise=exercise
        )
        with pymupdf.open(path) as pdf:
            text = " ".join(page.get_text() for page in pdf)
            assert "2j." in text
            assert "id_incident" in text
            if correction:
                assert "```" not in text, "SQL rubric must not expose Markdown fences"
            assert all(
                word[0] >= 0
                and word[2] <= page.rect.width
                and word[1] >= 0
                and word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
    subject = bundle / "sujet.pdf"
    with pymupdf.open(subject) as pdf:
        extracted = [page.get_text() for page in pdf]
    if large_print:
        prompt_words = exercise.questions[4].prompt.split()
        opening = " ".join(prompt_words[:5])
        ending = " ".join(prompt_words[-5:])
        normalized_pages = [" ".join(page.split()) for page in extracted]
        assert any(opening in page and ending in page for page in normalized_pages), (
            "Question 2e must not split across large-print pages"
        )

    class ExtractedDocument:
        def __init__(self, pages):
            self.pages = pages

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def __iter__(self):
            return (
                type("Page", (), {"get_text": lambda _self, value=text: value})()
                for text in self.pages
            )

    altered = extracted.copy()
    row_index = next(
        i for i, text in enumerate(altered) if "101\n1\n2\nouvert\n" in text
    )
    altered[row_index] = altered[row_index].replace(
        "101\n1\n2\nouvert\n", "101\n1\n2\nclos\n", 1
    )
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _path: ExtractedDocument(altered))
        with pytest.raises(ValueError, match="rows"):
            runtime.validate_database_depth_contract_pdf(
                subject, contract, correction=False, exercise=exercise
            )
    leaked = extracted.copy()
    leaked[-1] += "\n" + exercise.questions[1].answer
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _path: ExtractedDocument(leaked))
        with pytest.raises(ValueError, match="leaked"):
            runtime.validate_database_depth_contract_pdf(
                subject, contract, correction=False, exercise=exercise
            )


@pytest.mark.parametrize("large_print", [False, True])
def test_runtime_v17_preserves_v15_network_depth_with_locked_pdf_facts(
    tmp_path, monkeypatch, large_print
):
    import json

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.network_depth_contract import build_network_depth_contract
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import ControlledGraphTreeDepthFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime,
        "FrenchOllamaClient",
        lambda **_: ControlledGraphTreeDepthFrenchClient(),
    )
    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=index,
        output=str(tmp_path / "output"),
        seed=270100,
        model="fixture",
        ollama_url="http://localhost:11434",
        allow_remote=False,
        large_print=large_print,
    )
    _pin_v17_generation(monkeypatch, runtime)
    assert runtime.handle_generate_assessment(args) == 0
    (bundle,) = (tmp_path / "output").glob("nsi-*")
    package = json.loads((bundle / "assessment.json").read_text())
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v17"
    contract = build_network_depth_contract(args.seed)
    exercise = NSIExercise.model_validate(package["exercises"][2])
    for name, correction in (("sujet.pdf", False), ("corrige.pdf", True)):
        path = bundle / name
        runtime.validate_network_depth_contract_pdf(
            path, contract, correction=correction, exercise=exercise
        )
        with pymupdf.open(path) as pdf:
            text = " ".join(page.get_text() for page in pdf)
            assert "Sept liaisons bidirectionnelles" in text
            assert "État simultané des processus" in text
            assert all(
                word[0] >= 0
                and word[2] <= page.rect.width
                and word[1] >= 0
                and word[3] <= page.rect.height
                for page in pdf
                for word in page.get_text("words")
            )
            assert ("Accorder pour" in text) == correction
            if correction:
                normalized = " ".join(text.split())
                assert "0,25 point" in normalized
                assert "0,25 points" not in normalized
                final_page = pdf[-1].get_text()
                assert "3f." in final_page
                assert "Barème indicatif" in final_page
            else:
                final_page = pdf[-1].get_text()
                assert "3e." in final_page
                assert "3f." in final_page

    real_open = pymupdf.open

    class PageText:
        def __init__(self, value):
            self.value = value

        def get_text(self):
            return self.value

    class DocumentText:
        def __init__(self, values):
            self.values = values

        def __enter__(self):
            return [PageText(value) for value in self.values]

        def __exit__(self, *_):
            return False

    def reject_text_change(filename, old, new, correction):
        with real_open(bundle / filename) as pdf:
            pages = [page.get_text() for page in pdf]
        assert sum(old in page for page in pages) == 1
        pages = [page.replace(old, new, 1) for page in pages]
        with monkeypatch.context() as patch:
            patch.setattr(runtime.pymupdf, "open", lambda _: DocumentText(pages))
            with pytest.raises(ValueError):
                runtime.validate_network_depth_contract_pdf(
                    bundle / filename,
                    contract,
                    correction=correction,
                    exercise=exercise,
                )

    first_link = contract.to_dict()["links"][0]
    reject_text_change(
        "sujet.pdf",
        f"{first_link[0]}\n{first_link[1]}\n{first_link[2]}\n",
        f"{first_link[0]}\n{first_link[1]}\n99\n",
        False,
    )
    reject_text_change(
        "sujet.pdf",
        "capteur n'appose pas de signature",
        "capteur signe tous les messages",
        False,
    )
    reject_text_change(
        "sujet.pdf",
        "restent inchangés",
        "changent aussi",
        False,
    )
    reject_text_change(
        "corrige.pdf",
        "prévue arrête P2, qui libère B",
        "prévue arrête P2 sans libération explicite",
        True,
    )
    reject_text_change("sujet.pdf", "3b.", "3x.", False)
    reject_text_change(
        "corrige.pdf",
        "Réponse attendue\nCentral–R1",
        "Réponse proposée\nCentral–R1",
        True,
    )
    reject_text_change(
        "sujet.pdf",
        "3f.",
        "Barème indicatif\n3f.",
        False,
    )
    reject_text_change(
        "corrige.pdf",
        exercise.questions[1].marking[0].criterion,
        "Crédit absent",
        True,
    )
    with real_open(bundle / "corrige.pdf") as pdf:
        pages = [page.get_text() for page in pdf]
    misplaced_answer = exercise.questions[0].answer
    assert sum(misplaced_answer in page for page in pages) == 1
    pages = [page.replace(misplaced_answer, "Réponse omise", 1) for page in pages]
    pages[-1] += "\n" + misplaced_answer
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _: DocumentText(pages))
        with pytest.raises(ValueError, match=r"answer|réponse|Réponse"):
            runtime.validate_network_depth_contract_pdf(
                bundle / "corrige.pdf",
                contract,
                correction=True,
                exercise=exercise,
            )
    with real_open(bundle / "corrige.pdf") as pdf:
        pages = [page.get_text() for page in pdf]
    misplaced_criterion = exercise.questions[1].marking[0].criterion
    assert sum(misplaced_criterion in page for page in pages) == 1
    pages = [page.replace(misplaced_criterion, "Critère déplacé", 1) for page in pages]
    pages[-1] += "\n" + misplaced_criterion
    with monkeypatch.context() as patch:
        patch.setattr(runtime.pymupdf, "open", lambda _: DocumentText(pages))
        with pytest.raises(ValueError, match=r"credit|rubric|barème|Barème"):
            runtime.validate_network_depth_contract_pdf(
                bundle / "corrige.pdf",
                contract,
                correction=True,
                exercise=exercise,
            )


def test_network_depth_correction_sets_dijkstra_steps_on_separate_lines(tmp_path):
    import re

    import pymupdf

    from Backend.Core.france.network_depth_contract import build_network_depth_contract
    from Backend.Core.france.network_depth_prose import render_network_depth_candidate
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _tasks_for_seed_v15
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.runtime import validate_network_depth_contract_pdf

    seed = 270100
    contract = build_network_depth_contract(seed)
    selection = {
        "scene_id": "terrain",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }
    exercise = NSIExercise.model_validate(
        render_network_depth_candidate(
            contract, selection, _tasks_for_seed_v15(seed)[2]["question_blueprint"]
        )
    )
    path = tmp_path / "correction.pdf"
    render_assessment(path, [exercise], correction=True)
    validate_network_depth_contract_pdf(
        path, contract, correction=True, exercise=exercise
    )
    with pymupdf.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
    for step in contract.to_dict()["expected"]["after"]["trace"]:
        assert re.search(
            rf"(?m)^{re.escape(step['settled'])}\({step['distance']}\):",
            text,
        )


def test_network_depth_answer_and_rubric_stay_together(tmp_path):
    import pymupdf

    from Backend.Core.france.network_depth_contract import build_network_depth_contract
    from Backend.Core.france.network_depth_prose import render_network_depth_candidate
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _tasks_for_seed_v15
    from Backend.Core.france.rendering import render_assessment

    seed = 270100
    selection = {
        "scene_id": "terrain",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }
    exercise = NSIExercise.model_validate(
        render_network_depth_candidate(
            build_network_depth_contract(seed),
            selection,
            _tasks_for_seed_v15(seed)[2]["question_blueprint"],
        )
    )
    output = tmp_path / "network-correction.pdf"
    render_assessment(output, [exercise], correction=True)

    with pymupdf.open(output) as pdf:
        pages = [" ".join(page.get_text().split()) for page in pdf]
    answer_fragment = "P1 obtient B, termine puis libère A et B."
    answer_page = next(
        index for index, page in enumerate(pages) if answer_fragment in page
    )
    final_credit = "l'ordre commun A avant B empêchant le cycle"
    credit_page = next(
        index for index, page in enumerate(pages) if final_credit in page
    )
    assert credit_page == answer_page
    assert "Barème indicatif — question 3d" in pages[credit_page]


def test_french_pdf_restores_roman_body_after_other_renderer_font_mapping(
    tmp_path, monkeypatch
):
    import pymupdf
    from reportlab.lib import fonts

    from Backend.Core.fonts import register_fonts
    from Backend.Core.france.network_contract import build_network_contract
    from Backend.Core.france.network_prose import render_network_candidate
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _tasks_for_seed
    from Backend.Core.france.rendering import render_assessment

    register_fonts("ExamSans", "ExamSans-Bold", "ExamSans-Italic")
    selection = {
        "scene_id": "campus",
        "question_forms": {f"3{letter}": f"3{letter}-q1" for letter in "abcdef"},
        "rubric_forms": {f"3{letter}": f"3{letter}-r1" for letter in "abcdef"},
    }
    exercise = NSIExercise.model_validate(
        render_network_candidate(
            build_network_contract(270100),
            selection,
            _tasks_for_seed(270100)[2]["question_blueprint"],
        )
    )
    with monkeypatch.context() as patch:
        patch.setitem(fonts._ps2tt_map, "examsans", ("examsans", 0, 1))
        patch.setitem(fonts._tt2ps_map, ("examsans", 0, 0), "ExamSans-Italic")
        path = tmp_path / "subject.pdf"
        render_assessment(path, [exercise], correction=False)
    with pymupdf.open(path) as pdf:
        spans = [
            span
            for block in pdf[-1].get_text("dict")["blocks"]
            if "lines" in block
            for line in block["lines"]
            for span in line["spans"]
        ]
    assert any(
        "Un campus relie" in span["text"] and "Regular" in span["font"]
        for span in spans
    )


def test_missing_sources_fail_before_model_and_leave_no_output(tmp_path, capsys):
    from Backend.Core.france.runtime import handle_generate_assessment

    args = Namespace(
        assessment="fr-bac-general-nsi-written-2027",
        reference_index=tmp_path / "missing.sqlite",
        output=str(tmp_path / "output"),
        seed=5,
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://127.0.0.1:11434",
        allow_remote=False,
        large_print=False,
    )
    assert handle_generate_assessment(args) == 1
    assert "références" in capsys.readouterr().out
    assert not (tmp_path / "output").exists()


def test_originality_history_reads_only_bounded_valid_local_bundles(tmp_path):
    import json

    from Backend.Core.france.runtime import load_originality_history
    from tests.test_nsi_assessment import exercise

    output = tmp_path / "output"
    valid = output / "nsi-2027-1-valid"
    valid.mkdir(parents=True)
    payload = {
        "schema_version": 2,
        "assessment_policy": "fr-bac-general-nsi-written-2027",
        "exercises": [exercise()],
    }
    (valid / "assessment.json").write_text(json.dumps(payload), encoding="utf-8")
    malformed = output / "nsi-2027-2-malformed"
    malformed.mkdir()
    (malformed / "assessment.json").write_text("not-json", encoding="utf-8")

    history = load_originality_history(output)
    assert len(history) == 1
    assert "Données d'un réseau" in history[0]
    assert "Valeur 1 justifiée" not in history[0]
