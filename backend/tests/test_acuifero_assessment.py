from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytest

from acuifero_vigia.core import settings as settings_module
from acuifero_vigia.services.acuifero_assessment import (
    AcuiferoAssessmentEngine,
    AssessmentArtifactPack,
    TemporalEvidenceBuilder,
    TemporalEvidencePack,
)
from acuifero_vigia.adapters.video_assessment import OllamaGemmaRunner
from acuifero_vigia.models.domain import Site, SiteCalibration


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_UPLOAD_DIR", str(tmp_path / "uploads"))
    settings_module.get_settings.cache_clear()
    yield
    settings_module.get_settings.cache_clear()


def _build_test_video(path: Path) -> None:
    width, height = 320, 240
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 4.0, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Could not create synthetic test video")

    for index in range(16):
        frame = np.full((height, width, 3), (200, 210, 220), dtype=np.uint8)
        waterline_y = max(70, 210 - index * 9)
        cv2.rectangle(frame, (0, waterline_y), (width - 1, height - 1), (90, 70, 40), -1)
        cv2.line(frame, (0, 100), (width - 1, 100), (245, 245, 245), 2)
        writer.write(frame)

    writer.release()


def _site() -> Site:
    return Site(id="test-site", name="Puente Test", region="Zona Demo", lat=-32.95, lng=-60.64)


def _calibration() -> SiteCalibration:
    return SiteCalibration(
        site_id="test-site",
        roi_polygon="[[0, 40], [320, 40], [320, 220], [0, 220]]",
        critical_line="[[0, 95], [320, 95]]",
        reference_line="[[0, 155], [320, 155]]",
        notes="synthetic calibration",
    )


def test_temporal_evidence_builder_curates_frames(tmp_path: Path):
    video_path = tmp_path / "synthetic.avi"
    _build_test_video(video_path)

    builder = TemporalEvidenceBuilder()
    pack, ratio_hint, rise_velocity_hint, crossed_hint, confidence, trace = builder.build(
        site=_site(),
        video_path=str(video_path),
        calibration=_calibration(),
        source_type="video",
    )

    assert pack.frames_analyzed >= 3
    assert len(pack.selected_frames) >= 1
    assert all(Path(frame.frame_path).exists() for frame in pack.selected_frames)
    assert sorted(frame.timestamp_s for frame in pack.selected_frames) == [
        frame.timestamp_s for frame in pack.selected_frames
    ]
    assert Path(pack.evidence_frame_path).exists()
    assert ratio_hint > 0
    assert rise_velocity_hint != 0
    assert isinstance(crossed_hint, bool)
    assert confidence > 0
    assert trace


def test_assessment_engine_falls_back_when_runner_unavailable(tmp_path: Path):
    video_path = tmp_path / "synthetic.avi"
    _build_test_video(video_path)

    class NullRunner:
        def assess(self, pack: TemporalEvidencePack):
            return None

    engine = AcuiferoAssessmentEngine(builder=TemporalEvidenceBuilder(), runner=NullRunner())
    result = engine.assess_video(_site(), str(video_path), _calibration(), source_type="video")

    assert result.verdict.fallback_used is True
    assert result.verdict.runner_mode == "deterministic-fallback"
    assert result.verdict.assessment_level in {"yellow", "orange", "red"}
    assert Path(result.evidence_pack.artifact_pack.manifest_path).exists()


def test_ollama_runner_text_mode_parses_json_payload():
    class FakeSettings:
        llm_enabled = True
        llm_model = "gemma4:e2b"
        acuifero_multimodal_enabled = False

    class FakeLLM:
        settings = FakeSettings()

        def _looks_like_ollama(self) -> bool:
            return False

        def generate_text(self, *args, **kwargs):
            return (
                '{"assessment_level":"orange","assessment_score":0.76,'
                '"temporal_summary":"La secuencia muestra una subida sostenida del agua.",'
                '"reasoning_summary":"Gemma observa crecimiento temporal consistente y mayor ocupacion del cauce.",'
                '"reasoning_steps":["comparar frames","confirmar tendencia","escalar"],'
                '"critical_evidence":{"peak_ratio_hint":0.8}}'
            )

        @staticmethod
        def _extract_json(content):
            import json

            return json.loads(content)

    runner = OllamaGemmaRunner(FakeLLM())
    pack = TemporalEvidencePack(
        site_id="test-site",
        site_name="Puente Test",
        site_region="Zona Demo",
        video_path="synthetic.avi",
        source_type="video",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        frames_analyzed=8,
        selected_frames=[],
        evidence_frame_path="evidence.jpg",
        reference_y=155.0,
        critical_y=95.0,
        summary_metrics={"trend_hint": "rising", "peak_ratio_hint": 0.8},
        artifact_pack=AssessmentArtifactPack(
            manifest_path="manifest.json",
            selected_frame_paths=[],
            evidence_frame_path="evidence.jpg",
        ),
    )

    verdict = runner.assess(pack)

    assert verdict is not None
    assert verdict.assessment_level == "orange"
    assert 0.75 < verdict.assessment_score < 0.77
    assert verdict.runner_mode == "text-only-temporal"
    assert verdict.fallback_used is False
