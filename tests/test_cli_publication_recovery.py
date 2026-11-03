"""A failed CLI commit must not replace only part of an accepted paper set."""

from argparse import Namespace
from types import SimpleNamespace

import pytest

from Backend.Core import generation


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    stage = output / ".stage"
    stage.mkdir()
    paths = {
        "question_paper": stage / "question.pdf",
        "mark_scheme": stage / "scheme.pdf",
        "assessment_package": stage / "assessment.json",
    }
    for role, source in paths.items():
        source.write_bytes(f"new {role}".encode())
    manifest = stage / "manifest.json"
    manifest.write_bytes(b"new manifest")
    monkeypatch.setattr(generation, "validate_assessment_package", lambda *a, **k: {})
    monkeypatch.setattr(generation, "validate_package_novelty", lambda *a, **k: {})
    monkeypatch.setattr(generation, "conform_generated_documents", lambda *a: {})
    monkeypatch.setattr(generation, "validate_pdf_for_release", lambda *a, **k: {})
    monkeypatch.setattr(generation, "_write_package_manifest", lambda **k: manifest)
    args = Namespace(
        subject="fixture", paper="1", dry_run=False, provider="ollama", model="unused"
    )
    capability = SimpleNamespace(outputs_for=lambda _: tuple(paths))
    finalize = generation.finalize_generated_documents

    def finish():
        return finalize(
            args=args,
            capability=capability,
            staging_dir=stage,
            output_dir=output,
            paths=paths,
        )

    return output, paths, manifest, finish


def existing(output, paths, manifest):
    saved = {}
    for source in [*paths.values(), manifest]:
        destination = output / source.name
        saved[destination] = f"old {source.name}".encode()
        destination.write_bytes(saved[destination])
    return saved


@pytest.mark.parametrize("failure_at", [2, 4])
@pytest.mark.parametrize("previous", [False, True])
def test_failed_later_publication_restores_complete_previous_set(
    prepared, monkeypatch, failure_at, previous
):
    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest) if previous else {}
    unrelated = output / "unrelated.pdf"
    unrelated.write_bytes(b"keep unrelated")
    publish = generation._atomic_publish
    calls = 0

    def fail(source, destination):
        nonlocal calls
        calls += 1
        if calls == failure_at:
            raise OSError("injected publication failure")
        return publish(source, destination)

    monkeypatch.setattr(generation, "_atomic_publish", fail)
    with pytest.raises(OSError, match="injected publication failure"):
        finish()
    assert calls == failure_at
    for source in [*paths.values(), manifest]:
        destination = output / source.name
        if previous:
            assert destination.read_bytes() == saved[destination]
        else:
            assert not destination.exists()
    assert unrelated.read_bytes() == b"keep unrelated"
    assert not list(output.glob(".keldin-publish-*"))


@pytest.mark.parametrize("previous", [False, True])
def test_success_publishes_all_roles_without_touching_unrelated_files(
    prepared, previous
):
    output, paths, manifest, finish = prepared
    if previous:
        existing(output, paths, manifest)
    expected = {role: source.read_bytes() for role, source in paths.items()}
    expected["package_manifest"] = manifest.read_bytes()
    unrelated = output / "unrelated.json"
    unrelated.write_bytes(b"keep")
    result = finish()
    assert set(result) == set(expected)
    for role, destination in result.items():
        assert destination.parent == output
        assert destination.read_bytes() == expected[role]
    assert unrelated.read_bytes() == b"keep"
    assert not list(output.glob(".keldin-publish-*"))


def test_directory_destination_refuses_before_replacing_any_old_file(prepared):
    output, paths, _manifest, finish = prepared
    question = output / paths["question_paper"].name
    question.write_bytes(b"old question")
    (output / paths["mark_scheme"].name).mkdir()
    with pytest.raises(OSError):
        finish()
    assert question.read_bytes() == b"old question"


def test_symlink_destination_refuses_without_touching_its_target(prepared):
    output, paths, _manifest, finish = prepared
    target = output / "unrelated.txt"
    target.write_bytes(b"keep target")
    destination = output / paths["mark_scheme"].name
    destination.symlink_to(target)
    with pytest.raises(OSError, match="non-file output"):
        finish()
    assert destination.is_symlink()
    assert target.read_bytes() == b"keep target"
    assert not (output / paths["question_paper"].name).exists()


