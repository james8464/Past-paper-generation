"""V36 authors content through providers, never a finite question catalogue."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError as SchemaValidationError

from Backend.Core.france import llm_pipeline as subject
from tests.test_nsi_pipeline import make_index


def test_authoring_explains_prior_domains_without_fixing_tasks_or_reference_themes():
    prompt = subject.exercise_request(
        "2", 42, [], previous_topics=("algorithmique", "structures-donnees")
    ).prompt
    assert "previous_topics indique les domaines déjà abordés" in prompt
    assert "tâches principales évaluées différentes" in prompt
    assert "prérequis ou représentations communs restent possibles" in prompt
    assert "Un changement de contexte seul ne suffit pas" in prompt
    assert "leurs thèmes ne sont pas des choix obligatoires" in prompt
    assert '"previous_topics": ["algorithmique", "structures-donnees"]' in prompt


@pytest.mark.parametrize("shared_pages", [False, True])
def test_balanced_references_are_bounded_scoped_deterministic_and_deduplicated(
    monkeypatch, tmp_path, shared_pages
):
    from Backend.Core.education_context import NSI_2027, NSI_CONTEXT
    from Backend.Core.scoped_references import ReferenceHit

    calls = []

    class Index:
        def __init__(self, path, *, read_only):
            assert path == tmp_path / "references.sqlite" and read_only is True

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def retrieve(self, context, curriculum, query, *, categories, limit):
            assert context == NSI_CONTEXT
            assert curriculum == NSI_2027.curriculum_version
            assert limit == 2
            calls.append((categories, query))
            category = categories[0]
            start = (
                1
                if shared_pages or category == "official_paper"
                else 2 * (len(calls) - 1) + 1
            )
            return [
                ReferenceHit(
                    category,
                    "a" * 64,
                    page,
                    "Programme données",
                    "https://eduscol.education.gouv.fr/test",
                    category,
                )
                for page in (start, start + 1)
            ]

    monkeypatch.setattr(subject, "ReferenceIndex", Index)
    first = subject._retrieve_references(tmp_path / "references.sqlite")
    first_calls = list(calls)
    calls.clear()
    assert subject._retrieve_references(tmp_path / "references.sqlite") == first
    expected_queries = [
        " ".join(
            text
            for domain, text in subject.CURRICULUM_OBJECTIVES.values()
            if domain == topic
        )
        for topic in sorted(subject.TOPICS)
    ]
    assert first_calls == [(("programme",), query) for query in expected_queries] + [
        (
            ("official_paper",),
            "structures données algorithmique programmation bases données réseaux",
        )
    ]
    assert len(first) == (4 if shared_pages else 12)
    assert [item["category"] for item in first[-2:]] == ["official_paper"] * 2
    assert len(
        {(item["source_id"], item["source_sha256"], item["page"]) for item in first}
    ) == len(first)


def test_balanced_reference_lookup_preserves_foreign_holdout_and_curriculum_filters(
    tmp_path,
):
    from dataclasses import replace
    from hashlib import sha256

    from Backend.Core.education_context import NSI_CONTEXT
    from Backend.Core.scoped_references import ReferenceIndex, SourceDocument

    path = tmp_path / "references.sqlite"
    make_index(path)
    text = "Structures données algorithmique programmation bases données réseaux."
    with ReferenceIndex(path) as index:
        for identifier, context, split, curriculum in (
            (
                "uk",
                replace(NSI_CONTEXT, country="GB", education_system="uk"),
                "reference",
                "nsi-2019",
            ),
            ("holdout", NSI_CONTEXT, "holdout", "nsi-2019"),
            ("obsolete", NSI_CONTEXT, "reference", "obsolete"),
        ):
            index.add(
                SourceDocument(
                    identifier,
                    context,
                    curriculum,
                    "programme",
                    "MEN",
                    "https://eduscol.education.gouv.fr/test",
                    "2026-09-28T12:00:00+00:00",
                    sha256(text.encode()).hexdigest(),
                    2026,
                    "national",
                    "reference-only",
                    split,
                ),
                text,
                [(1, text)],
            )
    before = sha256(path.read_bytes()).hexdigest()
    hits = subject._retrieve_references(path)
    assert {hit["source_id"] for hit in hits} == {"programme", "official_paper"}
    assert sha256(path.read_bytes()).hexdigest() == before


def test_expanded_reference_bounds_and_duplicate_identity_refuse_tampering():
    references = [
        dict(
            source_id="programme",
            source_sha256="a" * 64,
            page=i + 1,
            text="Programme",
            url="https://eduscol.education.gouv.fr/test",
            category="programme",
        )
        for i in range(10)
    ]
    references.extend(
        dict(
            source_id="paper",
            source_sha256="b" * 64,
            page=i + 1,
            text="Sujet",
            url="https://eduscol.education.gouv.fr/test",
            category="official_paper",
        )
        for i in range(2)
    )
    subject._validate_references(references)
    for invalid in (
        [*references, dict(references[0], page=11)],
        [*references[:9], dict(references[-1], page=3), *references[-2:]],
        [*references[:-1], dict(references[0], text="changed")],
        [*references[:-1], references[0]],
    ):
        with pytest.raises(ValueError):
            subject._validate_references(invalid)


def test_conflicting_duplicate_hit_is_not_silently_deduplicated(monkeypatch, tmp_path):
    from dataclasses import replace

    from Backend.Core.scoped_references import ReferenceIndex

    path = tmp_path / "references.sqlite"
    make_index(path)
    retrieve = ReferenceIndex.retrieve
    calls = 0

    def changed_hit(index, *args, **kwargs):
        nonlocal calls
        calls += 1
        hits = retrieve(index, *args, **kwargs)
        return (
            [replace(hit, text="Contradiction") for hit in hits] if calls == 2 else hits
        )

    monkeypatch.setattr(ReferenceIndex, "retrieve", changed_hit)
    with pytest.raises(ValueError, match="contradictoire"):
        subject._retrieve_references(path)


@pytest.mark.parametrize("missing", ["programme", "official_paper"])
def test_balancing_never_invents_a_missing_reference_category(tmp_path, missing):
    from Backend.Core.scoped_references import ReferenceIndex

    path = tmp_path / "references.sqlite"
    make_index(path)
    with ReferenceIndex(path) as index:
        index.connection.execute("DELETE FROM chunks WHERE source_id=?", (missing,))
        index.connection.execute("DELETE FROM sources WHERE id=?", (missing,))
        index.connection.commit()
    client = Client()
    with pytest.raises(ValueError):
        subject.generate(index_path=path, client=client, seed=42)
    assert client.requests == []


def test_balancing_propagates_index_failures_instead_of_skipping_them(
    monkeypatch, tmp_path
):
    from Backend.Core.scoped_references import ReferenceIndex

    path = tmp_path / "references.sqlite"
    make_index(path)

    def broken(*_args, **_kwargs):
        raise ValueError("Corrupt reference record")

    monkeypatch.setattr(ReferenceIndex, "retrieve", broken)
    with pytest.raises(ValueError, match="Corrupt reference record"):
        subject._retrieve_references(path)


def raw_exercise(identifier="1", marker="Aventure originale"):
    topic, code = {
        "1": ("structures-donnees", "SD-LINEAIRE"),
        "2": ("bases-donnees", "BDD-MODELE"),
        "3": ("architectures-reseaux", "ASR-PROCESSUS"),
    }[identifier]
    return {
        "id": identifier,
        "title": marker,
        "context": f"Une équipe étudie ses données dans le contexte {marker}.",
        "topics": [topic],
        "minutes": 70,
        "target_points": "6",
        "materials": [
            {
                "kind": "table",
                "id": "donnees",
                "title": "Données du contexte",
                "columns": ["Objet", "Valeur"],
                "rows": [["Alpha", "2"], ["Beta", "4"]],
            }
        ],
        "questions": [
            dict(
                id=str(i + 1),
                prompt=f"Justifiez le résultat de l'étape {i + 1} dans {marker}.",
                points="1",
                answer=f"Réponse développée pour {marker}, étape {i + 1}.",
                marking=[
                    {
                        "points": "1",
                        "criterion": "Raisonnement cohérent avec les données.",
                    }
                ],
                material_ids=["donnees"],
                curriculum_codes=[code],
                operation=["apply", "analyse", "design", "debug", "justify", "analyse"][
                    i
                ],
                difficulty=[2, 2, 3, 3, 4, 4][i],
                estimated_minutes=[10, 10, 10, 10, 15, 15][i],
                verification={"kind": "human"},
            )
            for i in range(6)
        ],
    }


class Client:
    provider = "ollama"
    model = "mock-model"

    def __init__(self, marker="Aventure originale", mutate=None):
        self.marker, self.mutate = marker, mutate
        self.requests = []

    def generate_request(self, request):
        self.requests.append(request)
        properties = request.schema["properties"]
        if "id" in properties:
            result = raw_exercise(properties["id"]["const"], self.marker)
            if self.mutate:
                self.mutate(result)
            return result
        if "answers" in properties:
            assert (
                "marking" not in request.prompt and "verification" not in request.prompt
            )
            assert "Réponse développée" not in request.prompt
            return {
                "answers": {
                    identifier: "Solution indépendante détaillée."
                    for identifier in properties["answers"]["properties"]
                },
                "issues": [],
            }
        return {
            identifier: {
                "correct": True,
                "answer_complete": True,
                "rubric_consistent": True,
                "curriculum_aligned": True,
                "french": True,
                "self_contained": True,
                "issues": [],
                **(
                    {"advisories": []}
                    if "advisories" in properties[identifier]["properties"]
                    else {}
                ),
            }
            for identifier in properties
        }


class BlindNoteClient(Client):
    def generate_request(self, request):
        properties = request.schema["properties"]
        if "question_review" in properties:
            self.requests.append(request)
            assert all(
                note in request.prompt
                for note in getattr(
                    self, "notes", ["Une convention mérite une précision."]
                )
            )
            return {
                "question_review": {
                    identifier: {
                        **{
                            name: True
                            for name in (
                                "correct",
                                "answer_complete",
                                "rubric_consistent",
                                "curriculum_aligned",
                                "french",
                                "self_contained",
                            )
                        },
                        "issues": [],
                        **(
                            {"advisories": []}
                            if "advisories"
                            in properties["question_review"]["properties"][identifier][
                                "properties"
                            ]
                            else {}
                        ),
                    }
                    for identifier in properties["question_review"]["properties"]
                },
                "blind_issue_dispositions": {
                    "0": {
                        "issue_index": 0,
                        "blocking": False,
                        "rationale": "Les données publiques fixent cette convention.",
                    }
                },
            }
        result = super().generate_request(request)
        if "answers" in properties:
            result["issues"] = ["Une convention mérite une précision."]
        return result


def test_blind_notes_are_adjudicated_and_retained_as_revalidated_warnings(tmp_path):
    client = BlindNoteClient()
    package = generate(tmp_path, client)
    assert len(client.requests) == 9
    notes = [
        w for w in package["warnings"] if w.get("code") == "blind_issue_nonblocking"
    ]
    assert len(notes) == 3
    assert notes[0]["issue"] == "Une convention mérite une précision."
    assert notes[0]["rationale"] == "Les données publiques fixent cette convention."
    assert notes[0]["question_id"] == "exercise"
    assert notes[0]["issue"] in notes[0]["reason"]
    assert notes[0]["rationale"] in notes[0]["reason"]
    assert len(subject.validate_package(package)) == 3


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.clear(),
        lambda d: d.update({"1": d.pop("0")}),
        lambda d: d["0"].update(issue_index=True),
        lambda d: d["0"].update(issue_index=0.0),
        lambda d: d["0"].update(issue_index=1),
        lambda d: d["0"].update(blocking="false"),
        lambda d: d["0"].update(blocking=0),
        lambda d: d["0"].update(blocking=None),
        lambda d: d.update({"20": deepcopy(d["0"])}),
        lambda d: d["0"].update(rationale=""),
        lambda d: d["0"].update(rationale="   "),
        lambda d: d["0"].update(blocking=True),
    ],
)
def test_invalid_or_blocking_blind_disposition_refuses(tmp_path, mutate):
    class Invalid(BlindNoteClient):
        def generate_request(self, request):
            value = super().generate_request(request)
            if "blind_issue_dispositions" in value:
                mutate(value["blind_issue_dispositions"])
            return value

    client = Invalid()
    with pytest.raises((ValueError, SchemaValidationError)):
        generate(tmp_path, client)
    assert len(client.requests) == 3


@pytest.mark.parametrize(
    "flag",
    [
        "correct",
        "answer_complete",
        "rubric_consistent",
        "curriculum_aligned",
        "french",
        "self_contained",
        "issues",
    ],
)
def test_blind_adjudication_does_not_override_hard_question_failure(tmp_path, flag):
    class Invalid(BlindNoteClient):
        def generate_request(self, request):
            value = super().generate_request(request)
            if "question_review" in value:
                value["question_review"]["1"][flag] = (
                    ["Problème de fond."] if flag == "issues" else False
                )
            return value

    with pytest.raises(ValueError, match="refuse"):
        generate(tmp_path, Invalid())


def test_dispositions_must_cover_every_note_not_just_first(tmp_path):
    class TwoNotes(BlindNoteClient):
        def generate_request(self, request):
            value = super().generate_request(request)
            if "answers" in value:
                value["issues"].append("Une seconde réserve distincte.")
            return value

    client = TwoNotes()
    with pytest.raises(SchemaValidationError):
        generate(tmp_path, client)
    assert len(client.requests) == 3


class TwoAdjudicatedNotes(BlindNoteClient):
    notes = ("L’élève peut écrire « Noé ».", "Deux parcours équivalents : A→B ; A→C.")
    reasons = (
        "L’accent est conservé, sans normalisation.",
        "L’ordre ne change pas leur validité.",
    )

    def generate_request(self, request):
        value = super().generate_request(request)
        if "answers" in value:
            value["issues"] = list(self.notes)
        if "question_review" in value:
            # Deliberately reversed response key order, indexed notes remain ordered.
            value["blind_issue_dispositions"] = {
                str(index): {
                    "issue_index": index,
                    "blocking": False,
                    "rationale": self.reasons[index],
                }
                for index in (1, 0)
            }
        return value


def test_two_note_adjudication_retains_original_bytes_and_note_order(tmp_path):
    client = TwoAdjudicatedNotes()
    package = generate(tmp_path, client)
    notes = [
        w for w in package["warnings"] if w.get("code") == "blind_issue_nonblocking"
    ]
    for index, warning in enumerate(notes):
        assert warning["issue_index"] == index % 2
        assert warning["issue"].encode() == client.notes[index % 2].encode()
        assert warning["rationale"].encode() == client.reasons[index % 2].encode()


@pytest.mark.parametrize(
    "target", ["duplicate_index", "missing_question", "unknown_question"]
)
def test_complete_adjudication_cannot_hide_bad_coverage(tmp_path, target):
    class Invalid(TwoAdjudicatedNotes):
        def generate_request(self, request):
            value = super().generate_request(request)
            if "question_review" in value:
                if target == "duplicate_index":
                    value["blind_issue_dispositions"]["1"]["issue_index"] = 0
                elif target == "missing_question":
                    value["question_review"].pop("1")
                else:
                    value["question_review"]["unknown"] = deepcopy(
                        value["question_review"]["1"]
                    )
            return value

    with pytest.raises(SchemaValidationError):
        generate(tmp_path, Invalid())


def test_no_blind_notes_use_prospective_question_schema_without_disposition_envelope(
    tmp_path,
):
    client = Client()
    package = generate(tmp_path, client)
    assert client.requests[2].schema == subject._review_schema(
        subject.validate_authored_exercise(raw_exercise(), "1"), include_advisories=True
    )
    assert all(
        "blind_issue_dispositions" not in review for review in package["reviews"]
    )


@pytest.mark.parametrize(
    "target",
    [
        "disposition",
        "warning",
        "note",
        "edit_rationale",
        "omit_rationale",
        "warning_text",
    ],
)
def test_blind_adjudication_package_tampering_refuses_with_new_content_hash(
    tmp_path, target
):
    package = generate(tmp_path, BlindNoteClient())
    if target == "disposition":
        package["reviews"][0]["blind_issue_dispositions"]["0"]["blocking"] = True
    elif target == "warning":
        package["warnings"] = [
            w for w in package["warnings"] if w.get("code") != "blind_issue_nonblocking"
        ]
    elif target == "note":
        package["reviews"][0]["blind_solution"]["issues"].append("Nouvelle réserve.")
    elif target == "edit_rationale":
        package["reviews"][0]["blind_issue_dispositions"]["0"]["rationale"] = (
            "Texte remplacé."
        )
    elif target == "omit_rationale":
        package["reviews"][0]["blind_issue_dispositions"]["0"].pop("rationale")
    else:
        next(
            w for w in package["warnings"] if w.get("code") == "blind_issue_nonblocking"
        )["reason"] = "Avertissement masqué."
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_package(package)


def generate(tmp_path, client):
    path = tmp_path / "index.sqlite"
    make_index(path)
    return subject.generate(index_path=path, client=client, seed=42)


def test_different_model_responses_produce_different_substantive_papers(tmp_path):
    a = generate(tmp_path, Client("Aventure Alpha"))
    b = generate(tmp_path, Client("Recherche Beta"))
    assert a["exercises"] != b["exercises"]
    assert a["identity"]["content_sha256"] != b["identity"]["content_sha256"]
    assert a["model_used"] is True and a["generation_origin"] == "model_authored"
    assert a["status"] == "unreviewed_draft"
    assert len(subject.validate_package(a)) == 3
    assert (a["technical_points"], a["language_points"], a["minutes"]) == (
        "18",
        "2",
        210,
    )
    assert a["warnings"] and all(
        item["state"] == "not_checked" for item in a["warnings"]
    )


def test_requests_use_typed_schema_and_no_fixed_question_or_answer_bank(tmp_path):
    client = Client()
    package = generate(tmp_path, client)
    assert len(client.requests) == 9
    assert all(
        request.operation == "french_nsi_authoring" for request in client.requests
    )
    assert all(
        review["status"] == "model_reviewed_not_proven" for review in package["reviews"]
    )
    for request in client.requests[::3]:
        assert "Invente le contexte" in request.prompt
        assert "Réponse développée" not in request.prompt
        assert request.output_budget == 8192
    assert {item["category"] for item in package["references"]} == {
        "programme",
        "official_paper",
    }


@pytest.mark.parametrize(
    "provider,budgets",
    [
        ("ollama", [8192, 6000, 4096]),
        ("apple", [8192, 6000, 4096]),
        ("openai", [8192, 6000, 4096]),
        ("anthropic", [8192, 6000, 4096]),
        ("deepseek", [32768, 16384, 16384]),
    ],
)
def test_phase_output_allowances_are_explicit_and_provider_scoped(
    tmp_path, provider, budgets
):
    client = Client()
    client.provider = provider
    generate(tmp_path, client)
    assert [request.output_budget for request in client.requests] == budgets * 3


def test_authoring_budget_override_does_not_modify_schema_prompt_or_sampling_identity():
    default = subject.exercise_request(
        "1", 42, [], previous_topics=("Bases de données",)
    )
    larger = subject.exercise_request(
        "1", 42, [], previous_topics=("Bases de données",), output_budget=16384
    )
    assert default.output_budget == 8192 and larger.output_budget == 16384
    for field in (
        "prompt",
        "operation",
        "schema",
        "generation_seed",
        "seed",
        "attempt",
        "temperature",
        "expected_ids",
    ):
        assert getattr(default, field) == getattr(larger, field)


def test_structural_deepseek_regeneration_keeps_allowance_and_owned_schema_seed(
    tmp_path,
):
    class Retry(Client):
        provider = "deepseek"

        def generate_request(self, request):
            result = super().generate_request(request)
            if "id" in request.schema["properties"] and request.attempt == 1:
                result["topics"] = ["not-in-the-taxonomy"]
            return result

    client = Retry()
    generate(tmp_path, client)
    authors = [
        request for request in client.requests if "id" in request.schema["properties"]
    ]
    assert [request.attempt for request in authors] == [1, 2] * 3
    for first, second in zip(authors[::2], authors[1::2], strict=True):
        assert first.output_budget == second.output_budget == 32768
        assert first.schema == second.schema
        assert first.generation_seed == second.generation_seed
        assert first.temperature == second.temperature


def test_authoring_grammar_exposes_the_taxonomy_and_contract_keys():
    from jsonschema import Draft202012Validator

    from Backend.Core.france.nsi import CURRICULUM_OBJECTIVES, TOPICS

    schema = subject.exercise_request("1", 42, []).schema
    assert set(schema["properties"]["topics"]["items"]["enum"]) == TOPICS
    question = schema["$defs"]["NSIQuestion"]["properties"]
    assert set(question["curriculum_codes"]["items"]["enum"]) == set(
        CURRICULUM_OBJECTIVES
    )
    raw = raw_exercise()
    raw["questions"][0]["verification"] = {"type": "human"}
    assert list(Draft202012Validator(schema).iter_errors(raw))


def test_one_structural_regeneration_does_not_patch_answers_or_relax_marks(tmp_path):
    class Retry(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "id" in request.schema["properties"] and request.attempt == 1:
                result["topics"] = ["SD-LINEAIRE"]
            return result

    client = Retry()
    package = generate(tmp_path, client)
    authors = [
        request for request in client.requests if "id" in request.schema["properties"]
    ]
    assert [request.attempt for request in authors] == [1, 2] * 3
    assert all(
        "REGENERATION" in request.prompt for request in authors if request.attempt == 2
    )
    assert all("Réponse développée" not in request.prompt for request in authors)
    assert [item["attempts"] for item in package["authoring_attempts"]] == [2, 2, 2]
    assert len(subject.validate_package(package)) == 3


def test_second_invalid_structural_response_stops_without_review_or_catalogue(tmp_path):
    from Backend.Core.generation_diagnostics import GenerationEvidenceError

    client = Client(mutate=lambda raw: raw.update(topics=["not-a-topic"]))
    with pytest.raises(GenerationEvidenceError) as failure:
        generate(tmp_path, client)
    assert len(client.requests) == 2
    assert len(failure.value.details["attempts"]) == 2
    assert isinstance(failure.value.__cause__, SchemaValidationError)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.update(target_points="7"),
        lambda raw: raw.update(minutes=60),
        lambda raw: raw["questions"][0].update(points="2"),
        lambda raw: raw["questions"][0]["marking"][0].update(points="0.5"),
        lambda raw: raw["questions"][0].pop("verification"),
        lambda raw: raw["questions"][0].update(curriculum_codes=["UK-AO1"]),
        lambda raw: raw["questions"][0].update(
            answer="```python\nimport os\nos.remove('paper.pdf')\n```"
        ),
        lambda raw: raw["questions"][0].update(
            answer="```python\nvalue = open('secret')\n```"
        ),
        lambda raw: raw["questions"][0].update(
            verification={"kind": "tree_case_contract", "seed": 123}
        ),
        lambda raw: raw["questions"][0].update(
            verification={
                "kind": "python_trace",
                "code": "x = 2 + 3",
                "variable": "x",
                "expected": 6,
            }
        ),
    ],
)
def test_malformed_marks_curriculum_unsafe_code_and_fixed_contracts_refuse(mutate):
    raw = raw_exercise()
    mutate(raw)
    with pytest.raises((ValueError, SchemaValidationError)):
        subject.validate_authored_exercise(raw, "1")


def test_generic_execution_is_bounded_and_does_not_trust_model_expected_value():
    raw = raw_exercise()
    raw["questions"][0]["verification"] = {
        "kind": "python_trace",
        "code": "resultat = 2 + 3",
        "variable": "resultat",
        "expected": 5,
    }
    assert subject.validate_authored_exercise(raw, "1")
    raw["questions"][0]["verification"]["code"] = (
        "import os\nresultat = os.listdir('.')"
    )
    with pytest.raises(ValueError):
        subject.validate_authored_exercise(raw, "1")


def test_no_compatible_references_means_no_model_calls_and_no_catalogue_fallback(
    tmp_path,
):
    from Backend.Core.scoped_references import ReferenceIndex

    path = tmp_path / "empty.sqlite"
    with ReferenceIndex(path):
        pass
    client = Client()
    with pytest.raises(ValueError):
        subject.generate(index_path=path, client=client, seed=42)
    assert not client.requests


def test_negative_model_review_fails_instead_of_selecting_a_fixed_family(tmp_path):
    class Negative(Client):
        def generate_request(self, request):
            result = super().generate_request(request)
            if "1" in result:
                result["1"]["correct"] = False
                result["1"]["issues"] = ["Réponse incorrecte."]
            return result

    client = Negative()
    with pytest.raises(ValueError, match="refuse"):
        generate(tmp_path, client)
    assert len(client.requests) == 3


def test_restore_revalidates_reviews_even_if_content_hash_is_recomputed(tmp_path):
    package = generate(tmp_path, Client())
    package["reviews"][0]["question_review"]["1"]["correct"] = False
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError, match=r"contrôle|review"):
        subject.validate_package(package)


def test_changed_content_or_false_model_identity_cannot_replay(tmp_path):
    package = generate(tmp_path, Client())
    for mutate in (
        lambda p: p.update(model_used=False),
        lambda p: p["exercises"][0].update(title="Texte remplacé"),
        lambda p: p["identity"].update(seed=True),
    ):
        changed = deepcopy(package)
        mutate(changed)
        with pytest.raises(ValueError):
            subject.validate_package(changed)


def test_unimported_system_access_in_snippet_is_still_rejected():
    raw = raw_exercise()
    raw["questions"][0]["answer"] = "```python\nos.system('commande')\n```"
    with pytest.raises(ValueError, match="non autorisé"):
        subject.validate_authored_exercise(raw, "1")


def test_actual_installed_mlx_grammar_compiles_authoring_and_review_shapes():
    import json

    llguidance = pytest.importorskip("llguidance")
    from Backend.Core.providers import _mlx_decoder_schema

    exercise = subject.validate_authored_exercise(raw_exercise(), "1")
    for schema in (
        subject.exercise_request("1", 42, []).schema,
        subject._solution_schema(exercise),
        subject._review_schema(exercise),
        subject._adjudication_schema(exercise, ["Une réserve."]),
    ):
        grammar = llguidance.grammar_from(
            "json", json.dumps(_mlx_decoder_schema(schema))
        )
        assert not llguidance.LLMatcher.validate_grammar(grammar)


def test_holdout_sources_are_never_used_for_generation(tmp_path):
    import sqlite3

    path = tmp_path / "index.sqlite"
    make_index(path)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE sources SET split='holdout'")
    client = Client()
    with pytest.raises(ValueError):
        subject.generate(index_path=path, client=client, seed=42)
    assert not client.requests


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviews", []),
        ("checks", []),
        ("warnings", []),
        ("language_rubric", {}),
        ("references", []),
        ("teacher_review", "approved"),
    ],
)
def test_recomputed_hash_cannot_bypass_required_evidence(tmp_path, field, value):
    package = generate(tmp_path, Client())
    package[field] = value
    package["identity"]["content_sha256"] = subject._digest(
        {key: value for key, value in package.items() if key != "identity"}
    )
    with pytest.raises(ValueError):
        subject.validate_package(package)
