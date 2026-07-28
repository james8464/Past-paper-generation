from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from statistics import mean

from Backend.Core.events import emit
from Backend.Core.paths import absolute_user_path

SAMPLE_BYTES = 4 * 1024 * 1024
CPU_PROBE_SECONDS = 0.18
NETWORK_PROBE_URL = "https://www.apple.com/library/test/success.html"
NETWORK_DOWNLOAD_URL = "https://www.apple.com/"
NETWORK_TIMEOUT_SECONDS = 2
TICK_SECONDS = 1.0
BYTES_PER_MEGABYTE = 1_000_000
BYTES_PER_GIBIBYTE = 1_073_741_824

CPU_SCORE_TARGET_MB_S = 650
MEMORY_SCORE_TARGET_GB = 8
MEMORY_PRESSURE_COMFORT_PERCENT = 65
MEMORY_PRESSURE_CEILING_PERCENT = 95
SWAP_USAGE_SCORE_GB = 4
DISK_WRITE_TARGET_MB_S = 400
DISK_READ_TARGET_MB_S = 700
DISK_FREE_TARGET_GB = 20
SMALL_FILE_SCORE_MS = 22
PDF_TARGET_PAGES_PER_SECOND = 18
NETWORK_SCORE_FALLBACK = 0.72
NETWORK_LATENCY_CEILING_MS = 900
NETWORK_LATENCY_SCORE_MS = 1000
NETWORK_DOWNLOAD_TARGET_MB_S = 12
THERMAL_SCORE_FALLBACK = 0.9

CPU_SCORE_WEIGHT = 0.22
LOAD_SCORE_WEIGHT = 0.08
MEMORY_SCORE_WEIGHT = 0.15
SWAP_SCORE_WEIGHT = 0.08
DISK_SCORE_WEIGHT = 0.12
STORAGE_SCORE_WEIGHT = 0.08
NETWORK_SCORE_WEIGHT = 0.06
PDF_SCORE_WEIGHT = 0.09
THERMAL_SCORE_WEIGHT = 0.08
POWER_SCORE_WEIGHT = 0.04

READY_SCORE = 0.78
CAPABLE_SCORE = 0.60
Sample = dict[str, float | None]


def handle_benchmark(args: argparse.Namespace) -> int:
    duration = max(1.0, float(args.duration))
    output_dir = absolute_user_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    emit_static_metrics()

    samples: list[Sample] = []
    payload = os.urandom(SAMPLE_BYTES)
    started = time.perf_counter()
    last_network_ms: float | None = None
    last_network_download: float | None = None

    while True:
        elapsed = time.perf_counter() - started
        if elapsed >= duration:
            break

        cpu_mb_s = cpu_probe(payload)
        disk_write, disk_read, disk_free, small_file_ms = disk_probe(output_dir, payload)
        memory_available, memory_pressure, swap_used = memory_snapshot()
        cpu_load = cpu_load_percent()
        if len(samples) % 5 == 0 or last_network_ms is None:
            last_network_ms, last_network_download = network_probe()

        sample = {
            "elapsed": min(duration, time.perf_counter() - started),
            "cpu_load": cpu_load,
            "memory_available_gb": memory_available,
            "memory_pressure_percent": memory_pressure,
            "swap_used_gb": swap_used,
            "disk_write_mb_s": disk_write,
            "disk_read_mb_s": disk_read,
            "disk_free_gb": disk_free,
            "small_file_ms": small_file_ms,
            "network_latency_ms": last_network_ms,
            "network_download_mb_s": last_network_download,
            "ollama_latency_ms": ollama_latency_ms(),
            "cpu_mb_s": cpu_mb_s,
            "thermal_speed_limit_percent": thermal_speed_limit_percent(),
            "pdf_pages_per_s": pdf_probe(output_dir),
        }
        samples.append(sample)
        emit("benchmark_sample", **sample)

        remaining_tick = TICK_SECONDS - ((time.perf_counter() - started) % TICK_SECONDS)
        time.sleep(min(remaining_tick, max(0, duration - (time.perf_counter() - started))))

    emit_final_metrics(samples)
    return 0


