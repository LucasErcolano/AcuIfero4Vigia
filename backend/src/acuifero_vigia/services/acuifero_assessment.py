from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

import cv2
import numpy as np

from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.models.domain import Site, SiteCalibration
from acuifero_vigia.services.calibration import build_calibration_config
from acuifero_vigia.services.storage import persist_frame_image, persist_json_artifact


@dataclass
class EvidenceFrame:
    frame_path: str
    timestamp_s: float
    brightness: float
    contrast: float
    motion_score: float
    edge_strength: float
    waterline_ratio_hint: float
    waterline_y: int


@dataclass
class AssessmentArtifactPack:
    manifest_path: str
    selected_frame_paths: list[str]
    evidence_frame_path: str


@dataclass
class AssessmentVerdict:
    assessment_level: str
    assessment_score: float
    temporal_summary: str
    reasoning_summary: str
    reasoning_steps: list[str]
    critical_evidence: dict[str, Any]
    runner_name: str
    runner_mode: str
    fallback_used: bool


@dataclass
class TemporalEvidencePack:
    site_id: str
    site_name: str
    site_region: str
    video_path: str
    source_type: str
    started_at: datetime
    ended_at: datetime
    frames_analyzed: int
    selected_frames: list[EvidenceFrame]
    evidence_frame_path: str
    reference_y: float
    critical_y: float
    summary_metrics: dict[str, Any]
    artifact_pack: AssessmentArtifactPack


@dataclass
class AcuiferoAssessment:
    evidence_pack: TemporalEvidencePack
    verdict: AssessmentVerdict
    waterline_ratio_hint: float
    rise_velocity_hint: float
    crossed_critical_line_hint: bool
    confidence: float
    decision_trace: list[str]


class GemmaAssessmentRunner(Protocol):
    def assess(self, pack: TemporalEvidencePack) -> AssessmentVerdict | None: ...


@dataclass
class _Sample:
    waterline_y: int
    ratio: float
    edge_strength: float
    motion_score: float
    brightness: float
    contrast: float
    frame: np.ndarray
    timestamp_s: float


