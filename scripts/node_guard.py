from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import cv2
import httpx


def _camera_source(raw: str) -> int | str:
    raw = raw.strip()
    if raw.isdigit():
        return int(raw)
    return raw


def _record_clip(source: int | str, target: Path, clip_seconds: float, fps: float) -> None:
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"could not open camera source {source!r}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    source_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    capture_fps = fps if fps > 0 else source_fps if source_fps > 0 else 4.0

    writer = cv2.VideoWriter(
        str(target),
        cv2.VideoWriter_fourcc(*"MJPG"),
        capture_fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"could not create guard clip {target}")

    deadline = time.monotonic() + clip_seconds
    frame_period = 1.0 / capture_fps
    next_frame_at = time.monotonic()
    frames = 0
    try:
        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if not ok:
                time.sleep(0.1)
                continue
            now = time.monotonic()
            if now < next_frame_at:
                continue
            writer.write(frame)
            frames += 1
            next_frame_at = now + frame_period
    finally:
        writer.release()
        capture.release()

    if frames == 0:
        raise RuntimeError("guard clip contained no frames")


def _submit_clip(api_base: str, site_id: str, clip_path: Path, timeout: float) -> dict:
    with clip_path.open("rb") as handle:
        files = {"video": (clip_path.name, handle, "video/x-msvideo")}
        data = {"site_id": site_id}
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{api_base.rstrip('/')}/node/analyze", data=data, files=files)
            response.raise_for_status()
            return response.json()


def main() -> None:
    api_base = os.environ.get("ACUIFERO_API_BASE", "http://127.0.0.1:8000/api")
    site_id = os.environ.get("ACUIFERO_GUARD_SITE_ID", "silverado-fixed-cam-usgs")
    source = _camera_source(os.environ.get("ACUIFERO_CAMERA_SOURCE", "0"))
    interval_seconds = float(os.environ.get("ACUIFERO_GUARD_INTERVAL_SECONDS", "60"))
    clip_seconds = float(os.environ.get("ACUIFERO_GUARD_CLIP_SECONDS", "12"))
    fps = float(os.environ.get("ACUIFERO_GUARD_FPS", "4"))
    timeout = float(os.environ.get("ACUIFERO_GUARD_TIMEOUT_SECONDS", "300"))

    print(
        "Acuifero guard started "
        f"site_id={site_id} source={source!r} interval={interval_seconds}s clip={clip_seconds}s"
    )
    while True:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="acuifero-guard-") as tmp:
            clip_path = Path(tmp) / "guard.avi"
            try:
                _record_clip(source, clip_path, clip_seconds, fps)
                payload = _submit_clip(api_base, site_id, clip_path, timeout)
                observation = payload.get("observation", {})
                alert = payload.get("alert", {})
                print(
                    "guard analysis ok "
                    f"frames={observation.get('frames_analyzed')} "
                    f"level={alert.get('level')} score={alert.get('score')}"
                )
            except Exception as exc:
                print(f"guard analysis failed: {exc}")

        elapsed = time.monotonic() - started
        time.sleep(max(1.0, interval_seconds - elapsed))


if __name__ == "__main__":
    main()
