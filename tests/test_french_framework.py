import pymupdf
import pytest


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("les réseaux.", "Thème de l'exercice : « les réseaux »."),
        (
            "Parcours d'un réseau et recherche dans un arbre",
            "Thème de l'exercice : « Parcours d'un réseau et recherche dans un arbre ».",
        ),
        (
            "Étude d'un registre d'incidents",
            "Thème de l'exercice : « Étude d'un registre d'incidents ».",
        ),
        (
            "Liaisons d'une station",
            "Thème de l'exercice : « Liaisons d'une station ».",
        ),
        ("Cet exercice porte sur Python", "Cet exercice porte sur Python."),
        ("On étudie les réseaux.", "Thème de l'exercice : « On étudie les réseaux »."),
        ("Le réseau est saturé.", "Thème de l'exercice : « Le réseau est saturé »."),
    ],
)
def test_french_exercise_scope_reads_naturally_for_titles_and_sentences(title, expected):
    from Backend.Core.france.rendering import exercise_scope_text

    assert exercise_scope_text(title) == expected


def test_code_listings_never_silently_wrap_or_change_indentation():
    from reportlab.lib.styles import ParagraphStyle

    from Backend.Core.france.rendering import code_listing

    style = ParagraphStyle("code", fontName="Courier", fontSize=12)
    source = 'if True:\n    message = "bonjour"\n    resultat = message'
    listing = code_listing(source, style, 450)
    assert listing.lines == source.splitlines()
    with pytest.raises(ValueError, match="ligne de code"):
        code_listing('message = "' + "a" * 100 + '"', style, 450)


def test_framework_registry_does_not_add_france_as_a_uk_board():
    from Backend.Core.generator_registry import assessment_framework, generator_subjects

    assert "fr_nsi" not in generator_subjects()
    framework = assessment_framework("fr-bac-general-nsi-written-2027")
    assert framework.context.country == "FR"
    with pytest.raises(ValueError):
        assessment_framework("unknown")


def test_new_command_keeps_legacy_generate_arguments():
    from Backend.Core.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "generate-assessment",
            "--assessment",
            "fr-bac-general-nsi-written-2027",
            "--reference-index",
            "/tmp/references.sqlite",
            "--seed",
            "5",
        ]
    )
    assert args.provider == "ollama"
    assert args.assessment == "fr-bac-general-nsi-written-2027"
    old = parser.parse_args(
        ["generate", "--subject", "computer_science", "--paper", "1"]
    )
    assert old.paper == "1"


def test_render_transaction_sets_french_language(tmp_path):
    from reportlab.pdfgen.canvas import Canvas

    from Backend.Core.render_transaction import render_pdf_atomically

    def render(path):
        canvas = Canvas(str(path))
        canvas.drawString(50, 700, "Bonjour")
        canvas.save()

    destination = tmp_path / "test.pdf"
    render_pdf_atomically(destination, render, role="sujet", language="fr-FR")
    with pymupdf.open(destination) as pdf:
        assert pdf.xref_get_key(pdf.pdf_catalog(), "Lang")[1] == "fr-FR"