def _smooth_series(values: np.ndarray, kernel_size: int = 9) -> np.ndarray:
    if values.size == 0:
        return values

    kernel_size = max(3, kernel_size)
    if kernel_size % 2 == 0:
        kernel_size += 1

    kernel = np.ones(kernel_size, dtype=np.float32) / float(kernel_size)
    padding = kernel_size // 2
    padded = np.pad(values.astype(np.float32), (padding, padding), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def _normalize_by_percentile(values: np.ndarray, lower: int = 10, upper: int = 90) -> np.ndarray:
    if values.size == 0:
        return values

    low = float(np.percentile(values, lower))
    high = float(np.percentile(values, upper))
    if high <= low + 1e-6:
        return np.ones_like(values, dtype=np.float32) if high > 0 else np.zeros_like(values, dtype=np.float32)
    return np.clip((values - low) / (high - low), 0.0, 1.0).astype(np.float32)


def _level_from_score(score: float) -> str:
    if score >= 0.82:
        return "red"
    if score >= 0.62:
        return "orange"
    if score >= 0.4:
        return "yellow"
    return "green"


class TemporalEvidenceBuilder:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build(
        self,
        site: Site,
        video_path: str,
        calibration: SiteCalibration | None,
        source_type: str,
    ) -> tuple[TemporalEvidencePack, float, float, bool, float, list[str]]:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 1.0
        sample_step = max(int(round(fps)), 1)

        samples: list[_Sample] = []
        frame_index = 0
        previous_gray: np.ndarray | None = None
        config = None
        mask: np.ndarray | None = None
        width = 0
        height = 0
        search_top = 0
        search_bottom = 0
        critical_y = 0.0
        reference_y = 0.0
        low_visibility_frames = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % sample_step != 0:
                frame_index += 1
                continue

            height, width = frame.shape[:2]
            if config is None:
                config = build_calibration_config(calibration, width, height)
                mask = np.zeros((height, width), dtype=np.uint8)
                polygon = np.array(config.roi_polygon, dtype=np.int32)
                cv2.fillPoly(mask, [polygon], 255)

                critical_y = float((config.critical_line[0][1] + config.critical_line[1][1]) / 2)
                reference_y = float((config.reference_line[0][1] + config.reference_line[1][1]) / 2)

                roi_y_min = max(min(point[1] for point in config.roi_polygon), 0)
                roi_y_max = min(max(point[1] for point in config.roi_polygon), height - 1)
                band_margin = max(int(abs(reference_y - critical_y) * 0.75), int(height * 0.06))
                search_top = max(roi_y_min, int(min(reference_y, critical_y) - band_margin))
                search_bottom = min(roi_y_max, int(max(reference_y, critical_y) + band_margin))
                if search_bottom <= search_top:
                    search_top = roi_y_min
                    search_bottom = roi_y_max

            assert config is not None
            assert mask is not None

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            roi_pixels = gray[mask > 0]
            if roi_pixels.size == 0:
                frame_index += 1
                continue

            brightness = float(roi_pixels.mean())
            contrast = float(roi_pixels.std())
            if brightness < 12.0 or contrast < 3.0:
                low_visibility_frames += 1
                previous_gray = gray
                frame_index += 1
                continue

            sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            edge_map = np.abs(sobel_y)
            edge_map[mask == 0] = 0

            row_band = edge_map[search_top:search_bottom].astype(np.float32)
            row_mask = (mask[search_top:search_bottom] > 0).astype(np.float32)
            row_coverage = row_mask.sum(axis=1)
            valid_rows = row_coverage > 0
            if not np.any(valid_rows):
                previous_gray = gray
                frame_index += 1
                continue

            row_energy = np.zeros(row_band.shape[0], dtype=np.float32)
            row_energy[valid_rows] = row_band.sum(axis=1)[valid_rows] / row_coverage[valid_rows]
            row_energy = _smooth_series(row_energy, 11)
            best_row_offset = int(np.argmax(row_energy))
            waterline_y = int(search_top + best_row_offset)
            edge_strength = float(row_energy[best_row_offset])

            motion_score = 0.0
            if previous_gray is not None:
                delta = cv2.absdiff(gray, previous_gray)
                motion_score = float(delta[mask > 0].mean() / 255.0)
            previous_gray = gray

            denominator = max(abs(reference_y - critical_y), 1.0)
            ratio = float((reference_y - waterline_y) / denominator)
            timestamp_s = frame_index / fps
            samples.append(
                _Sample(
                    waterline_y=waterline_y,
                    ratio=ratio,
                    edge_strength=edge_strength,
                    motion_score=motion_score,
                    brightness=brightness,
                    contrast=contrast,
                    frame=frame.copy(),
                    timestamp_s=timestamp_s,
                )
            )
            frame_index += 1

        capture.release()

        if not samples or config is None:
            raise ValueError("The uploaded video did not produce usable frames for analysis")

        waterline_values = np.array([sample.waterline_y for sample in samples], dtype=np.float32)
        ratio_values = np.array([sample.ratio for sample in samples], dtype=np.float32)
        edge_values = np.array([sample.edge_strength for sample in samples], dtype=np.float32)
        motion_values = np.array([sample.motion_score for sample in samples], dtype=np.float32)
        contrast_values = np.array([sample.contrast for sample in samples], dtype=np.float32)

        activity_values = np.clip(
            0.65 * _normalize_by_percentile(edge_values, 15, 95)
            + 0.35 * _normalize_by_percentile(motion_values, 25, 95),
            0.0,
            1.0,
        )
        clarity_values = _normalize_by_percentile(contrast_values, 10, 90)

        window_size = min(20, len(samples))
        if len(samples) > 6:
            window_size = max(6, window_size)

        best_start = 0
        best_score = -1.0
        for start in range(0, len(samples) - window_size + 1):
            end = start + window_size
            window_ratio = np.maximum(ratio_values[start:end], 0.0)
            window_activity = activity_values[start:end]
            active_mask = window_activity >= 0.25
            usable_ratio = window_ratio[active_mask] if np.any(active_mask) else window_ratio
            score = float(np.median(usable_ratio) * 0.8 + np.mean(window_activity) * 0.2)
            if score > best_score:
                best_score = score
                best_start = start

        best_end = best_start + window_size
        window_slice = slice(best_start, best_end)
        window_samples = samples[window_slice]
        window_ratio = ratio_values[window_slice]
        window_waterline = waterline_values[window_slice]
        window_activity = activity_values[window_slice]
        window_clarity = clarity_values[window_slice]
        active_mask = window_activity >= 0.25
        if int(np.sum(active_mask)) < max(2, len(window_samples) // 4):
            active_mask = np.ones(len(window_samples), dtype=bool)

        selected_ratios = window_ratio[active_mask]
        selected_waterlines = window_waterline[active_mask]
        selected_activity = window_activity[active_mask]
        selected_clarity = window_clarity[active_mask]
        selected_median_ratio = float(np.median(selected_ratios))

        active_indices = np.flatnonzero(active_mask)
        elapsed = max(
            window_samples[int(active_indices[-1])].timestamp_s - window_samples[int(active_indices[0])].timestamp_s,
            1.0,
        )
        rise_velocity = float((selected_ratios[-1] - selected_ratios[0]) / elapsed)
        crossed_count = int(np.sum(selected_waterlines <= critical_y))
        crossed_critical_line = crossed_count >= max(1, len(selected_waterlines) // 3)

        consistency = float(
            max(0.0, 1.0 - (np.std(selected_waterlines) / max(abs(reference_y - critical_y) * 2.0, 1.0)))
        )
        coverage = float(np.mean(active_mask))
        activity = float(np.mean(selected_activity))
        clarity = float(np.mean(selected_clarity))
        confidence = float(
            np.clip(0.18 + 0.28 * consistency + 0.24 * coverage + 0.18 * activity + 0.12 * clarity, 0.05, 0.99)
        )

        evidence_offset = int(active_indices[int(np.argmax(selected_ratios))]) if len(selected_ratios) else len(window_samples) - 1
        evidence_sample = window_samples[evidence_offset]
        evidence_frame = evidence_sample.frame.copy()
        cv2.polylines(evidence_frame, [np.array(config.roi_polygon, dtype=np.int32)], True, (0, 255, 255), 2)
        cv2.line(evidence_frame, config.critical_line[0], config.critical_line[1], (0, 0, 255), 2)
        cv2.line(evidence_frame, config.reference_line[0], config.reference_line[1], (0, 255, 0), 2)
        cv2.line(
            evidence_frame,
            (0, int(evidence_sample.waterline_y)),
            (width - 1, int(evidence_sample.waterline_y)),
            (255, 200, 0),
            2,
        )
        evidence_frame_path = persist_frame_image(evidence_frame, "acuifero-evidence")

        selected_positions = self._select_curated_indices(len(window_samples), evidence_offset)
        selected_frames: list[EvidenceFrame] = []
        selected_frame_paths: list[str] = []
        for position in selected_positions:
            sample = window_samples[position]
            frame_path = persist_frame_image(sample.frame, "acuifero-frame")
            selected_frame_paths.append(frame_path)
            selected_frames.append(
                EvidenceFrame(
                    frame_path=frame_path,
                    timestamp_s=round(sample.timestamp_s, 2),
                    brightness=round(sample.brightness, 3),
                    contrast=round(sample.contrast, 3),
                    motion_score=round(sample.motion_score, 5),
                    edge_strength=round(sample.edge_strength, 5),
                    waterline_ratio_hint=round(sample.ratio, 5),
                    waterline_y=int(sample.waterline_y),
                )
            )

        duration_seconds = max(window_samples[-1].timestamp_s - window_samples[0].timestamp_s, 1.0)
        ended_at = datetime.utcnow()
        started_at = ended_at - timedelta(seconds=duration_seconds)
        trend = "rising" if rise_velocity > 0.002 else "falling" if rise_velocity < -0.001 else "stable"

        summary_metrics = {
            "window_start_index": best_start,
            "window_end_index": best_end,
            "sampled_frames": len(samples),
            "selected_window_frames": len(window_samples),
            "selected_curated_frames": len(selected_frames),
            "median_ratio_hint": round(selected_median_ratio, 4),
            "peak_ratio_hint": round(float(np.max(selected_ratios)), 4),
            "rise_velocity_hint": round(rise_velocity, 5),
            "crossed_critical_line_hint": crossed_critical_line,
            "crossed_count": crossed_count,
            "confidence": round(confidence, 4),
            "activity_mean": round(activity, 4),
            "clarity_mean": round(clarity, 4),
            "low_visibility_frames": low_visibility_frames,
            "trend_hint": trend,
            "reference_y": round(reference_y, 2),
            "critical_y": round(critical_y, 2),
        }

        decision_trace = [
            f"sampled {len(samples)} usable frames at ~1 FPS",
            f"curated {len(selected_frames)} temporal frames for Gemma",
            f"window ratio hint median={selected_median_ratio:.2f}",
            f"crossed critical hint in {crossed_count}/{len(selected_waterlines)} active frames",
            f"rise velocity hint={rise_velocity:.4f} ratio/sec with confidence={confidence:.2f}",
        ]

        pack = TemporalEvidencePack(
            site_id=site.id,
            site_name=site.name,
            site_region=site.region,
            video_path=video_path,
            source_type=source_type,
            started_at=started_at,
            ended_at=ended_at,
            frames_analyzed=len(samples),
            selected_frames=selected_frames,
            evidence_frame_path=evidence_frame_path,
            reference_y=reference_y,
            critical_y=critical_y,
            summary_metrics=summary_metrics,
            artifact_pack=AssessmentArtifactPack(
                manifest_path="",
                selected_frame_paths=selected_frame_paths,
                evidence_frame_path=evidence_frame_path,
            ),
        )
        return pack, selected_median_ratio, rise_velocity, crossed_critical_line, confidence, decision_trace

    def _select_curated_indices(self, total_frames: int, evidence_offset: int) -> list[int]:
        if total_frames <= 0:
            return []
        target = min(total_frames, max(1, self.settings.acuifero_max_curated_frames))
        raw_positions = np.linspace(0, total_frames - 1, num=target, dtype=int).tolist()
        positions = sorted(set(int(position) for position in raw_positions))
        if evidence_offset not in positions:
            positions.append(int(evidence_offset))
        positions = sorted(set(min(max(position, 0), total_frames - 1) for position in positions))
        while len(positions) > target:
            removable = 0 if positions[0] != evidence_offset else 1
            positions.pop(removable)
        return positions


class AcuiferoAssessmentEngine:
    def __init__(
        self,
        builder: TemporalEvidenceBuilder,
        runner: GemmaAssessmentRunner,
    ) -> None:
        self.builder = builder
        self.runner = runner

    def assess_video(
        self,
        site: Site,
        video_path: str,
        calibration: SiteCalibration | None,
        source_type: str,
    ) -> AcuiferoAssessment:
        pack, ratio_hint, rise_velocity_hint, crossed_hint, confidence, trace = self.builder.build(
            site=site,
            video_path=video_path,
            calibration=calibration,
            source_type=source_type,
        )
        verdict = self.runner.assess(pack)
        if verdict is None:
            verdict = self._fallback_verdict(pack, ratio_hint, rise_velocity_hint, crossed_hint, confidence)
            trace.append("Gemma runner unavailable or invalid, used deterministic fallback")
        else:
            trace.append(f"Gemma runner {verdict.runner_mode} produced {verdict.assessment_level}")

        manifest_payload = {
            "bundle": self._serialize_pack(pack),
            "verdict": asdict(verdict),
            "decision_trace": trace,
        }
        manifest_path = persist_json_artifact(manifest_payload, "acuifero-assessment")
        pack.artifact_pack.manifest_path = manifest_path

        return AcuiferoAssessment(
            evidence_pack=pack,
            verdict=verdict,
            waterline_ratio_hint=ratio_hint,
            rise_velocity_hint=rise_velocity_hint,
            crossed_critical_line_hint=crossed_hint,
            confidence=confidence,
            decision_trace=trace,
        )

    def _fallback_verdict(
        self,
        pack: TemporalEvidencePack,
        ratio_hint: float,
        rise_velocity_hint: float,
        crossed_hint: bool,
        confidence: float,
    ) -> AssessmentVerdict:
        score = float(np.clip(max(ratio_hint, 0.0), 0.0, 1.0))
        if crossed_hint:
            score = max(score, 0.84)
        if rise_velocity_hint > 0.002:
            score = min(1.0, score + 0.05)
        score = float(np.clip(score * (0.75 + 0.25 * confidence), 0.0, 1.0))
        level = _level_from_score(score)
        crossed_count = int(pack.summary_metrics.get("crossed_count", 0))
        trend_hint = str(pack.summary_metrics.get("trend_hint", "stable"))
        temporal_summary = (
            f"Gemma temporal fallback on {pack.frames_analyzed} frames: trend={trend_hint}, "
            f"peak waterline hint={ratio_hint:.2f}, critical corroboration frames={crossed_count}."
        )
        reasoning_steps = [
            f"ratio_hint={ratio_hint:.2f}",
            f"rise_velocity_hint={rise_velocity_hint:.4f}",
            f"crossed_critical_hint={crossed_hint}",
        ]
        return AssessmentVerdict(
            assessment_level=level,
            assessment_score=round(score, 4),
            temporal_summary=temporal_summary,
            reasoning_summary=(
                "Se preservo el paquete temporal de evidencia, pero el runner Gemma no devolvio un JSON utilizable. "
                "Acuifero aplico un fallback deterministico sobre la secuencia curada."
            ),
            reasoning_steps=reasoning_steps,
            critical_evidence={
                "crossed_count": crossed_count,
                "selected_frames": len(pack.selected_frames),
                "evidence_frame_path": pack.evidence_frame_path,
            },
            runner_name="acuifero-rules",
            runner_mode="deterministic-fallback",
            fallback_used=True,
        )

    @staticmethod
    def _serialize_pack(pack: TemporalEvidencePack) -> dict[str, Any]:
        return {
            "site_id": pack.site_id,
            "site_name": pack.site_name,
            "site_region": pack.site_region,
            "video_path": pack.video_path,
            "source_type": pack.source_type,
            "started_at": pack.started_at.isoformat(),
            "ended_at": pack.ended_at.isoformat(),
            "frames_analyzed": pack.frames_analyzed,
            "selected_frames": [asdict(frame) for frame in pack.selected_frames],
            "evidence_frame_path": pack.evidence_frame_path,
            "reference_y": pack.reference_y,
            "critical_y": pack.critical_y,
            "summary_metrics": pack.summary_metrics,
            "artifact_pack": asdict(pack.artifact_pack),
        }

    @staticmethod
    def bundle_json(pack: TemporalEvidencePack) -> str:
        return json.dumps(AcuiferoAssessmentEngine._serialize_pack(pack), ensure_ascii=True)
