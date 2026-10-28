from __future__ import annotations

import configparser
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "Resources/generator-registry.json").read_text())
GENERATOR_ROOTS = {
    Path("Resources") / family["python_path"]
    for family in REGISTRY["families"]
    if family["advertised"]
}


def test_bootstrap_installs_every_advertised_generator_without_network(tmp_path):
    repository = tmp_path / "fake repository with spaces"
    script = repository / "macOS/scripts/bootstrap_backend.sh"
    script.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "macOS/scripts/bootstrap_backend.sh", script)
    arguments = tmp_path / "pip-arguments"
    fake_pip = tmp_path / "fake-pip"
    fake_pip.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\nprintf "%s\\0" "$@" > "$BOOTSTRAP_ARGUMENTS"\n'
    )
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        '[[ "$1" == "-m" && "$2" == "venv" ]] || exit 91\n'
        'mkdir -p "$3/bin"\ncp "$FAKE_PIP_SCRIPT" "$3/bin/python"\n'
        'chmod +x "$3/bin/python"\n'
    )
    fake_python.chmod(0o700)
    subprocess.run(
        ["bash", str(script)],
        check=True,
        capture_output=True,
        timeout=10,
        env={
            **os.environ,
            "PYTHON": str(fake_python),
            "FAKE_PIP_SCRIPT": str(fake_pip),
            "BOOTSTRAP_ARGUMENTS": str(arguments),
        },
    )
    captured = arguments.read_bytes().decode().split("\0")[:-1]
    assert captured[:3] == ["-m", "pip", "install"]
    assert captured[3:5] == ["-r", str(repository / "requirements-build.txt")]
    assert len(captured[5:]) % 2 == 0
    assert captured[5::2] == ["-e"] * len(GENERATOR_ROOTS)
    installed = [Path(value).relative_to(repository) for value in captured[6::2]]
    assert len(installed) == len(set(installed))
    assert set(installed) == GENERATOR_ROOTS


def test_backend_ci_installs_the_same_advertised_generators():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    installed = re.findall(r"(?m)^\s+-e (Resources/[^\s\\]+)", workflow)
    assert len(installed) == len(set(installed))
    assert {Path(value) for value in installed} == GENERATOR_ROOTS


def test_pytest_paths_and_collections_cover_the_advertised_generators():
    configuration = configparser.ConfigParser()
    configuration.read(ROOT / "pytest.ini")
    python_paths = {
        Path(value) for value in configuration["pytest"]["pythonpath"].split()
    }
    test_paths = {Path(value) for value in configuration["pytest"]["testpaths"].split()}
    assert python_paths == {Path("."), *GENERATOR_ROOTS}
    assert test_paths == {Path("tests"), *(path / "tests" for path in GENERATOR_ROOTS)}


def test_conftest_routes_each_advertised_generator_without_changing_process_state():
    specification = importlib.util.spec_from_file_location(
        "generator_routing_under_test", ROOT / "conftest.py"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    class Recorder:
        def __init__(self):
            self.directory = None
            self.environment = {}

        def chdir(self, directory):
            self.directory = directory

        def setenv(self, key, value):
            self.environment[key] = value

    for relative_root in sorted(GENERATOR_ROOTS):
        recorder = Recorder()
        request = SimpleNamespace(fspath=ROOT / relative_root / "tests/test_example.py")
        module.generator_working_directory.__wrapped__(request, recorder)
        assert recorder.directory == ROOT / relative_root
        assert {
            Path(value)
            for value in recorder.environment["PYTHONPATH"].split(os.pathsep)
        } == {ROOT, *(ROOT / path for path in GENERATOR_ROOTS)}
