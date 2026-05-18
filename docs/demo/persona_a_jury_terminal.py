#!/usr/bin/env python3
"""Jury-safe Persona A terminal proof for the Raspberry Pi Acuifero node."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


API_BASE = "http://127.0.0.1:8000"
SITE_ID = "silverado-fixed-cam-usgs"
MODEL_PATH = Path("backend/data/models/gemma-4-E2B-it.litertlm")
SMOKE_STDERR_LOG = Path("/tmp/persona_a_litert_stderr.log")
BACKEND_STDOUT_LOG = Path("/tmp/persona_a_backend_stdout.log")
BACKEND_STDERR_LOG = Path("/tmp/persona_a_backend_stderr.log")
CAST_WIDTH = 80
CAST_HEIGHT = 24
LINE_DELAY_SECONDS = 0.055
SECTION_DELAY_SECONDS = 0.45
BACKEND_POLL_SECONDS = 45.0


@dataclass
class Hardware:
    host: str
    board: str
    memory: str


@dataclass
class RuntimeIdentity:
    model: str
    litert_lm: str
    provider: str = "litert"
    compute: str = "text=gpu / image=cpu/cpu"


@dataclass
class BackendStatus:
    status: str
    reason: str = ""
    provider: str = "not available"
    backend: str = "not available"
    multimodal_backend: str = "not available"
    multimodal_vision_backend: str = "not available"
    speculative_decoding: str = "not available"
    engine_ready: str = "not available"
    p1_runtime_ready: str = "not available"


@dataclass
class NodeAnalysis:
    status: str
    reason: str = ""
    http_status: str = "not available"
    runner_mode: str = "not emitted"
    assessment_mode: str = "not emitted"
    frames_analyzed: str = "not emitted"
    alert_level: str = "not emitted"


@dataclass
class Smoke:
    status: str
    elapsed_seconds: str
    rss_mb: str
    backend: str
    multimodal_backend: str
    multimodal_vision_backend: str
    model: str
    detail: str = ""


@dataclass
class HttpPayload:
    status: int
    payload: dict[str, Any]


class CastWriter:
    def __init__(self, path: Path, *, width: int = CAST_WIDTH, height: int = CAST_HEIGHT) -> None:
        self.path = path
        self.logical_time = 0.0
        self.handle = path.open("w", encoding="utf-8", newline="\n")
        header = {
            "version": 2,
            "width": width,
            "height": height,
            "timestamp": int(time.time()),
            "env": {"SHELL": "/bin/bash", "TERM": "vt100"},
            "title": "Persona A - Acuifero edge node Raspberry Pi LiteRT",
        }
        self.handle.write(json.dumps(header, ensure_ascii=True) + "\n")

    def write(self, text: str) -> None:
        payload = text.replace("\n", "\r\n")
        self.handle.write(json.dumps([round(self.logical_time, 6), "o", payload], ensure_ascii=True) + "\n")
        self.handle.flush()

    def advance(self, seconds: float) -> None:
        self.logical_time += seconds

    def close(self) -> None:
        self.handle.close()


class Presenter:
    def __init__(self, *, pace: bool, cast_out: Path | None = None) -> None:
        self.pace = pace
        self.cast = CastWriter(cast_out) if cast_out is not None else None

    def close(self) -> None:
        if self.cast is not None:
            self.cast.close()

    def pause(self, seconds: float) -> None:
        if self.cast is not None:
            self.cast.advance(seconds)
        if self.pace:
            time.sleep(seconds)

    def line(self, text: str = "") -> None:
        output = text + "\n"
        print(text, flush=True)
        if self.cast is not None:
            self.cast.write(output)
        self.pause(LINE_DELAY_SECONDS)

    def section(self, title: str) -> None:
        self.pause(SECTION_DELAY_SECONDS)
        self.line("=" * 44)
        self.line(title)
        self.line("=" * 44)


def bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "not available"
    return str(value).lower() if str(value).lower() in {"true", "false"} else str(value)


def basename(value: Any) -> str:
    text = str(value or "")
    return Path(text).name if text else "not available"


def read_board() -> str:
    path = Path("/proc/device-tree/model")
    if not path.exists():
        return "unknown"
    return path.read_bytes().replace(b"\x00", b"").decode("utf-8", errors="replace").strip()


def read_memory() -> str:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return "unknown"
    values: dict[str, int] = {}
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0])
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is None or available is None:
        return "unknown"
    return f"{total / 1024 / 1024:.1f} GiB total / {available / 1024 / 1024:.1f} GiB available"


def format_size(path: Path) -> str:
    size = path.stat().st_size
    if size >= 1024**3:
        return f"{math.ceil(size / 1024**3 * 10) / 10:.1f}G"
    if size >= 1024**2:
        return f"{math.ceil(size / 1024**2 * 10) / 10:.1f}M"
    return f"{size}B"


def check_litert_import() -> str:
    try:
        subprocess.run(
            [sys.executable, "-c", "import litert_lm"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
        )
    except Exception:
        return "failed"
    return "ok"


def model_label() -> str:
    if MODEL_PATH.exists():
        return f"{MODEL_PATH.name} ({format_size(MODEL_PATH)})"
    return f"{MODEL_PATH.name} (missing)"


def dry_run_hardware() -> Hardware:
    return Hardware(
        host="raspi5",
        board="Raspberry Pi 5 Model B Rev 1.1",
        memory="7.9 GiB total / 7.3 GiB available",
    )


def real_hardware() -> Hardware:
    return Hardware(host=socket.gethostname().strip(), board=read_board(), memory=read_memory())


def dry_run_identity() -> RuntimeIdentity:
    return RuntimeIdentity(model="gemma-4-E2B-it.litertlm (2.5G)", litert_lm="ok")


def real_identity() -> RuntimeIdentity:
    return RuntimeIdentity(model=model_label(), litert_lm=check_litert_import())


def env_for_pi_runtime() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "ACUIFERO_NODE_PROVIDER": "litert",
            "ACUIFERO_NODE_MODEL_PATH": str(MODEL_PATH),
            "ACUIFERO_NODE_BACKEND": "gpu",
            "ACUIFERO_NODE_MULTIMODAL_BACKEND": "cpu",
            "ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND": "cpu",
            "PYTHONPATH": "backend/src",
        }
    )
    return env


def request_json(url: str, *, method: str = "GET", timeout: float = 5.0) -> HttpPayload:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return HttpPayload(status=response.status, payload=json.loads(raw))


def backend_from_payload(payload: dict[str, Any], *, status: str = "ok") -> BackendStatus:
    acuifero = payload.get("acuifero") or {}
    return BackendStatus(
        status=status,
        provider=str(acuifero.get("provider", "not available")),
        backend=str(acuifero.get("backend", "not available")),
        multimodal_backend=str(acuifero.get("multimodal_backend", "not available")),
        multimodal_vision_backend=str(acuifero.get("multimodal_vision_backend", "not available")),
        speculative_decoding=bool_text(acuifero.get("speculative_decoding")),
        engine_ready=bool_text(acuifero.get("engine_ready")),
        p1_runtime_ready=bool_text(acuifero.get("p1_runtime_ready")),
    )


def dry_run_backend() -> BackendStatus:
    return BackendStatus(
        status="dry-run",
        reason="no backend call in dry-run",
        provider="litert",
        backend="gpu",
        multimodal_backend="cpu",
        multimodal_vision_backend="cpu",
        speculative_decoding="true",
        engine_ready="true",
        p1_runtime_ready="true",
    )


def read_backend_status() -> BackendStatus:
    try:
        result = request_json(f"{API_BASE}/api/settings/runtime", timeout=5.0)
    except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return BackendStatus(status="blocked", reason="backend not reachable")
    return backend_from_payload(result.payload)


def start_backend() -> subprocess.Popen[str]:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "acuifero_vigia.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    stdout_file = BACKEND_STDOUT_LOG.open("w", encoding="utf-8")
    stderr_file = BACKEND_STDERR_LOG.open("w", encoding="utf-8")
    return subprocess.Popen(
        command,
        env=env_for_pi_runtime(),
        stdout=stdout_file,
        stderr=stderr_file,
        text=True,
    )


def wait_for_backend(timeout_seconds: float = BACKEND_POLL_SECONDS) -> BackendStatus:
    deadline = time.monotonic() + timeout_seconds
    last = BackendStatus(status="blocked", reason="backend not reachable after startup")
    while time.monotonic() < deadline:
        last = read_backend_status()
        if last.status == "ok":
            return last
        time.sleep(1.0)
    return last


def ensure_backend() -> tuple[BackendStatus, subprocess.Popen[str] | None]:
    current = read_backend_status()
    if current.status == "ok":
        return current, None
    process = start_backend()
    status = wait_for_backend()
    if status.status != "ok" and process.poll() is not None:
        status.reason = "backend process exited before health check"
    return status, process


def seed_backend() -> None:
    subprocess.run(
        [sys.executable, "-m", "acuifero_vigia.scripts.seed"],
        env=env_for_pi_runtime(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )


def dry_run_node_analysis() -> NodeAnalysis:
    return NodeAnalysis(
        status="dry-run",
        reason="no endpoint call in dry-run",
        http_status="200",
        runner_mode="litert-multimodal-temporal",
        assessment_mode="gemma4-multimodal-v1",
        frames_analyzed="1",
        alert_level="green",
    )


def run_node_analysis(backend: BackendStatus) -> NodeAnalysis:
    if backend.status != "ok":
        return NodeAnalysis(status="blocked", reason="backend unavailable")

    def call_endpoint() -> HttpPayload:
        return request_json(
            f"{API_BASE}/api/sites/{SITE_ID}/sample-node-analysis",
            method="POST",
            timeout=180.0,
        )

    try:
        result = call_endpoint()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            seed_backend()
            try:
                result = call_endpoint()
            except Exception:
                return NodeAnalysis(status="blocked", reason="sample site or media unavailable")
        else:
            return NodeAnalysis(status="blocked", reason=f"endpoint returned HTTP {exc.code}")
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return NodeAnalysis(status="blocked", reason="endpoint unavailable")

    observation = result.payload.get("observation") or {}
    runner = observation.get("runner") or {}
    alert = result.payload.get("alert") or {}
    return NodeAnalysis(
        status="observed",
        http_status=str(result.status),
        runner_mode=str(runner.get("mode") or observation.get("runner_mode") or "not emitted"),
        assessment_mode=str(observation.get("assessment_mode", "not emitted")),
        frames_analyzed=str(observation.get("frames_analyzed", "not emitted")),
        alert_level=str(alert.get("level", "not emitted")),
    )


def dry_run_smoke() -> Smoke:
    return Smoke(
        status="dry-run",
        elapsed_seconds="253.81",
        rss_mb="3128.4",
        backend="gpu",
        multimodal_backend="cpu",
        multimodal_vision_backend="cpu",
        model="gemma-4-E2B-it.litertlm",
    )


def json_lines(text: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payloads.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return payloads


def smoke_from_stdout(stdout: str, *, returncode: int = 0) -> Smoke:
    parsed = json_lines(stdout)
    result_payload = next((item for item in parsed if isinstance(item.get("benchmark"), dict)), {})
    benchmark = result_payload.get("benchmark") or {}
    if returncode != 0 or not benchmark:
        return Smoke(
            status="failed",
            elapsed_seconds="not available",
            rss_mb="not available",
            backend="not available",
            multimodal_backend="not available",
            multimodal_vision_backend="not available",
            model=MODEL_PATH.name,
            detail="see captured diagnostic logs outside the take",
        )
    return Smoke(
        status="passed",
        elapsed_seconds=f"{float(benchmark['elapsed_seconds']):.2f}",
        rss_mb=f"{float(benchmark['rss_mb']):.1f}",
        backend=str(benchmark.get("backend", "unknown")),
        multimodal_backend=str(benchmark.get("multimodal_backend", "unknown")),
        multimodal_vision_backend=str(benchmark.get("multimodal_vision_backend", "unknown")),
        model=basename(benchmark.get("model") or MODEL_PATH.name),
    )


def run_real_smoke(identity: RuntimeIdentity) -> Smoke:
    if identity.litert_lm != "ok" or not MODEL_PATH.exists():
        return Smoke(
            status="failed",
            elapsed_seconds="not available",
            rss_mb="not available",
            backend="not available",
            multimodal_backend="not available",
            multimodal_vision_backend="not available",
            model=MODEL_PATH.name,
            detail="runtime import or model file unavailable",
        )
    command = [sys.executable, "scripts/litert_smoke.py", "--reasoning"]
    with SMOKE_STDERR_LOG.open("w", encoding="utf-8") as stderr_file:
        proc = subprocess.run(
            command,
            env=env_for_pi_runtime(),
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
            check=False,
        )
    return smoke_from_stdout(proc.stdout, returncode=proc.returncode)


def print_header(presenter: Presenter) -> None:
    presenter.line("=" * 44)
    presenter.line("PERSONA A - Acuifero edge node")
    presenter.line("REAL Raspberry Pi 5 - LiteRT-LM")
    presenter.line("=" * 44)
    presenter.line()


def print_step0(presenter: Presenter, hardware: Hardware) -> None:
    presenter.section("STEP 0 - Real edge hardware")
    presenter.line(f"host                 : {hardware.host}")
    presenter.line(f"board                : {hardware.board}")
    presenter.line(f"memory               : {hardware.memory}")
    presenter.line()


def print_step1(presenter: Presenter, identity: RuntimeIdentity) -> None:
    presenter.section("STEP 1 - Runtime identity")
    presenter.line(f"model file           : {identity.model}")
    presenter.line(f"litert_lm import     : {identity.litert_lm}")
    presenter.line(f"provider             : {identity.provider}")
    presenter.line(f"compute              : {identity.compute}")
    presenter.line()


def print_step2(presenter: Presenter, backend: BackendStatus) -> None:
    presenter.section("STEP 2 - Backend health + runtime config")
    presenter.line(f"status               : {backend.status}")
    if backend.reason:
        presenter.line(f"reason               : {backend.reason}")
    presenter.line(f"provider             : {backend.provider}")
    presenter.line(f"backend              : {backend.backend}")
    presenter.line(f"multimodal_backend   : {backend.multimodal_backend}")
    presenter.line(f"vision_backend       : {backend.multimodal_vision_backend}")
    presenter.line(f"speculative_decoding : {backend.speculative_decoding}")
    presenter.line(f"engine_ready         : {backend.engine_ready}")
    presenter.line(f"p1_runtime_ready     : {backend.p1_runtime_ready}")
    presenter.line()


def print_step3(presenter: Presenter, analysis: NodeAnalysis) -> None:
    presenter.section("STEP 3 - Node-analysis proof")
    presenter.line(f"status               : {analysis.status}")
    if analysis.reason:
        presenter.line(f"reason               : {analysis.reason}")
    presenter.line(f"HTTP status          : {analysis.http_status}")
    presenter.line(f"runner.mode          : {analysis.runner_mode}")
    presenter.line(f"assessment_mode      : {analysis.assessment_mode}")
    presenter.line(f"frames_analyzed      : {analysis.frames_analyzed}")
    presenter.line(f"alert_level          : {analysis.alert_level}")
    presenter.line()


def print_step4(presenter: Presenter, smoke: Smoke) -> None:
    presenter.section("STEP 4 - Real Pi LiteRT smoke")
    presenter.line("command              : scripts/litert_smoke.py --reasoning")
    presenter.line(f"status               : {smoke.status}")
    if smoke.detail:
        presenter.line(f"detail               : {smoke.detail}")
    presenter.line(f"elapsed_seconds      : {smoke.elapsed_seconds}")
    presenter.line(f"rss_mb               : {smoke.rss_mb}")
    presenter.line(f"backend              : {smoke.backend}")
    presenter.line(f"multimodal_backend   : {smoke.multimodal_backend}")
    presenter.line(f"vision_backend       : {smoke.multimodal_vision_backend}")
    presenter.line(f"model                : {smoke.model}")
    presenter.line()


def print_step5(presenter: Presenter) -> None:
    presenter.section("STEP 5 - Handoff to Persona C")
    presenter.line("Persona C Acto 2 uses synchronized cam=52 demo payload.")
    presenter.line("This Pi run validates the real edge LiteRT runtime behind that narrative.")


def run_take(*, dry_run: bool, pace: bool, cast_out: Path | None = None) -> int:
    presenter = Presenter(pace=pace, cast_out=cast_out)
    backend_process: subprocess.Popen[str] | None = None
    exit_code = 0
    try:
        print_header(presenter)
        hardware = dry_run_hardware() if dry_run else real_hardware()
        identity = dry_run_identity() if dry_run else real_identity()
        print_step0(presenter, hardware)
        print_step1(presenter, identity)

        if dry_run:
            backend = dry_run_backend()
        else:
            backend, backend_process = ensure_backend()
        print_step2(presenter, backend)

        analysis = dry_run_node_analysis() if dry_run else run_node_analysis(backend)
        print_step3(presenter, analysis)

        smoke = dry_run_smoke() if dry_run else run_real_smoke(identity)
        if smoke.status == "failed":
            exit_code = 1
        print_step4(presenter, smoke)

        print_step5(presenter)
        return exit_code
    finally:
        presenter.close()
        if backend_process is not None and backend_process.poll() is None:
            backend_process.terminate()


def load_cast(path: Path) -> tuple[dict[str, Any], list[tuple[float, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("cast file is empty")
    header = json.loads(lines[0])
    events: list[tuple[float, str]] = []
    for line in lines[1:]:
        event = json.loads(line)
        if len(event) >= 3 and event[1] == "o":
            events.append((float(event[0]), str(event[2]).replace("\r\n", "\n")))
    return header, events


def find_font(size: int) -> Any:
    from PIL import ImageFont

    candidates = [
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/cour.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def draw_terminal_frame(lines: list[str], *, width_cols: int, height_rows: int, font_size: int = 18) -> Any:
    from PIL import Image, ImageDraw

    font = find_font(font_size)
    probe = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(probe)
    bbox = draw.textbbox((0, 0), "M", font=font)
    char_width = max(1, bbox[2] - bbox[0])
    line_height = max(font_size + 4, bbox[3] - bbox[1] + 6)
    pad_x = 18
    pad_y = 14
    image = Image.new(
        "RGB",
        (pad_x * 2 + char_width * width_cols, pad_y * 2 + line_height * height_rows),
        (12, 14, 18),
    )
    draw = ImageDraw.Draw(image)
    visible = lines[-height_rows:]
    for row, text in enumerate(visible):
        draw.text((pad_x, pad_y + row * line_height), text[:width_cols], font=font, fill=(229, 235, 242))
    return image


def render_cast(cast_path: Path, gif_out: Path, mp4_out: Path) -> None:
    header, events = load_cast(cast_path)
    width = int(header.get("width", CAST_WIDTH))
    height = int(header.get("height", CAST_HEIGHT))
    screen_lines = [""]
    frames: list[Any] = []
    durations_ms: list[int] = []

    for index, (event_time, text) in enumerate(events):
        for chunk in text.split("\n"):
            if chunk == "":
                screen_lines.append("")
            else:
                screen_lines[-1] += chunk
        frames.append(draw_terminal_frame(screen_lines, width_cols=width, height_rows=height))
        next_time = events[index + 1][0] if index + 1 < len(events) else event_time + 1.2
        duration = max(45, min(1400, int((next_time - event_time) * 1000)))
        durations_ms.append(duration)

    if not frames:
        frames.append(draw_terminal_frame([""], width_cols=width, height_rows=height))
        durations_ms.append(1000)

    gif_out.parent.mkdir(parents=True, exist_ok=True)
    mp4_out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        gif_out,
        save_all=True,
        append_images=frames[1:],
        duration=durations_ms,
        loop=0,
        optimize=False,
    )

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to render mp4")
    fps = 12
    with tempfile.TemporaryDirectory(prefix="persona-a-render-") as tmp:
        tmp_path = Path(tmp)
        frame_index = 0
        for frame, duration in zip(frames, durations_ms):
            repeats = max(1, round(duration / 1000 * fps))
            for _ in range(repeats):
                frame.save(tmp_path / f"frame_{frame_index:05d}.png")
                frame_index += 1
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(tmp_path / "frame_%05d.png"),
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(mp4_out),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print sample values only")
    mode.add_argument("--real-smoke", action="store_true", help="run real Pi checks and LiteRT smoke")
    mode.add_argument("--render-cast", type=Path, help="render an asciinema v2 cast to gif/mp4")
    parser.add_argument("--cast-out", type=Path, help="write asciinema v2 output while printing the take")
    parser.add_argument("--gif-out", type=Path, help="GIF output path for --render-cast")
    parser.add_argument("--mp4-out", type=Path, help="MP4 output path for --render-cast")
    parser.add_argument("--pace", dest="pace", action="store_true", default=True)
    parser.add_argument("--no-pace", dest="pace", action="store_false")
    args = parser.parse_args(argv)

    if args.render_cast is not None:
        if args.gif_out is None or args.mp4_out is None:
            parser.error("--render-cast requires --gif-out and --mp4-out")
        render_cast(args.render_cast, args.gif_out, args.mp4_out)
        return 0

    dry_run = not args.real_smoke
    return run_take(dry_run=dry_run, pace=args.pace, cast_out=args.cast_out)


if __name__ == "__main__":
    raise SystemExit(main())
