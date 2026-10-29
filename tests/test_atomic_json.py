import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest

from tools.atomic_json import write_json_atomically
from tools.live_generation_matrix import _write_run_qualification_manifest


def test_atomic_json_preserves_previous_document_on_replace_failure(tmp_path: Path):
    path = tmp_path / "matrix-result.json"
    previous = b'{"passed": false}\n'
    path.write_bytes(previous)
    with (
        patch("tools.atomic_json.os.replace", side_effect=OSError("disk unavailable")),
        pytest.raises(OSError, match="disk unavailable"),
    ):
        write_json_atomically(path, {"passed": True})
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_json_uses_unique_sibling_files_and_complete_documents(tmp_path: Path):
    path = tmp_path / "new" / "result.json"
    siblings = []

    def inspect(source, destination):
        source = Path(source)
        assert source.parent == path.parent
        assert source != path
        assert json.loads(source.read_text(encoding="utf-8"))["label"] == "élève"
        siblings.append(source)
        os_replace(source, destination)

    os_replace = os.replace
    with patch("tools.atomic_json.os.replace", side_effect=inspect):
        write_json_atomically(path, {"label": "élève"})
        write_json_atomically(path, {"label": "élève"})
    assert len(set(siblings)) == 2
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert list(path.parent.iterdir()) == [path]


def test_atomic_json_serialization_failure_leaves_evidence_untouched(tmp_path: Path):
    path = tmp_path / "result.json"
    path.write_bytes(b'{"passed": false}\n')
    with pytest.raises(TypeError):
        write_json_atomically(path, {"invalid": object()})
    assert path.read_bytes() == b'{"passed": false}\n'
    assert list(tmp_path.iterdir()) == [path]


def test_live_manifest_interruption_keeps_previous_resume_document(tmp_path: Path):
    path = tmp_path / "qualification-run-manifest.json"
    previous = b'{"complete": false}\n'
    path.write_bytes(previous)
    with (
        patch("tools.atomic_json.os.replace", side_effect=OSError("interrupted")),
        pytest.raises(OSError, match="interrupted"),
    ):
        _write_run_qualification_manifest(
            output_root=tmp_path,
            report={
                "results": [],
                "summary": {},
                "complete": True,
                "expected_jobs": 0,
            },
            model="test",
            provider="ollama",
            base_seed=270100,
        )
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_json_flush_failure_keeps_previous_document(tmp_path: Path):
    path = tmp_path / "result.json"
    path.write_bytes(b'{"passed": false}\n')
    with (
        patch("tools.atomic_json.os.fsync", side_effect=OSError("flush failed")),
        pytest.raises(OSError, match="flush failed"),
    ):
        write_json_atomically(path, {"passed": True})
    assert path.read_bytes() == b'{"passed": false}\n'
    assert list(tmp_path.iterdir()) == [path]


def test_overlapping_atomic_json_writers_do_not_share_temporary_files(tmp_path: Path):
    path = tmp_path / "result.json"
    barrier = Barrier(2)
    os_replace = os.replace

    def synchronized_replace(source, destination):
        barrier.wait(timeout=5)
        os_replace(source, destination)

    with (
        patch("tools.atomic_json.os.replace", side_effect=synchronized_replace),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        futures = [
            pool.submit(write_json_atomically, path, {"writer": index})
            for index in range(2)
        ]
        for future in futures:
            future.result(timeout=10)
    assert json.loads(path.read_text(encoding="utf-8")) in [
        {"writer": 0},
        {"writer": 1},
    ]
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_json_does_not_unlink_after_committed_replace(tmp_path: Path):
    path = tmp_path / "result.json"
    with patch.object(Path, "unlink", side_effect=PermissionError("cleanup denied")):
        write_json_atomically(path, {"passed": True})
    assert json.loads(path.read_text()) == {"passed": True}
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("operation", ["fsync", "replace"])
@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt, SystemExit])
def test_atomic_json_preserves_primary_failure_when_cleanup_fails(
    tmp_path, operation, failure
):
    path = tmp_path / "result.json"
    path.write_bytes(b"previous")
    primary = failure("publication failed")
    with (
        patch(f"tools.atomic_json.os.{operation}", side_effect=primary),
        patch.object(Path, "unlink", side_effect=PermissionError("cleanup denied")),
        pytest.raises(failure) as caught,
    ):
        write_json_atomically(path, {"passed": True})
    assert caught.value is primary
    assert "cleanup denied" in " ".join(caught.value.__notes__)
    assert path.read_bytes() == b"previous"
    assert len(list(tmp_path.glob(".result.json.*.tmp"))) == 1


def test_atomic_json_closes_descriptor_when_stream_construction_fails(tmp_path):
    descriptors = []

    def fail_open(descriptor, *_args, **_kwargs):
        descriptors.append(descriptor)
        raise OSError("stream construction failed")

    with (
        patch("tools.atomic_json.os.fdopen", side_effect=fail_open),
        pytest.raises(OSError, match="stream construction failed"),
    ):
        write_json_atomically(tmp_path / "result.json", {})
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(descriptors[0])
    assert list(tmp_path.iterdir()) == []
