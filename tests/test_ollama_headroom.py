"""Approximate cache-aware headroom; no host sensors, server or inference."""

import io
import json
import subprocess
from types import SimpleNamespace

import pytest

from Backend.Core import ollama_admission as admission
from Backend.Core import providers

GIB = 1 << 30
DIGEST = "a" * 64


@pytest.fixture
def machine(monkeypatch):
    state = dict(free=9 * GIB, inactive=0, ps=[], pressure=1, vm=None, calls=[])
    monkeypatch.setattr(admission.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        admission, "_headroom_snapshot", admission._read_headroom_snapshot
    )
    monkeypatch.setattr(
        admission, "_memory_snapshot", lambda: (18 * GIB, state["pressure"])
    )

    def run(command, **kwargs):
        assert command == ["/usr/bin/vm_stat"]
        assert kwargs["timeout"] <= 2 and kwargs["check"]
        state["calls"].append("vm")
        return SimpleNamespace(
            stdout=state["vm"]
            or (
                "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
                f"Pages free: {state['free'] // 16384}.\n"
                f"Pages inactive: {state['inactive'] // 16384}.\n"
                "Pages speculative: 65536.\nPages purgeable: 65536.\n"
            )
        )

    def metadata(request, *, timeout):
        assert request.get_method() == "GET" and timeout <= 5
        state["calls"].append(request.full_url.rsplit("/", 1)[-1])
        if request.full_url.endswith("/ps") and "after_metadata_pressure" in state:
            state["pressure"] = state["after_metadata_pressure"]
        payload = (
            {
                "models": [
                    {
                        "name": "fixture:latest",
                        "model": "fixture:latest",
                        "size": 6 * GIB,
                        "digest": DIGEST,
                    }
                ]
            }
            if request.full_url.endswith("/tags")
            else {"models": state["ps"]}
        )
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(admission.subprocess, "run", run)
    monkeypatch.setattr(admission, "open_ollama_request", metadata)
    return state


def require():
    admission.require_local_ollama_capacity("http://localhost:11434", "fixture")


def resident():
    return {"name": "fixture:latest", "model": "fixture:latest", "digest": DIGEST}


def test_cold_load_refuses_current_headroom_shortfall(machine):
    machine["free"] = 4 * GIB
    with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
        require()


def test_ample_reclaimable_cache_is_not_treated_as_free_only(machine):
    machine.update(free=GIB, inactive=10 * GIB)
    require()
    assert machine["calls"] == ["tags", "ps", "vm"]


@pytest.mark.parametrize(
    "warm,headroom,passes",
    [
        (False, 8 * GIB, True),
        (False, 8 * GIB - 16384, False),
        (True, 2 * GIB, True),
        (True, 2 * GIB - 16384, False),
    ],
)
def test_cold_and_warm_boundaries_keep_generation_overhead(
    machine, warm, headroom, passes
):
    machine.update(free=headroom, ps=[resident()] if warm else [])
    if passes:
        require()
    else:
        with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
            require()


@pytest.mark.parametrize(
    "ps",
    [
        [{**resident(), "digest": "b" * 64}],
        [resident(), resident()],
        [{}],
        [{**resident(), "digest": None}],
        [{"name": "other", "digest": "bad"}],
    ],
)
def test_unknown_incompatible_or_duplicate_residency_refuses(machine, ps):
    machine["ps"] = ps
    with pytest.raises(admission.ResourceAdmissionError):
        require()


def test_other_digest_does_not_grant_warm_credit(machine):
    machine.update(free=3 * GIB, ps=[{"name": "other:latest", "digest": "b" * 64}])
    with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
        require()


@pytest.mark.parametrize(
    "vm",
    [
        "bad",
        "Mach Virtual Memory Statistics: (page size of 0 bytes)\nPages free: 1.\nPages inactive: 1.\n",
        "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 1.\nPages free: 2.\nPages inactive: 1.\n",
    ],
)
def test_unknown_or_duplicate_sensor_fields_refuse(machine, vm):
    machine["vm"] = vm
    with pytest.raises(admission.ResourceAdmissionError):
        require()


def test_impossible_counter_total_refuses_instead_of_clamping(machine):
    machine.update(free=18 * GIB, inactive=GIB)
    with pytest.raises(admission.ResourceAdmissionError):
        require()


def test_pressure_refuses_before_metadata(machine):
    machine["pressure"] = 2
    with pytest.raises(admission.ResourceAdmissionError):
        require()
    assert machine["calls"] == []


def test_resource_refusal_prevents_thinking_and_chat_post(machine, monkeypatch):
    machine["free"] = GIB

    def forbidden(*args, **kwargs):
        pytest.fail("Resource refusal must precede thinking or chat")

    monkeypatch.setattr(providers.OllamaClient, "_ollama_thinking_policy", forbidden)
    with pytest.raises(admission.ResourceAdmissionError):
        providers.OllamaClient("http://localhost:11434", "fixture")._ollama(
            "unchanged", schema={"type": "object"}, request_function=forbidden
        )


