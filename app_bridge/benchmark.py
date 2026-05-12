from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import platform
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from statistics import mean

from app_bridge.events import emit

SAMPLE_BYTES = 4 * 1024 * 1024
CPU_PROBE_SECONDS = 0.18
NETWORK_PROBE_URL = "https://www.apple.com/library/test/success.html"
NETWORK_TIMEOUT_SECONDS = 2
TICK_SECONDS = 1.0
BYTES_PER_MEGABYTE = 1_000_000
BYTES_PER_GIBIBYTE = 1_073_741_824

CPU_SCORE_TARGET_MB_S = 650
MEMORY_SCORE_TARGET_GB = 8
DISK_WRITE_TARGET_MB_S = 400
DISK_READ_TARGET_MB_S = 700
NETWORK_SCORE_FALLBACK = 0.72
NETWORK_LATENCY_CEILING_MS = 900
NETWORK_LATENCY_SCORE_MS = 1000

CPU_SCORE_WEIGHT = 0.34
LOAD_SCORE_WEIGHT = 0.16
MEMORY_SCORE_WEIGHT = 0.20
DISK_SCORE_WEIGHT = 0.20
NETWORK_SCORE_WEIGHT = 0.10

READY_SCORE = 0.78
CAPABLE_SCORE = 0.60


def handle_benchmark(args: argparse.Namespace) -> int:
    duration = max(1.0, float(args.duration))
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    emit_static_metrics()

    samples: list[dict[str, float | None]] = []
    payload = os.urandom(SAMPLE_BYTES)
    started = time.perf_counter()
    last_network_ms: float | None = None

    while True:
        elapsed = time.perf_counter() - started
        if elapsed >= duration:
            break

        cpu_mb_s = cpu_probe(payload)
        disk_write, disk_read = disk_probe(output_dir, payload)
        memory_available = available_memory_gb()
        cpu_load = cpu_load_percent()
        if len(samples) % 5 == 0 or last_network_ms is None:
            last_network_ms = network_latency_ms()

        sample = {
            "elapsed": min(duration, time.perf_counter() - started),
            "cpu_load": cpu_load,
            "memory_available_gb": memory_available,
            "disk_write_mb_s": disk_write,
            "disk_read_mb_s": disk_read,
            "network_latency_ms": last_network_ms,
            "cpu_mb_s": cpu_mb_s,
        }
        samples.append(sample)
        emit("benchmark_sample", **sample)

        remaining_tick = TICK_SECONDS - ((time.perf_counter() - started) % TICK_SECONDS)
        time.sleep(min(remaining_tick, max(0, duration - (time.perf_counter() - started))))

    emit_final_metrics(samples)
    return 0


def emit_static_metrics() -> None:
    emit("benchmark_metric", name="Device", detail=platform.platform())
    emit("benchmark_metric", name="Processor", detail=cpu_brand())
    emit("benchmark_metric", name="CPU Cores", value=os.cpu_count() or 1, unit="cores")
    emit("benchmark_metric", name="Memory", value=total_memory_gb(), unit="GB")


def emit_final_metrics(samples: list[dict[str, float | None]]) -> None:
    if not samples:
        emit("benchmark_done", score=0.0, verdict="Benchmark failed", detail="No samples were collected.")
        return

    cpu = avg(samples, "cpu_mb_s")
    cpu_load = avg(samples, "cpu_load")
    free_memory = avg(samples, "memory_available_gb")
    disk_write = avg(samples, "disk_write_mb_s")
    disk_read = avg(samples, "disk_read_mb_s")
    latency_values = [float(sample["network_latency_ms"]) for sample in samples if sample["network_latency_ms"] is not None]
    latency = mean(latency_values) if latency_values else None

    cpu_score = clamp(cpu / CPU_SCORE_TARGET_MB_S)
    load_score = clamp(1.0 - (cpu_load / 100) * 0.7)
    memory_score = clamp(free_memory / MEMORY_SCORE_TARGET_GB)
    disk_score = (clamp(disk_write / DISK_WRITE_TARGET_MB_S) + clamp(disk_read / DISK_READ_TARGET_MB_S)) / 2
    network_score = NETWORK_SCORE_FALLBACK if latency is None else clamp(1.0 - min(latency, NETWORK_LATENCY_CEILING_MS) / NETWORK_LATENCY_SCORE_MS)
    score = (
        cpu_score * CPU_SCORE_WEIGHT
        + load_score * LOAD_SCORE_WEIGHT
        + memory_score * MEMORY_SCORE_WEIGHT
        + disk_score * DISK_SCORE_WEIGHT
        + network_score * NETWORK_SCORE_WEIGHT
    )

    emit("benchmark_metric", name="CPU Throughput", value=cpu, unit="MB/s", score=cpu_score, detail="Hashing workload used as a local model proxy.")
    emit("benchmark_metric", name="Average CPU Load", value=cpu_load, unit="%", score=load_score)
    emit("benchmark_metric", name="Free Memory", value=free_memory, unit="GB", score=memory_score)
    emit("benchmark_metric", name="Disk Write", value=disk_write, unit="MB/s", score=clamp(disk_write / DISK_WRITE_TARGET_MB_S))
    emit("benchmark_metric", name="Disk Read", value=disk_read, unit="MB/s", score=clamp(disk_read / DISK_READ_TARGET_MB_S))
    if latency is None:
        emit("benchmark_metric", name="Network", detail="Unavailable during benchmark", score=network_score)
    else:
        emit("benchmark_metric", name="Network Latency", value=latency, unit="ms", score=network_score)

    if score >= READY_SCORE:
        verdict = "Ready for local generation"
        detail = "This Mac should generate papers comfortably with the selected local setup."
    elif score >= CAPABLE_SCORE:
        verdict = "Capable with slower local models"
        detail = "Generation should work, but large Ollama models may take noticeably longer."
    else:
        verdict = "Use smaller models or hosted AI"
        detail = "The diagnostic found limited headroom for local generation."

    emit("benchmark_done", score=round(score, 3), verdict=verdict, detail=detail)