def test_backup_failure_happens_before_any_destination_write(prepared, monkeypatch):
    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest)
    calls = 0
    link = generation.os.link

    def fail_second_backup(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("hard links unavailable")
        return link(source, destination)

    monkeypatch.setattr(generation.os, "link", fail_second_backup)
    monkeypatch.setattr(
        generation,
        "_atomic_publish",
        lambda *args: pytest.fail("publication before backup completion"),
    )
    with pytest.raises(OSError, match="hard links unavailable"):
        finish()
    assert all(destination.read_bytes() == data for destination, data in saved.items())
    assert not list(output.glob(".keldin-publish-*"))


@pytest.mark.parametrize("after_write", [False, True])
def test_cancellation_restores_all_attempted_destinations(
    prepared, monkeypatch, after_write
):
    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest)
    publish = generation._atomic_publish
    calls = 0

    def cancel(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            if after_write:
                publish(source, destination)
            raise generation.GenerationCancelled
        return publish(source, destination)

    monkeypatch.setattr(generation, "_atomic_publish", cancel)
    with pytest.raises(generation.GenerationCancelled):
        finish()
    assert all(destination.read_bytes() == data for destination, data in saved.items())
    assert not list(output.glob(".keldin-publish-*"))


def test_failed_rollback_retains_named_backup_outside_render_staging(
    prepared, monkeypatch
):
    import shutil

    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest)
    replace = generation.os.replace

    def fail(source, destination):
        if source.parent.name.startswith(".keldin-publish-"):
            raise OSError("restoration refused")
        if destination.name == paths["mark_scheme"].name:
            raise OSError("publication refused")
        return replace(source, destination)

    monkeypatch.setattr(generation.os, "replace", fail)
    with pytest.raises(RuntimeError, match="Recovery copies remain in") as caught:
        finish()
    recovery = next(output.glob(".keldin-publish-*"))
    assert str(recovery) in str(caught.value)
    # handle_generate removes render staging on failure, not recovery siblings.
    shutil.rmtree(manifest.parent)
    for destination, data in saved.items():
        assert (recovery / destination.name).read_bytes() == data


def test_backup_cleanup_failure_does_not_rollback_success(prepared, monkeypatch):
    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest)
    cleanup_calls = []

    def unavailable_cleanup(directory, *, ignore_errors):
        assert ignore_errors
        cleanup_calls.append(directory)
        # shutil.rmtree(ignore_errors=True) can leave files when cleanup is denied.

    monkeypatch.setattr(generation.shutil, "rmtree", unavailable_cleanup)
    result = finish()
    assert len(cleanup_calls) == 1
    for role, destination in result.items():
        expected = (
            b"new manifest" if role == "package_manifest" else f"new {role}".encode()
        )
        assert destination.read_bytes() == expected
    for destination, data in saved.items():
        assert (cleanup_calls[0] / destination.name).read_bytes() == data


def test_cleanup_cancellation_after_commit_still_reports_completion(
    prepared, monkeypatch, capsys
):
    import json

    output, paths, manifest, finish = prepared
    existing(output, paths, manifest)
    cleanup = generation.shutil.rmtree

    def cancelled_cleanup(directory, **kwargs):
        if directory.name.startswith(".keldin-publish-"):
            raise generation.GenerationCancelled
        return cleanup(directory, **kwargs)

    monkeypatch.setattr(generation.shutil, "rmtree", cancelled_cleanup)
    monkeypatch.setattr(generation, "_invoke_plugin", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        generation, "finalize_generated_documents", lambda **kwargs: finish()
    )
    request = Namespace(
        output=str(output),
        api_key="",
        model="fixture",
        subject="economics",
        paper="1",
        provider="ollama",
        dry_run=False,
        seed=123,
    )
    assert generation.handle_generate(request) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["type"] == "done"
    assert not any(event.get("stage") == "cancel" for event in events)
    notices = [event for event in events if event.get("stage") == "publication_cleanup"]
    assert len(notices) == 1
    assert events.index(notices[0]) < next(
        index for index, event in enumerate(events) if event["type"] == "file"
    )
    for source in [*paths.values(), manifest]:
        expected = (
            b"new manifest"
            if source == manifest
            else next(
                f"new {role}".encode() for role, path in paths.items() if path == source
            )
        )
        assert (output / source.name).read_bytes() == expected
    recovery = next(output.glob(".keldin-publish-*"))
    assert str(recovery) in notices[0]["message"]
    assert (recovery / manifest.name).read_bytes() == b"old manifest.json"


def test_cancellation_during_backup_is_not_postcommit_maintenance(
    prepared, monkeypatch
):
    output, paths, manifest, finish = prepared
    saved = existing(output, paths, manifest)

    def cancelled_backup(*args):
        raise generation.GenerationCancelled

    monkeypatch.setattr(generation.os, "link", cancelled_backup)
    with pytest.raises(generation.GenerationCancelled):
        finish()
    assert all(path.read_bytes() == data for path, data in saved.items())
    assert not list(output.glob(".keldin-publish-*"))
