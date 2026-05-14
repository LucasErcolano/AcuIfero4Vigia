from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from acuifero_vigia.adapters.video_assessment import OllamaGemmaRunner
from acuifero_vigia.core import settings as settings_module
from acuifero_vigia.models.domain import Site, SiteCalibration
from acuifero_vigia.services.acuifero_assessment import (
    AcuiferoAssessmentEngine,
    AssessmentArtifactPack,
    EvidenceFrame,
    TemporalEvidenceBuilder,
    TemporalEvidencePack,
)


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ACUIFERO_MULTIMODAL_MAX_FRAMES", "1")
    monkeypatch.setenv("ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE", "512")
    settings_module.get_settings.cache_clear()
    yield
    settings_module.get_settings.cache_clear()


def _build_test_image(path: Path) -> None:
    image = Image.new("RGB", (320, 240), (200, 210, 220))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 132, 319, 239), fill=(90, 70, 40))
    draw.line((0, 95, 319, 95), fill=(245, 245, 245), width=2)
    image.save(path, format="JPEG")


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


def test_multimodal_evidence_builder_curates_image(tmp_path: Path):
    image_path = tmp_path / "synthetic.jpg"
    _build_test_image(image_path)

    builder = TemporalEvidenceBuilder()
    pack, ratio_hint, rise_velocity_hint, crossed_hint, confidence, trace = builder.build(
        site=_site(),
        video_path=str(image_path),
        calibration=_calibration(),
        source_type="frame",
    )

    assert pack.frames_analyzed == 1
    assert len(pack.selected_frames) == 1
    assert Path(pack.selected_frames[0].frame_path).exists()
    assert Path(pack.evidence_frame_path).exists()
    assert ratio_hint == 0
    assert rise_velocity_hint == 0
    assert crossed_hint is False
    assert confidence == 0
    assert pack.summary_metrics["opencv_used"] is False
    assert trace


def test_assessment_engine_falls_back_when_runner_unavailable(tmp_path: Path):
    image_path = tmp_path / "synthetic.jpg"
    _build_test_image(image_path)

    class NullRunner:
        def assess(self, pack: TemporalEvidencePack):
            return None

    engine = AcuiferoAssessmentEngine(builder=TemporalEvidenceBuilder(), runner=NullRunner())
    result = engine.assess_video(_site(), str(image_path), _calibration(), source_type="frame")

    assert result.verdict.fallback_used is True
    assert result.verdict.runner_mode == "multimodal-unavailable-fallback"
    assert result.verdict.assessment_level == "yellow"
    assert Path(result.evidence_pack.artifact_pack.manifest_path).exists()


def test_ollama_runner_multimodal_mode_parses_json_payload(monkeypatch, tmp_path: Path):
    image_path = tmp_path / "synthetic.jpg"
    _build_test_image(image_path)

    class FakeSettings:
        llm_enabled = True
        llm_model = "gemma4:e2b"
        acuifero_multimodal_enabled = True
        acuifero_multimodal_model = "gemma4:e2b"
        acuifero_multimodal_base_url = "http://127.0.0.1:11434/v1"
        acuifero_multimodal_image_max_side = 512
        acuifero_multimodal_num_ctx = 1024
        acuifero_multimodal_num_predict = 192
        acuifero_multimodal_timeout_seconds = 30

    class FakeLLM:
        settings = FakeSettings()

        @staticmethod
        def _extract_json(content):
            import json

            return json.loads(content)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "content": (
                        '{"assessment_level":"orange","assessment_score":0.76,'
                        '"temporal_summary":"La imagen muestra agua alta junto al puente.",'
                        '"reasoning_summary":"Gemma detecta ocupacion del cauce y riesgo sobre infraestructura.",'
                        '"reasoning_steps":["mirar linea de agua","comparar con puente","escalar"],'
                        '"critical_evidence":{"waterline_ratio":0.76,"crossed_critical_line":false,'
                        '"rise_velocity":0.0,"confidence":0.82,"visual_cues":["agua alta"]}}'
                    )
                }
            }

    def fake_post(self, *_a, **_k):
        return FakeResponse()

    import httpx

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    runner = OllamaGemmaRunner(FakeLLM())
    pack = TemporalEvidencePack(
        site_id="test-site",
        site_name="Puente Test",
        site_region="Zona Demo",
        video_path=str(image_path),
        source_type="frame",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        frames_analyzed=1,
        selected_frames=[
            EvidenceFrame(
                frame_path=str(image_path),
                timestamp_s=0.0,
                brightness=-1,
                contrast=-1,
                motion_score=-1,
                edge_strength=-1,
                waterline_ratio_hint=-1,
                waterline_y=-1,
            )
        ],
        evidence_frame_path=str(image_path),
        reference_y=0,
        critical_y=0,
        summary_metrics={"mode": "gemma4-multimodal-only"},
        artifact_pack=AssessmentArtifactPack(
            manifest_path="manifest.json",
            selected_frame_paths=[str(image_path)],
            evidence_frame_path=str(image_path),
        ),
    )

    verdict = runner.assess(pack)

    assert verdict is not None
    assert verdict.assessment_level == "orange"
    assert 0.75 < verdict.assessment_score < 0.77
    assert verdict.runner_mode == "ollama-multimodal-temporal"
    assert verdict.fallback_used is False
