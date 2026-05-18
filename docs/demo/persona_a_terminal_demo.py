#!/usr/bin/env python3
"""Terminal-friendly Persona A demo.

Runs live against the backend when available. If the backend is not reachable,
prints a clearly labeled replay from docs/demo/persona_a_replay.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPLAY_PATH = Path(__file__).with_name("persona_a_replay.json")
SITE_ID = "silverado-fixed-cam-usgs"


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def read_json(url: str, *, method: str = "GET", timeout: float = 5.0) -> dict[str, Any]:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def load_replay() -> dict[str, Any]:
    return json.loads(REPLAY_PATH.read_text(encoding="utf-8"))


def runtime_from_live(api: str) -> dict[str, Any]:
    payload = read_json(f"{api}/api/settings/runtime", timeout=4.0)
    acuifero = payload.get("acuifero", {})
    model_path = str(acuifero.get("model_path") or "")
    model = Path(model_path).name if model_path else acuifero.get("multimodal_model")
    return {
        "provider": acuifero.get("provider"),
        "backend": acuifero.get("backend"),
        "multimodal_backend": acuifero.get("multimodal_backend"),
        "vision_backend": acuifero.get("multimodal_vision_backend")
        or acuifero.get("vision_backend"),
        "speculative_decoding": acuifero.get("speculative_decoding"),
        "model": model,
        "node_profile": acuifero.get("node_profile"),
        "p1_runtime_ready": acuifero.get("p1_runtime_ready"),
    }


def sample_from_live(api: str) -> tuple[dict[str, Any], float]:
    start = time.perf_counter()
    payload = read_json(
        f"{api}/api/sites/{SITE_ID}/sample-node-analysis",
        method="POST",
        timeout=90.0,
    )
    elapsed = time.perf_counter() - start
    observation = payload.get("observation", {})
    runner = observation.get("runner") or {}
    return (
        {
            "endpoint": f"/api/sites/{SITE_ID}/sample-node-analysis",
            "source": "live backend call",
            "runner_mode": runner.get("mode") or observation.get("runner_mode"),
            "assessment_mode": observation.get("assessment_mode"),
            "frames_analyzed": observation.get("frames_analyzed"),
            "assessment_level": observation.get("assessment_level"),
            "alert_level": (payload.get("alert") or {}).get("level"),
            "waterline_ratio": observation.get("waterline_ratio"),
            "rise_velocity": observation.get("rise_velocity"),
            "water_level": observation.get("water_level"),
            "crossed_critical_line": observation.get("crossed_critical_line"),
            "confidence": observation.get("confidence"),
        },
        elapsed,
    )


def firewall_from_sample(
    sample: dict[str, Any],
    replay_firewall: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    if mode == "replay":
        return dict(replay_firewall)
    return {
        "cv_backend": "pil-pure-python",
        "waterline_ratio": sample.get("waterline_ratio", replay_firewall.get("waterline_ratio")),
        "rise_velocity": sample.get("rise_velocity", replay_firewall.get("rise_velocity")),
        "water_level": sample.get("water_level") or "not_returned_by_api",
        "crossed_critical_line": sample.get(
            "crossed_critical_line", replay_firewall.get("crossed_critical_line")
        ),
        "confidence": sample.get("confidence") or "see_artifact",
    }


def compact_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--force-replay", action="store_true")
    args = parser.parse_args()

    replay = load_replay()
    mode = "replay"
    elapsed: float | None = None

    if args.force_replay:
        runtime = replay["runtime"]
        sample = replay["sample_analysis"]
    else:
        try:
            runtime = runtime_from_live(args.api)
            sample, elapsed = sample_from_live(args.api)
            mode = "live"
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            runtime = replay["runtime"]
            sample = replay["sample_analysis"]
            print(f"[replay] backend unavailable or incomplete: {exc}", file=sys.stderr)

    firewall = firewall_from_sample(sample, replay["firewall"], mode=mode)

    section("PERSONA A — Acuífero edge node (Raspberry Pi 5)")
    print(f"mode={mode}")
    print("Behind the scenes for the camera signal consumed by Persona C Acto 2.")

    section("Runtime config")
    compact_json(runtime)

    section("Deterministic visual prefilter / PIL")
    compact_json(firewall)

    section("Backend sample-node-analysis")
    print(f"POST {sample['endpoint']}")
    if elapsed is not None:
        print(f"live_elapsed_seconds={elapsed:.2f}")
    compact_json(
        {
            "source": sample.get("source"),
            "runner.mode": sample.get("runner_mode"),
            "assessment_mode": sample.get("assessment_mode"),
            "frames_analyzed": sample.get("frames_analyzed"),
            "assessment_level": sample.get("assessment_level"),
            "alert_level": sample.get("alert_level"),
        }
    )

    section("Bridge to Persona C Acto 2")
    compact_json(replay["acto_2_payload"])
    print("same edge-node channel feeds Persona C Acto 2 demo payload.")
    print("cam=52 is the synchronized Acto 2 payload, not the Silverado sample score.")

    section("Overlay for edit")
    compact_json(replay["benchmark_overlay"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
