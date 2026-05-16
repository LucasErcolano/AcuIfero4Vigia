from __future__ import annotations

import importlib.util
import logging
from datetime import datetime
from pathlib import Path

import anyio
import httpx
import pytest

from acuifero_vigia.adapters.image_assessment import GemmaImageAssessmentAdapter
from acuifero_vigia.adapters.litert_node import LiteRTNodeHealth, LiteRTNodeRuntime
from acuifero_vigia.adapters.llm import LLMHealth
from acuifero_vigia.adapters.video_assessment import LiteRTGemmaRunner, OllamaGemmaRunner
from acuifero_vigia.api import deps as deps_module
from acuifero_vigia.api.routers.runtime import get_runtime_status
from acuifero_vigia.core import settings as settings_module
from acuifero_vigia.services.acuifero_assessment import AssessmentArtifactPack, EvidenceFrame, TemporalEvidencePack


@pytest.fixture(autouse=True)
def clear_settings_cache():
    settings_module.get_settings.cache_clear()
    yield
    settings_module.get_settings.cache_clear()


def _pack(image_path: Path) -> TemporalEvidencePack:
    return TemporalEvidencePack(
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
                brightness=-1.0,
                contrast=-1.0,
                motion_score=-1.0,
                edge_strength=-1.0,
                waterline_ratio_hint=-1.0,
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


def test_deps_select_litert_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "litert")
    monkeypatch.setenv("ACUIFERO_NODE_MODEL_PATH", str(tmp_path / "gemma-4-E2B-it.litertlm"))

    runner, assessor = deps_module._build_acuifero_runtime_components()

    assert isinstance(runner, LiteRTGemmaRunner)
    assert isinstance(assessor, GemmaImageAssessmentAdapter)
    assert assessor.runtime is deps_module.acuifero_node_runtime
    assert assessor.force_embedded is True


def test_deps_select_ollama_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "ollama")

    runner, assessor = deps_module._build_acuifero_runtime_components()

    assert isinstance(runner, OllamaGemmaRunner)
    assert isinstance(assessor, GemmaImageAssessmentAdapter)
    assert assessor.runtime is None
    assert assessor.force_embedded is False


def test_invalid_acuifero_provider_fails_startup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "bad-provider")
    settings_module.get_settings.cache_clear()
    spec = importlib.util.spec_from_file_location(
        "acuifero_vigia.api._deps_invalid_test",
        Path(deps_module.__file__),
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    with pytest.raises(ValueError, match="Unsupported ACUIFERO_NODE_PROVIDER"):
        spec.loader.exec_module(module)


def test_ollama_provider_runner_returns_verdict(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    image_path = tmp_path / "synthetic.jpg"
    image_path.write_bytes(b"fake-image")
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "ollama")
    monkeypatch.setenv("ACUIFERO_LLM_ENABLED", "true")
    monkeypatch.setenv("ACUIFERO_MULTIMODAL_ENABLED", "true")
    monkeypatch.setenv("ACUIFERO_MULTIMODAL_MODEL", "gemma4:e2b")
    monkeypatch.setenv("ACUIFERO_MULTIMODAL_BASE_URL", "http://127.0.0.1:11434/v1")

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

    def fake_post(self, *_args, **_kwargs):
        return FakeResponse()

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    monkeypatch.setattr(
        "acuifero_vigia.adapters.video_assessment._encode_image",
        lambda *_args, **_kwargs: "encoded",
    )

    runner, _assessor = deps_module._build_acuifero_runtime_components()
    assert isinstance(runner, OllamaGemmaRunner)
    verdict = runner.assess(_pack(image_path))

    assert verdict is not None
    assert verdict.runner_mode == "ollama-multimodal-temporal"
    assert verdict.fallback_used is False


def test_runtime_status_uses_ollama_health_for_dev_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "ollama")
    monkeypatch.setattr(
        deps_module.llm_client,
        "health",
        lambda: LLMHealth(True, True, "http://127.0.0.1:11434/v1", "gemma4:e2b", "ok"),
    )
    monkeypatch.setattr(
        deps_module.acuifero_node_runtime,
        "health",
        lambda: LiteRTNodeHealth(
            enabled=False,
            reachable=False,
            provider="ollama",
            backend="cpu",
            model="gemma4:e2b",
            model_path="embedded://ollama-dev",
            detail="Acuifero node provider is not litert",
        ),
    )

    status = anyio.run(get_runtime_status)

    assert status.acuifero["provider"] == "ollama"
    assert status.acuifero["engine_ready"] is True
    assert "Ollama development runtime" in status.acuifero["engine_detail"]


def test_litert_runtime_logs_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture):
    monkeypatch.setenv("ACUIFERO_NODE_PROVIDER", "litert")
    monkeypatch.setenv("ACUIFERO_NODE_MODEL_PATH", str(tmp_path / "gemma-4-E2B-it.litertlm"))
    runtime = LiteRTNodeRuntime()
    monkeypatch.setattr(runtime, "_ensure_engine", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    with caplog.at_level(logging.WARNING):
        response = runtime.generate_text("sys", "user", max_tokens=32)

    assert response is None
    assert "LiteRT node message failed" in caplog.text
