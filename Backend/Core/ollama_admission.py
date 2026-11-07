"""Conservative local Ollama preflight, not a runtime memory-fit guarantee."""

from __future__ import annotations

import ipaddress
import json
import platform
import re
import subprocess
from typing import cast
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
    physical = _checked_physical_memory()
    size, resident = _installed_model_state(base_url, model)
    if type(size) is not int or size <= 0 or type(resident) is not bool:
        raise ResourceAdmissionError("Could not verify installed model size/residency.")
    reserve = max(4 * GIB, (physical + 3) // 4)
    overhead = max(2 * GIB, (size + 3) // 4)
    if size + overhead > physical - reserve:
        raise ResourceAdmissionError(
            "This local Ollama model exceeds the conservative memory headroom limit. "
            "Choose a smaller installed model or another provider. "
            "Model download size does not include all generation memory."
        )
    # Sample after bounded metadata reads, never cache available/resident state.
    headroom = _headroom_snapshot(physical)
    if type(headroom) is not int or not 0 <= headroom <= physical:
        raise ResourceAdmissionError("Could not verify local memory headroom.")
    if _checked_physical_memory() != physical:
        raise ResourceAdmissionError("System memory changed during admission.")
    required = overhead if resident else size + overhead
    if required > min(physical - reserve, headroom):
        raise ResourceAdmissionError(
            "Local Ollama has insufficient estimated memory headroom. "
            "Generation was not started."
        )


def _checked_physical_memory() -> int:
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
    return physical


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate metadata field")
        result[key] = value
    return result


def _model_metadata(base_url: str, route: str) -> list[object]:
    try:
        with open_ollama_request(
            Request(f"{base_url.rstrip('/')}/api/{route}"), timeout=5
        ) as response:
            content = response.read(METADATA_LIMIT + 1)
        if len(content) > METADATA_LIMIT:
            raise ValueError("Oversized model metadata")
        payload = json.loads(content, object_pairs_hook=_unique_fields)
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise ValueError("Invalid model metadata")
        return cast(list[object], payload["models"])
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        # Preserve the existing wrapper-aware cancellation identity.
        from Backend.Core.providers import _transport_interruption

        interruption = _transport_interruption(error)
        if interruption is error:
            raise
        if interruption is not None:
            raise interruption from error
        raise ResourceAdmissionError(
            "Could not verify local Ollama model metadata."
        ) from error


def _names(item: dict[str, object]) -> set[str]:
    names = [item[key] for key in ("name", "model") if key in item]
    if not names or any(
        type(name) is not str or not name or any(c.isspace() for c in name)
        for name in names
    ):
        raise ValueError("Invalid model name")
    validated_names = cast(list[str], names)
    normalized = {
        name if ":" in name.rsplit("/", 1)[-1] else f"{name}:latest"
        for name in validated_names
    }
    if len(normalized) != 1:
        raise ValueError("Conflicting model aliases")
    return normalized


def _digest(item: dict[str, object]) -> str:
    digest = item.get("digest")
    if type(digest) is not str or re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise ValueError("Invalid model digest")
    return digest


def _installed_model_state(base_url: str, model: str) -> tuple[int, bool]:
    try:
        candidates = _names({"name": model})
        matches = [
            item
            for item in _model_metadata(base_url, "tags")
            if isinstance(item, dict) and candidates.intersection(_names(item))
        ]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous installed model")
        size = matches[0].get("size")
        if type(size) is not int or size <= 0:
            raise ValueError("Invalid installed model size")
        digest = _digest(matches[0])
        seen_names: set[str] = set()
        seen_digests: set[str] = set()
        for item in _model_metadata(base_url, "ps"):
            if not isinstance(item, dict):
                raise ValueError("Invalid resident model")
            names, loaded_digest = _names(item), _digest(item)
            if seen_names.intersection(names) or loaded_digest in seen_digests:
                raise ValueError("Ambiguous resident models")
            if candidates.intersection(names) and loaded_digest != digest:
                raise ValueError("Resident model digest changed")
            seen_names.update(names)
            seen_digests.add(loaded_digest)
        return size, digest in seen_digests
    except (ValueError, TypeError) as error:
        raise ResourceAdmissionError(
            "Could not verify installed model size/residency."
        ) from error


def _sensor_output(command: list[str]) -> str:
    result = subprocess.run(
        command, check=True, capture_output=True, text=True, timeout=2
    )
    content = result.stdout
    if type(content) is not str or len(content) > 65536:
        raise ValueError("Oversized memory sensor")
    return content


def _linux_memory_value(name: str) -> int:
    # A bounded child also gives the kernel-file probe an explicit time limit.
    content = _sensor_output(["/bin/cat", "/proc/meminfo"])
    lines = [line for line in content.splitlines() if line.startswith(f"{name}:")]
    if len(lines) != 1 or not (
        match := re.fullmatch(rf"{name}:\s*([0-9]+)\s+kB", lines[0])
    ):
        raise ValueError("Missing memory sensor")
    return int(match[1]) * 1024


def _read_headroom_snapshot(physical: int) -> int:
    try:
        if platform.system() == "Linux":
            value = _linux_memory_value("MemAvailable")
            if not 0 <= value <= physical:
                raise ValueError("Impossible available memory")
            return value
        if platform.system() != "Darwin":
            raise ValueError("Unsupported headroom sensor platform")
        lines = _sensor_output(["/usr/bin/vm_stat"]).splitlines()
        header = re.fullmatch(
            r"Mach Virtual Memory Statistics: \(page size of ([0-9]+) bytes\)", lines[0]
        )
        if header is None or int(header[1]) <= 0:
            raise ValueError("Missing native page size")
        page_size = int(header[1])
        if page_size & (page_size - 1) or physical % page_size:
            raise ValueError("Invalid native page size")
        counts = []
        for label in ("free", "inactive"):
            matches = [
                re.fullmatch(rf"Pages {label}:\s*([0-9]+)\.", line)
                for line in lines
                if line.startswith(f"Pages {label}:")
            ]
            if len(matches) != 1 or matches[0] is None:
                raise ValueError("Missing native page count")
            counts.append(int(matches[0][1]))
        # Approximate reclaimability, not exact available RAM or Ollama's formula.
        # Speculative is already in free_count; no overlapping categories added.
        value = sum(counts) * page_size
        if not 0 <= value <= physical:
            raise ValueError("Impossible native memory counters")
        return value
    except InterruptedError:
        raise
    except (OSError, ValueError, IndexError, subprocess.SubprocessError) as error:
        raise ResourceAdmissionError(
            "Could not verify current memory headroom."
        ) from error


def _read_memory_snapshot() -> tuple[int, int | None]:
    try:
        system = platform.system()
        if system == "Darwin":
            values = []
            for key in ("hw.memsize", "kern.memorystatus_vm_pressure_level"):
                values.append(
                    int(_sensor_output(["/usr/sbin/sysctl", "-n", key]).strip())
                )
            return values[0], values[1]
        if system == "Linux":
            # Kernel-reported physical memory, not guessed free/reclaimable RAM.
            return _linux_memory_value("MemTotal"), None
        raise ValueError("Unsupported memory sensor platform")
    except InterruptedError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise ResourceAdmissionError(
            "Could not verify system memory for local Ollama. Generation was not started."
        ) from error


_memory_snapshot = _read_memory_snapshot
_headroom_snapshot = _read_headroom_snapshot