def emit_static_metrics() -> None:
    emit("benchmark_metric", name="Device", detail=platform.platform())
    emit("benchmark_metric", name="Architecture", detail=platform.machine())
    emit("benchmark_metric", name="Processor", detail=cpu_brand())
    emit("benchmark_metric", name="CPU Cores", value=os.cpu_count() or 1, unit="cores")
    emit("benchmark_metric", name="Memory", value=total_memory_gb(), unit="GB")
    emit("benchmark_metric", name="Python Runtime", detail=platform.python_version())
    performance_cores, efficiency_cores = apple_cpu_core_split()
    if performance_cores is not None:
        emit("benchmark_metric", name="Performance Cores", value=performance_cores, unit="cores")
    if efficiency_cores is not None:
        emit("benchmark_metric", name="Efficiency Cores", value=efficiency_cores, unit="cores")


def emit_final_metrics(samples: list[Sample]) -> None:
    if not samples:
        emit("benchmark_done", score=0.0, verdict="Benchmark failed", detail="No samples were collected.")
        return

    cpu = avg(samples, "cpu_mb_s")
    cpu_load = avg(samples, "cpu_load")
    free_memory = avg(samples, "memory_available_gb")
    memory_pressure = avg(samples, "memory_pressure_percent")
    swap_used = avg(samples, "swap_used_gb")
    disk_write = avg(samples, "disk_write_mb_s")
    disk_read = avg(samples, "disk_read_mb_s")
    disk_free = latest(samples, "disk_free_gb")
    small_file_ms = avg(samples, "small_file_ms")
    pdf_pages_per_s = avg(samples, "pdf_pages_per_s")
    thermal_limit = optional_mean(samples, "thermal_speed_limit_percent")
    latency_values = [float(sample["network_latency_ms"]) for sample in samples if sample["network_latency_ms"] is not None]
    latency = mean(latency_values) if latency_values else None
    download_values = [float(sample["network_download_mb_s"]) for sample in samples if sample["network_download_mb_s"] is not None]
    download = mean(download_values) if download_values else None
    ollama_values = [float(sample["ollama_latency_ms"]) for sample in samples if sample["ollama_latency_ms"] is not None]
    ollama_latency = mean(ollama_values) if ollama_values else None
    power_source, battery_percent, power_score = power_status()

    cpu_score = clamp(cpu / CPU_SCORE_TARGET_MB_S)
    load_score = clamp(1.0 - (cpu_load / 100) * 0.7)
    memory_score = clamp(free_memory / MEMORY_SCORE_TARGET_GB)
    memory_pressure_score = memory_pressure_score_for(memory_pressure)
    swap_score = clamp(1.0 - swap_used / SWAP_USAGE_SCORE_GB)
    storage_score = clamp(disk_free / DISK_FREE_TARGET_GB)
    small_file_score = clamp(1.0 - min(small_file_ms, SMALL_FILE_SCORE_MS) / SMALL_FILE_SCORE_MS)
    disk_score = (
        clamp(disk_write / DISK_WRITE_TARGET_MB_S)
        + clamp(disk_read / DISK_READ_TARGET_MB_S)
        + small_file_score
    ) / 3
    latency_score = NETWORK_SCORE_FALLBACK if latency is None else clamp(1.0 - min(latency, NETWORK_LATENCY_CEILING_MS) / NETWORK_LATENCY_SCORE_MS)
    download_score = NETWORK_SCORE_FALLBACK if download is None else clamp(download / NETWORK_DOWNLOAD_TARGET_MB_S)
    network_score = (latency_score + download_score) / 2
    pdf_score = clamp(pdf_pages_per_s / PDF_TARGET_PAGES_PER_SECOND)
    thermal_score = THERMAL_SCORE_FALLBACK if thermal_limit is None else clamp(thermal_limit / 100)
    score = (
        cpu_score * CPU_SCORE_WEIGHT
        + load_score * LOAD_SCORE_WEIGHT
        + ((memory_score + memory_pressure_score) / 2) * MEMORY_SCORE_WEIGHT
        + swap_score * SWAP_SCORE_WEIGHT
        + disk_score * DISK_SCORE_WEIGHT
        + storage_score * STORAGE_SCORE_WEIGHT
        + network_score * NETWORK_SCORE_WEIGHT
        + pdf_score * PDF_SCORE_WEIGHT
        + thermal_score * THERMAL_SCORE_WEIGHT
        + power_score * POWER_SCORE_WEIGHT
    )

    emit("benchmark_metric", name="CPU Throughput", value=cpu, unit="MB/s", score=cpu_score, detail="Hashing workload used as a local model proxy.")
    emit("benchmark_metric", name="Average CPU Load", value=cpu_load, unit="%", score=load_score)
    emit("benchmark_metric", name="Free Memory", value=free_memory, unit="GB", score=memory_score)
    emit("benchmark_metric", name="Memory Pressure", value=memory_pressure, unit="%", score=memory_pressure_score)
    emit("benchmark_metric", name="Swap Used", value=swap_used, unit="GB", score=swap_score)
    emit("benchmark_metric", name="Disk Write", value=disk_write, unit="MB/s", score=clamp(disk_write / DISK_WRITE_TARGET_MB_S))
    emit("benchmark_metric", name="Disk Read", value=disk_read, unit="MB/s", score=clamp(disk_read / DISK_READ_TARGET_MB_S))
    emit("benchmark_metric", name="Small-file Latency", value=small_file_ms, unit="ms", score=small_file_score, detail="Proxy for many small PDF and image writes.")
    emit("benchmark_metric", name="Output Free Space", value=disk_free, unit="GB", score=storage_score)
    emit("benchmark_metric", name="PDF Render", value=pdf_pages_per_s, unit="pages/s", score=pdf_score)
    if latency is None:
        emit("benchmark_metric", name="Network Latency", detail="Unavailable during benchmark", score=latency_score)
    else:
        emit("benchmark_metric", name="Network Latency", value=latency, unit="ms", score=latency_score)
    if download is None:
        emit("benchmark_metric", name="Network Download", detail="Unavailable during benchmark", score=download_score)
    else:
        emit("benchmark_metric", name="Network Download", value=download, unit="MB/s", score=download_score)
    if ollama_latency is None:
        emit("benchmark_metric", name="Ollama Response", detail="Ollama was not reachable during benchmark")
    else:
        emit("benchmark_metric", name="Ollama Response", value=ollama_latency, unit="ms", score=clamp(1.0 - min(ollama_latency, 1000) / 1000))
    if thermal_limit is None:
        emit("benchmark_metric", name="Thermal Speed Limit", detail="Unavailable on this Mac", score=thermal_score)
    else:
        emit("benchmark_metric", name="Thermal Speed Limit", value=thermal_limit, unit="%", score=thermal_score)
    emit("benchmark_metric", name="Power Source", detail=power_source, score=power_score)
    if battery_percent is not None:
        emit("benchmark_metric", name="Battery Level", value=battery_percent, unit="%", score=power_score)

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


