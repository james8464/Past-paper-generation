from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "Resources/economics/edexcel-a/generator"


def test_new_cli_exports_the_existing_callable_objects():
    old = importlib.import_module("pastpapergen.cli")
    new = importlib.import_module("keldin_edexcel.cli")
    assert new.main is old.main
    assert new.generate_package is old.generate_package
    assert (
        importlib.import_module("keldin_edexcel").__version__
        == importlib.import_module("pastpapergen").__version__
    )


def test_both_console_entrypoints_dispatch_to_same_existing_generator(
    tmp_path, monkeypatch
):
    old = importlib.import_module("pastpapergen.cli")
    new = importlib.import_module("keldin_edexcel.cli")
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return {
            role: tmp_path / role
            for role in ("question_paper", "source_booklet", "mark_scheme")
        }

    monkeypatch.setattr(old, "generate_package", generate)
    arguments = [
        "--paper",
        "1",
        "--seed",
        "270100",
        "--dry-run",
        "--out",
        str(tmp_path),
    ]
    assert old.main(arguments) == new.main(arguments) == 0
    assert calls[0] == calls[1]
    assert calls[0]["dry_run"] is True


def test_packaging_and_frozen_collection_preserve_both_surfaces():
    configuration = tomllib.loads((GENERATOR / "pyproject.toml").read_text())
    assert configuration["project"]["name"] == "pastpapergen"
    assert configuration["project"]["scripts"] == {
        "pastpapergen": "pastpapergen.cli:main",
        "keldin-edexcel": "keldin_edexcel.cli:main",
    }
    assert set(configuration["tool"]["setuptools"]["packages"]["find"]["include"]) == {
        "pastpapergen*",
        "keldin_edexcel*",
    }
    registry = json.loads((ROOT / "Resources/generator-registry.json").read_text())
    family = next(
        row
        for row in registry["families"]
        if row["id"] == "pearson-edexcel/economics-a-2015"
    )
    assert family["package"] == "pastpapergen"
    assert family["entry_point"] == "pastpapergen.cli:generate_package"
    source = (ROOT / "macOS/scripts/build_backend.sh").read_text()
    assert "--hidden-import keldin_edexcel.cli" in source
    assert 'find "$generator_root/$package"' in source


def test_wheel_backend_is_an_explicit_test_dependency():
    requirements = {}
    for raw in (ROOT / "requirements-test.txt").read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            requirement = Requirement(line)
            requirements[requirement.name] = requirement
    assert "setuptools" in requirements
    assert requirements["setuptools"].specifier


def test_wheel_contains_facade_and_legacy_implementation_without_installing(tmp_path):
    copied = tmp_path / "generator"
    shutil.copytree(
        GENERATOR,
        copied,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.egg-info", "build", ".pytest_cache"
        ),
    )
    built = subprocess.run(
        [
            sys.executable,
            "-c",
            "from setuptools.build_meta import build_wheel; build_wheel('dist')",
        ],
        cwd=copied,
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, (
        f"Wheel build failed (exit {built.returncode}).\n"
        f"stdout:\n{built.stdout}\nstderr:\n{built.stderr}"
    )
    (wheel,) = (copied / "dist").glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert {
            "keldin_edexcel/__init__.py",
            "keldin_edexcel/cli.py",
            "keldin_edexcel/__main__.py",
            "pastpapergen/models.py",
            "pastpapergen/cli.py",
        } <= names
        (entries,) = (
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        text = archive.read(entries).decode()
        assert "pastpapergen = pastpapergen.cli:main" in text
        assert "keldin-edexcel = keldin_edexcel.cli:main" in text
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join((str(wheel), str(ROOT)))}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from keldin_edexcel.cli import main, generate_package; import pastpapergen.cli as old; assert main is old.main; assert generate_package is old.generate_package",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_old_and_new_module_dry_previews_keep_same_paper_contract(tmp_path):
    import pymupdf

    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join((str(GENERATOR), str(ROOT))),
    }
    texts = []
    for module in ("pastpapergen", "keldin_edexcel"):
        output = tmp_path / module
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
                "--paper",
                "1",
                "--seed",
                "270100",
                "--syllabus",
                str(GENERATOR / "data/syllabus_seed.json"),
                "--out",
                str(output),
                "--dry-run",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        papers = {}
        for path in sorted(output.glob("*.pdf")):
            with pymupdf.open(path) as document:
                papers[path.name] = [page.get_text() for page in document]
        assert len(papers) == 3
        texts.append(papers)
    assert texts[0] == texts[1]
