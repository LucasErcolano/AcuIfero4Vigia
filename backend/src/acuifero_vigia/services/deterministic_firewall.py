"""Deterministic OpenCV firewall executed before the multimodal LLM.

Runs cheap per-frame computer vision on curated frames to produce a numeric
vector (waterline_ratio, rise_velocity, brightness, contrast, edge strength,
motion) that the downstream Gemma runner can use as anti-hallucination context.

If OpenCV is unavailable at import time we degrade gracefully: every metric is
returned as -1.0 and `opencv_used=False`, matching the previous behaviour.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np

    _CV2_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    _CV2_AVAILABLE = False


@dataclass
class FrameMetrics:
    index: int
    timestamp_s: float
    brightness: float
    contrast: float
    edge_strength: float
    motion_score: float
    waterline_y: int
    waterline_ratio: float


@dataclass
class FirewallResult:
    opencv_used: bool
    frames: list[FrameMetrics] = field(default_factory=list)
    waterline_ratio: float = 0.0
    rise_velocity: float = 0.0
    crossed_critical_line: bool = False
    confidence: float = 0.0
    water_level: str = "unknown"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "opencv_used": self.opencv_used,
            "waterline_ratio": round(self.waterline_ratio, 4),
            "rise_velocity": round(self.rise_velocity, 4),
            "crossed_critical_line": self.crossed_critical_line,
            "confidence": round(self.confidence, 3),
            "water_level": self.water_level,
            "frames": [
                {
                    "index": f.index,
                    "timestamp_s": f.timestamp_s,
                    "brightness": round(f.brightness, 2),
                    "contrast": round(f.contrast, 2),
                    "edge_strength": round(f.edge_strength, 3),
                    "motion_score": round(f.motion_score, 3),
                    "waterline_y": f.waterline_y,
                    "waterline_ratio": round(f.waterline_ratio, 4),
                }
                for f in self.frames
            ],
            "notes": self.notes,
        }


def _classify_water_level(ratio: float, rise_velocity: float, crossed: bool) -> str:
    if crossed or ratio >= 0.55 or rise_velocity >= 0.10:
        return "critical"
    if ratio >= 0.30 or rise_velocity >= 0.03:
        return "elevated"
    return "low"


def _empty_result(frame_paths: Sequence[str], sample_seconds: float, reason: str) -> FirewallResult:
    frames = [
        FrameMetrics(
            index=i,
            timestamp_s=round(i * sample_seconds, 2),
            brightness=-1.0,
            contrast=-1.0,
            edge_strength=-1.0,
            motion_score=-1.0,
            waterline_y=-1,
            waterline_ratio=-1.0,
        )
        for i in range(len(frame_paths))
    ]
    return FirewallResult(opencv_used=False, frames=frames, notes=[reason])


def analyze_frames(
    frame_paths: Sequence[str],
    sample_seconds: float,
    *,
    critical_line_ratio: float = 0.5,
) -> FirewallResult:
    if not _CV2_AVAILABLE:
        return _empty_result(frame_paths, sample_seconds, "opencv not installed")
    if not frame_paths:
        return FirewallResult(opencv_used=True, notes=["no frames"])

    metrics: list[FrameMetrics] = []
    prev_gray = None
    for idx, path in enumerate(frame_paths):
        image = cv2.imread(str(Path(path)))
        if image is None:
            metrics.append(
                FrameMetrics(
                    index=idx,
                    timestamp_s=round(idx * sample_seconds, 2),
                    brightness=-1.0,
                    contrast=-1.0,
                    edge_strength=-1.0,
                    motion_score=-1.0,
                    waterline_y=-1,
                    waterline_ratio=-1.0,
                )
            )
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        brightness = float(gray.mean())
        contrast = float(gray.std())

        edges = cv2.Canny(gray, threshold1=60, threshold2=160)
        edge_strength = float(edges.mean() / 255.0)

        row_edge_density = edges.sum(axis=1) / max(1, width * 255)
        search_start = height // 3
        search_region = row_edge_density[search_start:]
        if search_region.size > 0 and float(search_region.max()) > 0.0:
            waterline_y = int(search_start + int(np.argmax(search_region)))
        else:
            waterline_y = -1
        waterline_ratio = (height - waterline_y) / height if waterline_y > 0 else 0.0

        if prev_gray is not None and prev_gray.shape == gray.shape:
            diff = cv2.absdiff(prev_gray, gray)
            motion_score = float(diff.mean() / 255.0)
        else:
            motion_score = 0.0
        prev_gray = gray

        metrics.append(
            FrameMetrics(
                index=idx,
                timestamp_s=round(idx * sample_seconds, 2),
                brightness=brightness,
                contrast=contrast,
                edge_strength=edge_strength,
                motion_score=motion_score,
                waterline_y=waterline_y,
                waterline_ratio=waterline_ratio,
            )
        )

    valid_ratios = [m.waterline_ratio for m in metrics if m.waterline_ratio > 0.0]
    last_ratio = valid_ratios[-1] if valid_ratios else 0.0
    first_ratio = valid_ratios[0] if valid_ratios else 0.0
    duration_s = max(sample_seconds * max(1, len(valid_ratios) - 1), 1.0)
    rise_velocity = (last_ratio - first_ratio) / duration_s
    crossed = last_ratio >= critical_line_ratio
    water_level = _classify_water_level(last_ratio, rise_velocity, crossed)

    valid_count = sum(1 for m in metrics if m.waterline_y > 0)
    confidence = valid_count / max(1, len(metrics))

    result = FirewallResult(
        opencv_used=True,
        frames=metrics,
        waterline_ratio=last_ratio,
        rise_velocity=rise_velocity,
        crossed_critical_line=crossed,
        confidence=confidence,
        water_level=water_level,
    )

    logger.info(
        "deterministic_firewall waterline_ratio=%.3f rise_velocity=%.4f crossed=%s water_level=%s frames=%d",
        last_ratio,
        rise_velocity,
        crossed,
        water_level,
        len(metrics),
    )
    return result
