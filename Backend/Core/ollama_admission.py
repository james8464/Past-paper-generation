"""Conservative local Ollama preflight, not a runtime memory-fit guarantee."""

from __future__ import annotations

import ipaddress
import json
import platform
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request

from Backend.Core.france.network import open_ollama_request

GIB = 1 << 30
METADATA_LIMIT = 4 * 1024 * 1024


class ResourceAdmissionError(RuntimeError):
    """Resource refusal must never enter structured-output repair retries."""

    code = "local_memory_unavailable"


def _is_local_endpoint(base_url: str) -> bool:
    hostname = urlsplit(base_url).hostname
    if hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname or "").is_loopback
    except ValueError:
        return False


def require_local_ollama_capacity(base_url: str, model: str) -> None:
    if not _is_local_endpoint(base_url):
        return
    physical, pressure = _memory_snapshot()
    if type(physical) is not int or physical <= 0:
        raise ResourceAdmissionError(
            "Could not verify physical memory for local Ollama."
        )
    # Linux has no equivalent categorical macOS pressure sensor. Its physical
    # memory bound still applies; do not invent a pressure level from free pages.
    if platform.system() != "Linux" and (type(pressure) is not int or pressure != 1):
        raise ResourceAdmissionError(
            "Local Ollama generation requires normal system memory pressure. "
            "Close memory-heavy apps and try again."
        )
    size = _installed_model_size(base_url, model)
    if type(size) is not int or size <= 0:
        raise ResourceAdmissionError(
            "Could not verify the installed Ollama model size."
        )
    reserve = max(4 * GIB, (physical + 3) // 4)
    overhead = max(2 * GIB, (size + 3) // 4)
    if size + overhead > physical - reserve:
        raise ResourceAdmissionError(
            "This local Ollama model exceeds the conservative memory headroom limit. "
            "Choose a smaller installed model or another provider. "
            "Model download size does not include all generation memory."
        )


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate metadata field")
        result[key] = value
    return result


def _installed_model_size(base_url: str, model: str) -> int:
    try:
        with open_ollama_request(
            Request(f"{base_url.rstrip('/')}/api/tags"), timeout=5
        ) as response:
            content = response.read(METADATA_LIMIT + 1)
        if len(content) > METADATA_LIMIT:
            raise ValueError("Oversized model metadata")
        payload = json.loads(content, object_pairs_hook=_unique_fields)
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise ValueError("Invalid model metadata")
        candidates = {model}
        if ":" not in model.rsplit("/", 1)[-1]:
            candidates.add(f"{model}:latest")
        matches = [
            item
            for item in payload["models"]
            if isinstance(item, dict)
            and (item.get("name") in candidates or item.get("model") in candidates)
        ]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous installed model")
        size = matches[0].get("size")
        if type(size) is not int or size <= 0:
            raise ValueError("Invalid installed model size")
        return size
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        # Import at call time: providers owns the existing wrapper-aware
        # interruption contract and imports this preflight module itself.
        from Backend.Core.providers import _transport_interruption

        interruption = _transport_interruption(error)
        if interruption is error:
            raise
        if interruption is not None:
            raise interruption from error
        raise ResourceAdmissionError(
            "Could not verify the installed Ollama model size. "
            "Check the selected server and installed model, then try again."
        ) from error


def _read_memory_snapshot() -> tuple[int, int | None]:
    try:
        system = platform.system()
        if system == "Darwin":
            values = []
            for key in ("hw.memsize", "kern.memorystatus_vm_pressure_level"):
                result = subprocess.run(
                    ["/usr/sbin/sysctl", "-n", key],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                values.append(int(result.stdout.strip()))
            return values[0], values[1]
        if system == "Linux":
            # Kernel-reported physical memory, not guessed free/reclaimable RAM.
            lines = Path("/proc/meminfo").read_text(encoding="ascii").splitlines()
            entries = [line.split() for line in lines if line.startswith("MemTotal:")]
            if len(entries) != 1 or len(entries[0]) != 3 or entries[0][2] != "kB":
                raise ValueError("Missing physical memory")
            return int(entries[0][1]) * 1024, None
        raise ValueError("Unsupported memory sensor platform")
    except InterruptedError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise ResourceAdmissionError(
            "Could not verify system memory for local Ollama. Generation was not started."
        ) from error


_memory_snapshot = _read_memory_snapshot