def test_headroom_sensor_timeout_is_typed(machine, monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired("vm_stat", 2)

    monkeypatch.setattr(admission.subprocess, "run", fail)
    with pytest.raises(admission.ResourceAdmissionError):
        require()


@pytest.mark.parametrize("warm", [False, True])
def test_exact_byte_headroom_boundary(machine, monkeypatch, warm):
    machine["ps"] = [resident()] if warm else []
    required = (2 if warm else 8) * GIB
    monkeypatch.setattr(admission, "_headroom_snapshot", lambda physical: required)
    require()
    monkeypatch.setattr(admission, "_headroom_snapshot", lambda physical: required - 1)
    with pytest.raises(admission.ResourceAdmissionError, match="headroom"):
        require()


def test_pressure_is_rechecked_after_metadata(machine):
    machine["after_metadata_pressure"] = 2
    with pytest.raises(admission.ResourceAdmissionError, match="pressure"):
        require()


def test_resident_digest_alias_does_not_charge_weights_again(machine):
    machine.update(
        free=3 * GIB,
        ps=[{**resident(), "name": "alias:latest", "model": "alias:latest"}],
    )
    require()


@pytest.mark.parametrize(
    "ps",
    [
        [{**resident(), "model": "other:latest"}],
        [resident(), {**resident(), "digest": "b" * 64}],
        [{"name": " ", "digest": DIGEST}],
        [False],
    ],
)
def test_conflicting_alias_names_or_invalid_resident_rows_refuse(machine, ps):
    machine["ps"] = ps
    with pytest.raises(admission.ResourceAdmissionError):
        require()


@pytest.mark.parametrize(
    "available", ["12582912", "1", None, "True", "99999999999999999"]
)
def test_linux_kernel_available_is_required_and_bounded(
    machine, monkeypatch, available
):
    monkeypatch.setattr(admission.platform, "system", lambda: "Linux")

    def read(command, **kwargs):
        assert command == ["/bin/cat", "/proc/meminfo"] and kwargs["timeout"] == 2
        return SimpleNamespace(
            stdout="MemTotal: 18874368 kB\nMemFree: 12582912 kB\n"
            + (f"MemAvailable: {available} kB\n" if available is not None else "")
        )

    monkeypatch.setattr(admission.subprocess, "run", read)
    if available == "12582912":
        require()
    else:
        with pytest.raises(admission.ResourceAdmissionError):
            require()


def test_headroom_sensor_cancellation_keeps_identity(machine, monkeypatch):
    error = InterruptedError("cancel")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(admission.subprocess, "run", fail)
    with pytest.raises(InterruptedError) as caught:
        require()
    assert caught.value is error


@pytest.mark.parametrize("wrapped", [False, True])
def test_residency_probe_cancellation_keeps_identity(machine, monkeypatch, wrapped):
    from urllib.error import URLError

    real_fake = admission.open_ollama_request
    error = InterruptedError("cancel")

    def read(request, **kwargs):
        if request.full_url.endswith("/ps"):
            transport = URLError(error)
            if wrapped:
                raise RuntimeError("wrapped") from transport
            raise transport
        return real_fake(request, **kwargs)

    monkeypatch.setattr(admission, "open_ollama_request", read)
    with pytest.raises(InterruptedError) as caught:
        require()
    assert caught.value is error


@pytest.mark.parametrize(
    "body", [b"[]", b"{}", b'{"models":{}}', b'{"models":[],"models":[]}']
)
def test_malformed_residency_root_is_typed(machine, monkeypatch, body):
    original = admission.open_ollama_request

    def read(request, **kwargs):
        return (
            io.BytesIO(body)
            if request.full_url.endswith("/ps")
            else original(request, **kwargs)
        )

    monkeypatch.setattr(admission, "open_ollama_request", read)
    with pytest.raises(admission.ResourceAdmissionError):
        require()


@pytest.mark.parametrize("oversized", [False, True])
def test_residency_transport_is_bounded_direct_get(machine, monkeypatch, oversized):
    original = admission.open_ollama_request
    calls = []

    class Response(io.BytesIO):
        def read(self, size=-1):
            calls.append(size)
            return super().read(size)

    def read(request, **kwargs):
        if request.full_url.endswith("/ps"):
            assert request.full_url == "http://localhost:11434/api/ps"
            assert request.get_method() == "GET" and kwargs == {"timeout": 5}
            return Response(
                b"x" * (admission.METADATA_LIMIT + 1) if oversized else b'{"models":[]}'
            )
        return original(request, **kwargs)

    monkeypatch.setattr(admission, "open_ollama_request", read)
    if oversized:
        with pytest.raises(admission.ResourceAdmissionError):
            require()
    else:
        require()
    assert calls == [admission.METADATA_LIMIT + 1]
