import pymupdf
import pytest


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
