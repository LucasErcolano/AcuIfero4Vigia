from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import cv2
import numpy as np

from acuifero_vigia.models.domain import SiteCalibration
from acuifero_vigia.services.calibration import build_calibration_config
from acuifero_vigia.services.storage import persist_frame_image


@dataclass
class NodeAnalysisResult:
    started_at: datetime
    ended_at: datetime
    frames_analyzed: int
    waterline_ratio: float
    rise_velocity: float
    crossed_critical_line: bool
    confidence: float
    severity_score: float
    evidence_frame_path: str
    decision_trace: list[str]


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
    padded = np.pad(values.astype(np.float32), (padding, padding), mode='edge')
    return np.convolve(padded, kernel, mode='valid')


def _normalize_by_percentile(values: np.ndarray, lower: int = 10, upper: int = 90) -> np.ndarray:
    if values.size == 0:
        return values

    low = float(np.percentile(values, lower))
    high = float(np.percentile(values, upper))
    if high <= low + 1e-6:
        return np.ones_like(values, dtype=np.float32) if high > 0 else np.zeros_like(values, dtype=np.float32)
    return np.clip((values - low) / (high - low), 0.0, 1.0).astype(np.float32)


class NodeAnalyzer:
    def analyze_video(self, video_path: str, calibration: SiteCalibration | None) -> NodeAnalysisResult:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError(f'Could not open video: {video_path}')

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
            raise ValueError('The uploaded video did not produce usable frames for analysis')

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

        median_ratio = float(np.median(selected_ratios))
        active_indices = np.flatnonzero(active_mask)
        elapsed = max(
            window_samples[int(active_indices[-1])].timestamp_s - window_samples[int(active_indices[0])].timestamp_s,
            1.0,
        )
        rise_velocity = float((selected_ratios[-1] - selected_ratios[0]) / elapsed)

        crossed_count = int(np.sum(selected_waterlines <= critical_y))
        crossed_critical_line = crossed_count >= max(1, len(selected_waterlines) // 3)

        consistency = float(max(0.0, 1.0 - (np.std(selected_waterlines) / max(abs(reference_y - critical_y) * 2.0, 1.0))))
        coverage = float(np.mean(active_mask))
        activity = float(np.mean(selected_activity))
        clarity = float(np.mean(selected_clarity))
        confidence = float(np.clip(0.18 + 0.28 * consistency + 0.24 * coverage + 0.18 * activity + 0.12 * clarity, 0.05, 0.99))

        severity_score = float(np.clip(max(median_ratio, 0.0), 0.0, 1.0))
        if crossed_critical_line:
            severity_score = max(severity_score, 0.82)
        if rise_velocity > 0.002:
            severity_score = min(1.0, severity_score + 0.05)
        severity_score = float(np.clip(severity_score * (0.78 + 0.22 * confidence), 0.0, 1.0))

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
        evidence_frame_path = persist_frame_image(evidence_frame, 'evidence')

        duration_seconds = max(window_samples[-1].timestamp_s - window_samples[0].timestamp_s, 1.0)
        ended_at = datetime.utcnow()
        started_at = ended_at - timedelta(seconds=duration_seconds)

        decision_trace = [
            f'sampled {len(samples)} frames at ~1 FPS',
            f'used risk window {best_start + 1}-{best_end} with median ratio={median_ratio:.2f}',
            f'critical line crossed in {crossed_count}/{len(selected_waterlines)} active frames',
            f'rise velocity={rise_velocity:.4f} ratio/sec',
            f'confidence={confidence:.2f} with activity={activity:.2f} and coverage={coverage:.2f}',
        ]

        return NodeAnalysisResult(
            started_at=started_at,
            ended_at=ended_at,
            frames_analyzed=len(samples),
            waterline_ratio=float(median_ratio),
            rise_velocity=rise_velocity,
            crossed_critical_line=crossed_critical_line,
            confidence=confidence,
            severity_score=severity_score,
            evidence_frame_path=evidence_frame_path,
            decision_trace=decision_trace,
        )