def disk_probe(output_dir: Path, payload: bytes) -> tuple[float, float, float, float]:
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
        small_file_ms = small_file_latency_ms(output_dir)
        disk_free = shutil.disk_usage(output_dir).free / BYTES_PER_GIBIBYTE
        return size_mb / write_elapsed, size_mb / read_elapsed, disk_free, small_file_ms
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


def small_file_latency_ms(output_dir: Path) -> float:
    payload = b"x" * 8192
    count = 12
    started = time.perf_counter()
    for index in range(count):
        path = output_dir / f".past-paper-small-{os.getpid()}-{index}.tmp"
        try:
            path.write_bytes(payload)
            _ = path.read_bytes()
        finally:
            with contextlib.suppress(OSError):
                path.unlink()
    return (time.perf_counter() - started) * 1000 / count


def network_probe() -> tuple[float | None, float | None]:
    return network_latency_ms(), network_download_mb_s()


def network_latency_ms() -> float | None:
    started = time.perf_counter()
    try:
        request = urllib.request.Request(
            NETWORK_PROBE_URL,
            headers={"User-Agent": "PaperCreatorBenchmark/1.0"},
        )
        with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            response.read(128)
            if response.status >= 400:
                return None
    except (OSError, TimeoutError, urllib.error.URLError):
        return None
    return (time.perf_counter() - started) * 1000


def network_download_mb_s() -> float | None:
    started = time.perf_counter()
    try:
        request = urllib.request.Request(
            NETWORK_DOWNLOAD_URL,
            headers={"User-Agent": "PaperCreatorBenchmark/1.0"},
        )
        with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            total = 0
            while chunk := response.read(64 * 1024):
                total += len(chunk)
            if response.status >= 400 or total == 0:
                return None
    except (OSError, TimeoutError, urllib.error.URLError):
        return None
    elapsed = max(0.001, time.perf_counter() - started)
    return total / elapsed / BYTES_PER_MEGABYTE


def ollama_latency_ms() -> float | None:
    started = time.perf_counter()
    try:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/tags",
            headers={"User-Agent": "PaperCreatorBenchmark/1.0"},
        )
        with urllib.request.urlopen(request, timeout=0.8) as response:
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