def cpu_probe(payload: bytes) -> float:
    started = time.perf_counter()
    processed = 0
    while time.perf_counter() - started < CPU_PROBE_SECONDS:
        hashlib.sha256(payload).digest()
        processed += len(payload)
    elapsed = max(0.001, time.perf_counter() - started)
    return processed / elapsed / BYTES_PER_MEGABYTE


def disk_probe(output_dir: Path, payload: bytes) -> tuple[float, float]:
    fd, raw_path = tempfile.mkstemp(prefix="past-paper-benchmark-", suffix=".bin", dir=output_dir)
    path = Path(raw_path)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            started = time.perf_counter()
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            write_elapsed = max(0.001, time.perf_counter() - started)

        started = time.perf_counter()
        _ = path.read_bytes()
        read_elapsed = max(0.001, time.perf_counter() - started)
        size_mb = len(payload) / BYTES_PER_MEGABYTE
        return size_mb / write_elapsed, size_mb / read_elapsed
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


def network_latency_ms() -> float | None:
    started = time.perf_counter()
    try:
        request = urllib.request.Request(
            NETWORK_PROBE_URL,
            headers={"User-Agent": "PastPaperCreatorBenchmark/1.0"},
        )
        with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            response.read(128)
            if response.status >= 400:
                return None
    except (OSError, TimeoutError, urllib.error.URLError):
        return None
    return (time.perf_counter() - started) * 1000


def cpu_load_percent() -> float:
    try:
        load = os.getloadavg()[0]
        cores = max(1, os.cpu_count() or 1)
        return clamp(load / cores, upper=2.0) * 50
    except OSError:
        return 0


def available_memory_gb() -> float:
    if platform.system() == "Darwin":
        try:
            output = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
            page_size = 4096
            free_pages = 0
            for raw_line in output.splitlines():
                line = raw_line.strip()
                if "page size of" in line:
                    page_size = int(line.split("page size of", 1)[1].split("bytes", 1)[0].strip())
                elif line.startswith(("Pages free", "Pages inactive", "Pages speculative")):
                    free_pages += int(line.split(":", 1)[1].strip().rstrip(".").replace(".", ""))
            return free_pages * page_size / BYTES_PER_GIBIBYTE
        except (OSError, subprocess.SubprocessError, ValueError, IndexError):
            return max(0.0, total_memory_gb() * 0.35)
    return max(0.0, total_memory_gb() * 0.35)


def total_memory_gb() -> float:
    if platform.system() == "Darwin":
        try:
            raw = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, stderr=subprocess.DEVNULL)
            return int(raw.strip()) / BYTES_PER_GIBIBYTE
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return pages * page_size / BYTES_PER_GIBIBYTE
        except (OSError, ValueError):
            pass
    return 0


def cpu_brand() -> str:
    if platform.system() == "Darwin":
        try:
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or platform.machine()


def avg(samples: list[dict[str, float | None]], key: str) -> float:
    values = [float(sample[key]) for sample in samples if sample.get(key) is not None]
    return mean(values) if values else 0


def clamp(value: float, upper: float = 1.0) -> float:
    return max(0.0, min(upper, value))
