"""Direct family entry points publish complete sets, not early individual roles."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pymupdf as fitz
import pytest

from Backend.Core import document_publication, family_adapter, generation
from Backend.Core.family_contracts import ArtifactSpec, FamilyAdapter


def owned_adapter(label="new", *, supporting=None, filename="question.pdf"):
    def write(path, role):
        path.write_bytes(f"{label}:{role}".encode())

    return FamilyAdapter(
        id="owned",
        subject_label="Owned",
        backend_subject="owned",
        load_message="Load",
        build_message="Build",
        prompt_version="owned",
        load_syllabus=lambda _: object(),
        load_rule=lambda _: object(),
        build=lambda *_: label,
        stem=lambda *_: "owned",
        artifacts=lambda *_: (
            ArtifactSpec(
                "question", filename, lambda path: write(path, "question"), "Question"
            ),
            ArtifactSpec(
                "scheme", "scheme.pdf", lambda path: write(path, "scheme"), "Scheme"
            ),
        ),
        supporting_artifacts=supporting,
        output_order=("scheme", "question"),
    )


@pytest.fixture
def owned_io(monkeypatch):
    def render(destination, renderer, **_):
        renderer(destination)

    def package(assessment, path, **_):
        path.write_bytes(f"{assessment}:assessment".encode())

    monkeypatch.setattr(family_adapter, "render_pdf_atomically", render)
    monkeypatch.setattr(family_adapter, "validate_preview_pdf", lambda _: {})
    monkeypatch.setattr(family_adapter, "write_assessment_package", package)
    return package


def run_owned(adapter, output, progress=None):
    return family_adapter.run_family_adapter(
        adapter,
        paper="1",
        syllabus_path=output / "unused",
        output_dir=output,
        seed=1,
        dry_run=True,
        progress=progress,
    )


def old_files(output):
    output.mkdir(exist_ok=True)
    for name in ("question.pdf", "scheme.pdf", "support.txt", "owned-assessment.json"):
        (output / name).write_bytes(f"old:{name}".encode())
    return {p.name: p.read_bytes() for p in output.iterdir()}


def visible_files(output):
    return {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()}


@pytest.mark.parametrize("failure_type", [RuntimeError, InterruptedError])
def test_actual_direct_edexcel_late_render_failure_preserves_old_set(
    tmp_path, monkeypatch, failure_type
):
    root = Path(__file__).resolve().parents[1]
    resource = root / "Resources/economics/edexcel-a/generator"
    monkeypatch.syspath_prepend(str(resource))
    from pastpapergen import cli

    before = {}
    for suffix in ("question-paper", "source-booklet", "mark-scheme"):
        path = tmp_path / f"paper-2-{suffix}.pdf"
        with fitz.open() as document:
            document.new_page().insert_text((40, 80), f"Owned old {suffix}")
            document.save(path)
        before[path.name] = path.read_bytes()

    def fail_source(*_args):
        raise failure_type("owned later source-render failure")

    monkeypatch.setattr(cli, "render_source_booklet", fail_source)
    progress = []
    with pytest.raises(failure_type, match="owned later source-render failure"):
        cli.generate_package(
            paper="2",
            syllabus_path=resource / "data/syllabus_seed.json",
            output_dir=tmp_path,
            seed=270100,
            model="owned-offline-unused",
            ollama_url="http://127.0.0.1:1",
            dry_run=True,
            progress=progress.append,
        )
    assert {path.name: path.read_bytes() for path in tmp_path.glob("*.pdf")} == before
    assert "Done" not in progress
    assert not list(tmp_path.glob(".keldin-family-*"))


@pytest.mark.parametrize("populated", [False, True])
@pytest.mark.parametrize("stage", ["preview", "support", "assessment"])
def test_no_final_role_is_replaced_until_every_stage_succeeds(
    tmp_path, monkeypatch, owned_io, populated, stage
):
    before = old_files(tmp_path) if populated else {}

    def fail(*_args, **_kwargs):
        raise RuntimeError(f"owned {stage} failure")

    def support(_assessment, _context, _syllabus, _paper, output, _progress):
        (output / "support.txt").write_bytes(b"new:support")
        if stage == "support":
            fail()
        return {"support": output / "support.txt"}

    if stage == "preview":
        monkeypatch.setattr(family_adapter, "validate_preview_pdf", fail)
    elif stage == "assessment":
        monkeypatch.setattr(family_adapter, "write_assessment_package", fail)
    progress = []
    with pytest.raises(RuntimeError, match=f"owned {stage} failure"):
        run_owned(owned_adapter(supporting=support), tmp_path, progress.append)
    assert visible_files(tmp_path) == before
    assert not list(tmp_path.glob(".keldin-family-*"))
    assert "Done" not in progress


@pytest.mark.parametrize(
    "failure_type", [InterruptedError, generation.GenerationCancelled]
)
def test_precommit_cancellation_keeps_old_set_and_exception_identity(
    tmp_path, monkeypatch, owned_io, failure_type
):
    before = old_files(tmp_path)
    error = failure_type("owned cancellation")

    def cancel(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(family_adapter, "write_assessment_package", cancel)
    with pytest.raises(failure_type) as caught:
        run_owned(owned_adapter(), tmp_path)
    assert caught.value is error
    assert visible_files(tmp_path) == before
    assert not list(tmp_path.glob(".keldin-family-*"))
    assert generation.GenerationCancelled is document_publication.GenerationCancelled


def test_success_returns_final_paths_in_order_with_support_and_done_after_commit(
    tmp_path, owned_io
):
    stages = []

    def support(_assessment, _context, _syllabus, _paper, output, _progress):
        stages.append(output)
        path = output / "support.txt"
        path.write_bytes(b"new:support")
        return {"support": path}

    def progress(message):
        if message == "Done":
            assert (tmp_path / "question.pdf").read_bytes() == b"new:question"
            assert (
                tmp_path / "owned-assessment.json"
            ).read_bytes() == b"new:assessment"

    result = run_owned(owned_adapter(supporting=support), tmp_path, progress)
    assert list(result) == ["scheme", "question", "support", "assessment_package"]
    assert all(path.parent == tmp_path and path.is_file() for path in result.values())
    assert stages and stages[0].parent == tmp_path and not stages[0].exists()
    assert not list(tmp_path.glob(".keldin-family-*"))
    assert (tmp_path / ".keldin-checkpoints/publication.job.lock").is_file()


@pytest.mark.parametrize(
    "filename", ["../outside.pdf", "/outside.pdf", "sub/question.pdf"]
)
def test_artifact_path_traversal_refuses_before_any_renderer(
    tmp_path, monkeypatch, owned_io, filename
):
    before = old_files(tmp_path)
    monkeypatch.setattr(
        family_adapter,
        "render_pdf_atomically",
        lambda *_a, **_k: pytest.fail("unsafe renderer started"),
    )
    with pytest.raises(ValueError, match="direct children"):
        run_owned(owned_adapter(filename=filename), tmp_path)
    assert visible_files(tmp_path) == before


def test_support_output_cannot_escape_owned_staging(tmp_path, owned_io):
    output = tmp_path / "output"
    before = old_files(output)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"owned outside")

    def support(*_args):
        return {"support": outside}

    with pytest.raises(ValueError, match="inside their staging directory"):
        run_owned(owned_adapter(supporting=support), output)
    assert visible_files(output) == before
    assert outside.read_bytes() == b"owned outside"


def test_duplicate_destinations_keep_old_set(tmp_path, owned_io):
    before = old_files(tmp_path)
    with pytest.raises(OSError, match="filenames must be distinct"):
        run_owned(owned_adapter(filename="scheme.pdf"), tmp_path)
    assert visible_files(tmp_path) == before


@pytest.mark.parametrize("first_fails", [False, True])
def test_direct_adapters_share_one_commit_lease_but_prepare_in_parallel(
    tmp_path, monkeypatch, owned_io, first_fails
):
    first_written, release_first, second_prepared, second_entered = (
        Event(),
        Event(),
        Event(),
        Event(),
    )
    original_package = owned_io
    original_publish = document_publication.atomic_publish

    def package(assessment, path, **kwargs):
        original_package(assessment, path, **kwargs)
        if assessment == "second":
            second_prepared.set()

    def publish(source, destination):
        value = source.read_bytes()
        result = original_publish(source, destination)
        if value == b"first:scheme":
            first_written.set()
            assert release_first.wait(5)
            if first_fails:
                raise OSError("owned first-commit failure")
        if value.startswith(b"second:"):
            second_entered.set()
        return result

    monkeypatch.setattr(family_adapter, "write_assessment_package", package)
    monkeypatch.setattr(document_publication, "atomic_publish", publish)
    old_files(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(run_owned, owned_adapter("first"), tmp_path)
        try:
            assert first_written.wait(3)
            second = workers.submit(run_owned, owned_adapter("second"), tmp_path)
            assert second_prepared.wait(3), "rendering was blocked by the commit lease"
            assert not second_entered.wait(0.15), "two document sets interleaved"
        finally:
            release_first.set()
        if first_fails:
            with pytest.raises(OSError, match="owned first-commit failure"):
                first.result(timeout=3)
        else:
            first.result(timeout=3)
        second.result(timeout=3)
    assert (tmp_path / "question.pdf").read_bytes() == b"second:question"
    assert (tmp_path / "scheme.pdf").read_bytes() == b"second:scheme"
    assert (tmp_path / "owned-assessment.json").read_bytes() == b"second:assessment"
    assert not list(tmp_path.glob(".keldin-family-*"))


def test_distinct_roots_do_not_share_an_adapter_commit_lease(tmp_path, owned_io):
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    with document_publication.publication_lease(occupied):
        result = run_owned(owned_adapter(), tmp_path / "independent")
    assert all(path.is_file() for path in result.values())


@pytest.mark.parametrize("where", ["stage", "backup"])
def test_inner_cleanup_cancellation_cannot_reach_outer_publication(
    tmp_path, monkeypatch, owned_io, where
):
    output = tmp_path / "user-output"
    before = old_files(output)
    stage = tmp_path / "outer-stage"
    original_cleanup = family_adapter.TemporaryDirectory.cleanup
    original_rmtree = document_publication.shutil.rmtree
    error = generation.GenerationCancelled("owned inner cleanup cancellation")

    def cleanup(temporary):
        original_cleanup(temporary)
        raise error

    def rmtree(path, *args, **kwargs):
        if Path(path).name.startswith(".keldin-publish-"):
            raise error
        return original_rmtree(path, *args, **kwargs)

    if where == "stage":
        monkeypatch.setattr(family_adapter.TemporaryDirectory, "cleanup", cleanup)
    else:
        monkeypatch.setattr(document_publication.shutil, "rmtree", rmtree)
    progress = []
    with pytest.raises(generation.GenerationCancelled) as caught:
        result = run_owned(owned_adapter(), stage, progress.append)
        document_publication.publish_document_set(result, output)
    assert caught.value is error
    assert "Done" not in progress
    assert visible_files(output) == before
