"""Hardware measurements must not certify an untested model or paper."""

import json
from pathlib import Path

import pytest

from Backend.Core import benchmark

ROOT = Path(__file__).resolve().parents[1]
TITLE = "Hardware check passed"
DETAIL = (
    "This checks the Mac's hardware, not the selected model's speed or paper quality."
)
FRENCH_DETAIL = "Ce test vérifie le matériel du Mac, pas la vitesse du modèle sélectionné ni la qualité des sujets."


def test_successful_hardware_summary_does_not_claim_model_performance(monkeypatch):
    events = []
    monkeypatch.setattr(
        benchmark,
        "emit",
        lambda kind, **values: events.append({"type": kind, **values}),
    )
    monkeypatch.setattr(benchmark, "power_status", lambda: ("AC Power", None, 1.0))
    sample = {
        "cpu_mb_s": 650,
        "cpu_load": 0,
        "memory_available_gb": 8,
        "memory_pressure_percent": 0,
        "swap_used_gb": 0,
        "disk_write_mb_s": 400,
        "disk_read_mb_s": 700,
        "disk_free_gb": 20,
        "small_file_ms": 0,
        "pdf_pages_per_s": 18,
        "thermal_speed_limit_percent": 100,
        "network_latency_ms": 0,
        "network_download_mb_s": 12,
        "ollama_latency_ms": None,
    }
    benchmark.emit_final_metrics([sample])
    assert events[-1] == {
        "type": "benchmark_done",
        "score": 1.0,
        "verdict": TITLE,
        "detail": DETAIL,
    }


@pytest.mark.parametrize(
    "english,french",
    [
        (TITLE, "Vérification du matériel réussie"),
        (DETAIL, FRENCH_DETAIL),
    ],
)
def test_hardware_verdict_is_mapped_and_translated(english, french):
    app = ROOT / "macOS/Keldin"
    source = (app / "Domain/NativeInterfaceCopy.swift").read_text()
    assert f'"{english}": "{english}"' in source
    catalog = json.loads((app / "Localizable.xcstrings").read_text())["strings"]
    assert catalog[english]["localizations"]["fr"]["stringUnit"] == {
        "state": "translated",
        "value": french,
    }


def test_historical_benchmark_messages_remain_displayable():
    app = ROOT / "macOS/Keldin"
    source = (app / "Domain/NativeInterfaceCopy.swift").read_text()
    catalog = json.loads((app / "Localizable.xcstrings").read_text())["strings"]
    for legacy in (
        "Ready for local generation",
        "This Mac should generate papers comfortably with the selected local setup.",
    ):
        assert f'"{legacy}": "{legacy}"' in source
        assert (
            catalog[legacy]["localizations"]["fr"]["stringUnit"]["state"]
            == "translated"
        )
