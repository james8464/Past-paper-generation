# Renaming storage must preserve prior files without reviving stale settings.


from hashlib import sha256

import pytest

from Backend.Core.legacy_migration import (
    copy_missing_tree,
    environment_value,
    output_directory,
)


def test_rebrand_preserves_the_historical_v32_origin_digest():
    from Backend.Core.france.provider import ApplicationOwnedFrenchClient

    expected = sha256(b"Paper Creator application-owned French cases v32").hexdigest()
    assert ApplicationOwnedFrenchClient.model_digest == expected


def test_environment_alias_is_read_only_and_new_value_takes_precedence():
    values = {"PAPER_CREATOR_API_KEY": "old"}
    assert environment_value("KELDIN_API_KEY", environment=values) == "old"
    values["KELDIN_API_KEY"] = ""
    assert environment_value("KELDIN_API_KEY", environment=values) == ""
    assert (
        environment_value("KELDIN_ROOT", "fallback", environment=values) == "fallback"
    )
    assert values["PAPER_CREATOR_API_KEY"] == "old"
    assert environment_value("KELDIN_APP_VERSION", None, environment={}) is None


def test_checkpoint_import_merges_missing_files_without_changing_originals(tmp_path):
    old = tmp_path / ".papercreator-checkpoints"
    old.mkdir()
    (old / "accepted.json").write_text('{"items": {}}')
    (old / "conflict.json").write_text("old")
    new = tmp_path / ".keldin-checkpoints"
    new.mkdir()
    (new / "conflict.json").write_text("new")
    assert output_directory(tmp_path, new.name) == new
    assert (new / "accepted.json").read_bytes() == (old / "accepted.json").read_bytes()
    assert (new / "conflict.json").read_text() == "new"
    assert (old / "conflict.json").read_text() == "old"
    output_directory(tmp_path, new.name)
    assert (new / "conflict.json").read_text() == "new"
    (new / "accepted.json").unlink()
    output_directory(tmp_path, new.name)
    assert not (new / "accepted.json").exists()


def test_copy_does_not_follow_source_or_destination_symlinks(tmp_path):
    source = tmp_path / "old"
    source.mkdir()
    secret = tmp_path / "outside"
    secret.write_text("private")
    (source / "link").symlink_to(secret)
    target = tmp_path / "new"
    copy_missing_tree(source, target)
    assert not (target / "link").exists()
    (source / "ordinary").write_text("data")
    (target / "ordinary").symlink_to(secret)
    copy_missing_tree(source, target)
    assert secret.read_text() == "private"
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(OSError, match="symbolic link"):
        copy_missing_tree(source, alias)


def test_failed_import_does_not_leave_a_partial_checkpoint(tmp_path, monkeypatch):
    source = tmp_path / "old"
    source.mkdir()
    (source / "accepted.json").write_text("complete")
    target = tmp_path / "new"

    def interrupted(original, copied):
        copied.write(b"partial")
        raise OSError("interrupted")

    monkeypatch.setattr("Backend.Core.legacy_migration.shutil.copyfileobj", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        copy_missing_tree(source, target)
    assert list(target.iterdir()) == []
    assert (source / "accepted.json").read_text() == "complete"


def test_generation_date_accepts_the_legacy_setting(monkeypatch):
    from Backend.Core.generation_date import generation_date

    monkeypatch.delenv("KELDIN_GENERATED_ON", raising=False)
    monkeypatch.setenv("PAPER_CREATOR_GENERATED_ON", "2026-10-28")
    assert generation_date().isoformat() == "2026-10-28"
    monkeypatch.setenv("KELDIN_GENERATED_ON", "2026-10-29")
    assert generation_date().isoformat() == "2026-10-29"


def test_copy_rejects_a_destination_inside_the_source_tree(tmp_path):
    source = tmp_path / "old"
    source.mkdir()
    with pytest.raises(OSError, match="outside"):
        copy_missing_tree(source, source / "nested")
    assert not (source / "nested").exists()