def test_french_pdf_has_real_credit_language_and_no_official_claim(tmp_path):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment

    exercises = []
    for number in range(1, 4):
        exercises.append(
            NSIExercise.model_validate(
                {
                    "id": str(number),
                    "title": "Étude d'un réseau",
                    "context": "Un établissement étudie ses connexions et leurs débits.",
                    "topics": ["architectures-reseaux"],
                    "minutes": 60 if number < 3 else 70,
                    "target_points": "6",
                    "questions": [
                        {
                            "id": str(i),
                            "prompt": "Expliquer précisément la méthode employée.",
                            "points": "1.5",
                            "answer": "La méthode utilise les connexions indiquées.",
                                "marking": [
                                {
                                    "points": "1.5",
                                    "criterion": "Méthode justifiée dans ce contexte.",
                                    }
                                ],
                                "curriculum_codes": ["ASR-ROUTAGE"],
                                "operation": ("apply", "analyse", "design", "justify")[
                                    i - 1
                                ],
                                "difficulty": (2, 3, 4, 4)[i - 1],
                                "estimated_minutes": (
                                    (15, 15, 15, 15)
                                    if number < 3
                                    else (18, 18, 17, 17)
                                )[i - 1],
                            }
                        for i in range(1, 5)
                    ],
                }
            )
        )
    for large in (False, True):
        output = tmp_path / f"subject-{large}.pdf"
        render_assessment(output, exercises, correction=False, large_print=large)
        with pymupdf.open(output) as pdf:
            text = " ".join(" ".join(page.get_text() for page in pdf).split())
            assert "non officiel" in text
            assert "18 points" in text and "2 points" in text
            assert "ÉPREUVE" in text
            assert "Méthode justifiée" not in text
            for page in pdf:
                for word in page.get_text("words"):
                    assert word[0] >= 0 and word[2] <= page.rect.width
                    assert word[1] >= 0 and word[3] <= page.rect.height

        correction = tmp_path / f"correction-{large}.pdf"
        render_assessment(correction, exercises, correction=True, large_print=large)
        with pymupdf.open(correction) as pdf:
            cover = " ".join(pdf[0].get_text().split())
            assert "CORRIGÉ PROPOSÉ ET BARÈME INDICATIF" in cover
            assert "corrigé proposé" in pdf.metadata["title"].lower()
            assert "enseignant" in cover
            assert "Dès que ce sujet vous est remis" not in cover
            assert "Le candidat traite les trois exercices" not in cover
            assert "L’usage de la calculatrice" not in cover
            for word in pdf[0].get_text("words"):
                assert 0 <= word[0] < word[2] <= pdf[0].rect.width
                assert 0 <= word[1] < word[3] <= pdf[0].rect.height


def test_french_pdf_renders_structured_tables_and_graphs_as_vectors(tmp_path):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment

    raw = {
        "id": "1",
        "title": "Routage dans un réseau régional",
        "context": "Un réseau relie trois établissements situés en Occitanie.",
        "topics": ["architectures-reseaux", "algorithmique"],
        "minutes": 60,
        "target_points": "6",
        "materials": [
            {
                "kind": "weighted_graph",
                "id": "reseau",
                "title": "Latences entre établissements",
                "nodes": ["Albi", "Nîmes", "Sète"],
                "edges": [["Albi", "Nîmes", 4], ["Nîmes", "Sète", 3]],
                "directed": False,
            },
            {
                "kind": "table",
                "id": "capacites",
                "title": "Capacités disponibles",
                "columns": ["liaison", "débit"],
                "rows": [["Albi-Nîmes", "100"], ["Nîmes-Sète", "80"]],
            },
        ],
        "questions": [
            {
                "id": str(i),
                "prompt": "Justifier précisément le résultat obtenu.",
                "points": "1.5",
                "answer": "Le résultat est justifié à partir des données.",
                "marking": [
                    {"points": "1.5", "criterion": "Résultat et justification."}
                ],
                "material_ids": ["reseau"] if i == 1 else [],
                "curriculum_codes": [
                    "ASR-ROUTAGE" if i % 2 else "ALG-GRAPHES"
                ],
                "operation": ("apply", "analyse", "design", "justify")[i - 1],
                "difficulty": (2, 3, 4, 4)[i - 1],
                "estimated_minutes": 15,
                "verification": {"kind": "human"},
            }
            for i in range(1, 5)
        ],
    }
    output = tmp_path / "structured.pdf"
    render_assessment(
        output, [NSIExercise.model_validate(raw)], correction=False, large_print=False
    )
    with pymupdf.open(output) as pdf:
        text = " ".join(page.get_text() for page in pdf)
        assert "Latences entre établissements" in text
        assert "Capacités disponibles" in text
        assert "Albi" in text and "Nîmes" in text and "Sète" in text
        assert all(not page.get_images(full=True) for page in pdf)