def memory_snapshot() -> tuple[float, float, float]:
    total = total_memory_gb()
    available = available_memory_gb()
    pressure = system_memory_pressure_percent()
    if pressure is None:
        pressure = 0.0 if total <= 0 else clamp((total - available) / total, upper=1.0) * 100
    return available, pressure, swap_used_gb()


def system_memory_pressure_percent() -> float | None:
    if platform.system() != "Darwin":
        return None
    try:
        output = subprocess.check_output(["memory_pressure", "-Q"], text=True, stderr=subprocess.DEVNULL, timeout=1.0)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"free percentage:\s*(\d+)%", output)
    if not match:
        return None
    return 100.0 - float(match.group(1))


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


def swap_used_gb() -> float:
    if platform.system() == "Darwin":
        try:
            raw = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True, stderr=subprocess.DEVNULL)
            match = re.search(r"used\s*=\s*([0-9.]+)([MGT])", raw)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                if unit == "G":
                    return value
                if unit == "M":
                    return value / 1024
                if unit == "T":
                    return value * 1024
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return 0.0


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


def thermal_speed_limit_percent() -> float | None:
    if platform.system() != "Darwin":
        return None
    try:
        output = subprocess.check_output(["pmset", "-g", "therm"], text=True, stderr=subprocess.DEVNULL, timeout=1.0)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", output)
    return float(match.group(1)) if match else None


def power_status() -> tuple[str, float | None, float]:
    if platform.system() != "Darwin":
        return "Unknown", None, 0.9
    try:
        output = subprocess.check_output(["pmset", "-g", "batt"], text=True, stderr=subprocess.DEVNULL, timeout=1.0)
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return "Unknown", None, 0.9

    source = "AC Power" if "AC Power" in output else "Battery Power" if "Battery Power" in output else "Unknown"
    match = re.search(r"(\d+)%", output)
    battery = float(match.group(1)) if match else None
    if source == "AC Power" or battery is None:
        return source, battery, 1.0
    if battery >= 50:
        return source, battery, 0.9
    if battery >= 20:
        return source, battery, 0.7
    return source, battery, 0.4


def pdf_probe(output_dir: Path) -> float:
    fd, raw_path = tempfile.mkstemp(prefix="past-paper-pdf-benchmark-", suffix=".pdf", dir=output_dir)
    os.close(fd)
    path = Path(raw_path)
    pages = 4
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        started = time.perf_counter()
        pdf = canvas.Canvas(str(path), pagesize=A4)
        for page in range(pages):
            pdf.setFont("Helvetica", 11)
            pdf.drawString(72, 780, f"Paper creator diagnostic page {page + 1}")
            for line in range(36):
                y = 744 - line * 18
                pdf.line(72, y, 520, y)
            pdf.showPage()
        pdf.save()
        elapsed = max(0.001, time.perf_counter() - started)
        return pages / elapsed
    except Exception:
        return 0.0
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


def apple_cpu_core_split() -> tuple[float | None, float | None]:
    if platform.system() != "Darwin":
        return None, None
    performance = sysctl_float("hw.perflevel0.physicalcpu")
    efficiency = sysctl_float("hw.perflevel1.physicalcpu")
    return performance, efficiency


def cpu_brand() -> str:
    if platform.system() == "Darwin":
        try:
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or platform.machine()


def sysctl_float(name: str) -> float | None:
    try:
        raw = subprocess.check_output(["sysctl", "-n", name], text=True, stderr=subprocess.DEVNULL, timeout=1.0)
        return float(raw.strip())
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired, ValueError):
        return None


def avg(samples: list[Sample], key: str) -> float:
    values = [float(sample[key]) for sample in samples if sample.get(key) is not None]
    return mean(values) if values else 0


def optional_mean(samples: list[Sample], key: str) -> float | None:
    values = [float(sample[key]) for sample in samples if sample.get(key) is not None]
    return mean(values) if values else None


def latest(samples: list[Sample], key: str) -> float:
    for sample in reversed(samples):
        value = sample.get(key)
        if value is not None:
            return float(value)
    return 0.0


def memory_pressure_score_for(percent: float) -> float:
    if percent <= MEMORY_PRESSURE_COMFORT_PERCENT:
        return 1.0
    span = MEMORY_PRESSURE_CEILING_PERCENT - MEMORY_PRESSURE_COMFORT_PERCENT
    return clamp(1.0 - (percent - MEMORY_PRESSURE_COMFORT_PERCENT) / span)


def clamp(value: float, upper: float = 1.0) -> float:
    return max(0.0, min(upper, value))
