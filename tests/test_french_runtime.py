from argparse import Namespace

import pytest


@pytest.mark.parametrize("failure", [None, "render", "cancel"])
def test_publication_is_complete_or_absent(tmp_path, monkeypatch, failure):
    import json
    from hashlib import sha256

    from Backend.Core.france import runtime
    from tests.test_nsi_pipeline import FrenchClient, make_index

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
        large_print=False,
    )
    monkeypatch.setattr(runtime, "model_identity", lambda *args: "fixture-digest")
    monkeypatch.setattr(runtime, "FrenchOllamaClient", lambda **kwargs: FrenchClient())
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
        import pymupdf

        with pymupdf.open(bundles[0] / "corrige.pdf") as pdf:
            # Six tiny fixture answers fit together; no orphan answer page.
            assert len(pdf) == 5
            assert "Exercice 1, question 6" in pdf[2].get_text()


def test_runtime_rejects_remote_ollama_without_explicit_consent():
    from Backend.Core.france.runtime import validate_endpoint

    validate_endpoint("http://127.0.0.1:11434", allow_remote=False)
    with pytest.raises(ValueError, match="distant"):
        validate_endpoint("https://school.example.fr", allow_remote=False)
    validate_endpoint("https://school.example.fr", allow_remote=True)
    with pytest.raises(ValueError):
        validate_endpoint("https://key:password@school.example.fr", allow_remote=True)


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
