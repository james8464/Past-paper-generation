from argparse import Namespace

import pytest


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
    from Backend.Core.france.runtime import network_pdf_contract_version

    assert network_pdf_contract_version("fr-nsi-written-2027-v15") == "v15"
    assert network_pdf_contract_version("fr-nsi-written-2027-v14") == "v14"
    with pytest.raises(ValueError, match="Version"):
        network_pdf_contract_version("fr-nsi-written-2027-v13")


@pytest.mark.parametrize("large_print", [False, True])
def test_runtime_publishes_v15_network_depth_with_locked_pdf_facts(
    tmp_path, monkeypatch, large_print
):
    import json

    import pymupdf

    from Backend.Core.france import runtime
    from Backend.Core.france.network_depth_contract import build_network_depth_contract
    from Backend.Core.france.nsi import NSIExercise
    from tests.test_nsi_pipeline import ControlledNetworkDepthFrenchClient, make_index

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime, "FrenchOllamaClient", lambda **_: ControlledNetworkDepthFrenchClient()
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
    assert package["identity"]["prompt_version"] == "fr-nsi-written-2027-v15"
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
