from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools import calibrate_student_responses as calibration
from tools import live_process


@pytest.mark.parametrize(
    "timeout",
    [float("nan"), float("inf"), -float("inf"), 0, -1, True, False, "5", None],
)
def test_invalid_timeout_refuses_before_log_mutation_or_process_spawn(
    tmp_path, monkeypatch, timeout
):
    log = tmp_path / "events.jsonl"
    log.write_text("retained")
    monkeypatch.setattr(
        live_process.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("must not spawn"),
    )
    with pytest.raises(ValueError, match="timeout"):
        live_process.run_backend(
            ["fake"], cwd=tmp_path, run_dir=tmp_path, timeout_seconds=timeout
        )
    assert log.read_text() == "retained"
    assert not (tmp_path / "stderr.log").exists()


@pytest.mark.parametrize("timeout", [1, 0.25])
def test_positive_integer_and_fractional_timeouts_keep_launch_failure_contract(
    tmp_path, monkeypatch, timeout
):
    def missing(*_args, **_kwargs):
        raise FileNotFoundError("fake backend unavailable")

    monkeypatch.setattr(live_process.subprocess, "Popen", missing)
    result = live_process.run_backend(
        ["fake"], cwd=tmp_path, run_dir=tmp_path, timeout_seconds=timeout
    )
    assert result.return_code == 127
    assert result.timed_out is False
    assert "fake backend unavailable" in result.stderr


@pytest.mark.parametrize(
    "arguments",
    [
        ["--secure-store", "store", "--delete"],
        ["--secure-store", "store", "--export-encrypted", "export"],
        [
            "--secure-store",
            "store",
            "--dataset-id",
            "x",
            "--delete",
            "--export-encrypted",
            "export",
        ],
        ["responses", "--secure-store", "store", "--dataset-id", "x"],
        ["--secure-store", "store", "--dataset-id", "x", "--metadata", "metadata"],
        ["--secure-store", "store", "--dataset-id", "x", "--consents", "consents"],
        [
            "--secure-store",
            "store",
            "--dataset-id",
            "x",
            "--delete",
            "--review",
            "missing-review",
        ],
        [
            "--secure-store",
            "store",
            "--dataset-id",
            "x",
            "--export-encrypted",
            "export",
            "--output",
            "report",
        ],
        ["--secure-store", "store", "--dataset-id", " "],
        ["--delete"],
        ["--dataset-id", "x"],
        [
            "responses",
            "--secure-store",
            "store",
            "--delete",
            "--metadata",
            "metadata",
            "--consents",
            "consents",
        ],
    ],
)
def test_invalid_calibration_actions_refuse_before_keys_stores_or_data(
    arguments, monkeypatch
):
    monkeypatch.setattr(sys, "argv", ["calibration", *arguments])
    monkeypatch.setattr(
        calibration, "_load_key", lambda *_a, **_k: pytest.fail("must not load key")
    )
    monkeypatch.setattr(
        calibration,
        "CalibrationStore",
        lambda *_a, **_k: pytest.fail("must not construct store"),
    )
    monkeypatch.setattr(
        Path, "read_text", lambda *_a, **_k: pytest.fail("must not read data")
    )
    with pytest.raises(SystemExit) as error:
        calibration.main()
    assert error.value.code == 2


@pytest.mark.parametrize("action", ["delete", "export"])
def test_valid_secure_actions_call_only_requested_fake_store_operation(
    action, monkeypatch
):
    calls = []

    class Store:
        def __init__(self, path, *, key):
            calls.append(("store", path, key))

        def delete(self, dataset):
            calls.append(("delete", dataset))
            return True

        def export_encrypted(self, dataset, destination):
            calls.append(("export", dataset, destination))
            return destination

    args = ["--secure-store", "store", "--dataset-id", "x"]
    args += ["--delete"] if action == "delete" else ["--export-encrypted", "export"]
    monkeypatch.setattr(sys, "argv", ["calibration", *args])
    monkeypatch.setattr(calibration, "_load_key", lambda *_a, **_k: b"fake-key")
    monkeypatch.setattr(calibration, "CalibrationStore", Store)
    assert calibration.main() == 0
    assert calls[1][0] == action
    assert len(calls) == 2


@pytest.mark.parametrize("import_new", [False, True])
def test_valid_secure_import_and_existing_aggregation_remain_available(
    import_new, monkeypatch
):
    calls = []

    class Store:
        def __init__(self, *_args, **_kwargs):
            pass

        def import_csv(self, path, *, metadata, consents):
            calls.append(("import", path))
            return "new"

        def aggregate(self, dataset, **_kwargs):
            calls.append(("aggregate", dataset))
            return {
                "sample": {"candidates": 1, "items": 1},
                "difficulty_independently_verified": False,
                "checks": {},
            }

    args = ["--secure-store", "store"]
    args += (
        ["responses", "--metadata", "metadata", "--consents", "consents"]
        if import_new
        else ["--dataset-id", "existing"]
    )
    monkeypatch.setattr(sys, "argv", ["calibration", *args])
    monkeypatch.setattr(calibration, "_load_key", lambda *_a, **_k: b"fake-key")
    monkeypatch.setattr(calibration, "CalibrationStore", Store)
    monkeypatch.setattr(calibration, "CalibrationMetadata", lambda **_kwargs: object())
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, **_kwargs: "[]" if str(path) == "consents" else "{}",
    )
    assert calibration.main() == 2
    expected = (
        [("import", Path("responses")), ("aggregate", "new")]
        if import_new
        else [("aggregate", "existing")]
    )
    assert calls == expected