def test_french_pdf_uses_measured_bac_page_geometry(tmp_path):
    """Keep the provisional 2027 profile close to the measured 2026 subject."""
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment

    exercise = NSIExercise.model_validate(
        {
            "id": "1",
            "title": "Les réseaux, le routage et la sécurisation des communications",
            "context": "Un lycée relie plusieurs sites par un réseau informatique.",
            "topics": ["architectures-reseaux"],
            "minutes": 60,
            "target_points": "6",
            "questions": [
                {
                    "id": str(index),
                    "prompt": "Justifier précisément la réponse à partir du contexte proposé.",
                    "points": "1.5",
                    "answer": "La réponse s'appuie sur les données du réseau.",
                    "marking": [
                        {"points": "1.5", "criterion": "Réponse contextualisée et justifiée."}
                    ],
                    "curriculum_codes": ["ASR-ROUTAGE"],
                    "operation": ("apply", "analyse", "design", "justify")[index - 1],
                    "difficulty": (2, 3, 4, 4)[index - 1],
                    "estimated_minutes": 15,
                }
                for index in range(1, 5)
            ],
        }
    )
    output = tmp_path / "measured-layout.pdf"
    render_assessment(output, [exercise], correction=False, large_print=False)

    with pymupdf.open(output) as pdf:
        cover_spans = [
            span
            for block in pdf[0].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span["text"].strip()
        ]
        by_text = {span["text"].strip(): span for span in cover_spans}
        assert by_text["BACCALAURÉAT GÉNÉRAL"]["size"] == pytest.approx(20, abs=0.2)
        assert 78 <= by_text["BACCALAURÉAT GÉNÉRAL"]["bbox"][1] <= 86
        assert by_text["SESSION 2027"]["size"] == pytest.approx(14, abs=0.2)
        assert 200 <= by_text["SESSION 2027"]["bbox"][1] <= 210
        assert by_text["NUMÉRIQUE ET SCIENCES INFORMATIQUES"]["size"] == pytest.approx(
            20, abs=0.2
        )
        assert 295 <= by_text["NUMÉRIQUE ET SCIENCES INFORMATIQUES"]["bbox"][1] <= 305
        assert 440 <= by_text["Durée de l’épreuve : 3 heures 30"]["bbox"][1] <= 455
        calculator = by_text["L’usage de la calculatrice n’est pas autorisé."]
        assert calculator["flags"] & 2
        assert 510 <= calculator["bbox"][1] <= 525

        exercise_spans = [
            span
            for block in pdf[1].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span["text"].strip()
        ]
        exercise_by_text = {span["text"].strip(): span for span in exercise_spans}
        heading = exercise_by_text["Exercice 1 (6 points)"]
        assert heading["size"] == pytest.approx(14, abs=0.2)
        assert 67 <= heading["bbox"][1] <= 78
        scope = next(
            span
            for span in exercise_spans
            if span["text"].startswith("Thème de l'exercice")
        )
        assert scope["flags"] & 2
        assert scope["text"].startswith("Thème de l'exercice : « Les réseaux")
        assert 96 <= scope["bbox"][1] <= 112
        number = exercise_by_text["1."]
        assert 80 <= number["bbox"][0] <= 86
        prompt = next(
            span
            for span in exercise_spans
            if span["text"].startswith("Justifier précisément")
        )
        assert 104 <= prompt["bbox"][0] <= 110

    correction = tmp_path / "measured-correction.pdf"
    render_assessment(correction, [exercise], correction=True, large_print=False)
    with pymupdf.open(correction) as pdf:
        text = " ".join(page.get_text() for page in pdf)
        assert text.count("Consignes générales de correction") == 1
        assert "Exercice 1, question" not in text
        assert text.count("Réponse attendue") == 4
        assert text.count("Barème indicatif") >= 4
