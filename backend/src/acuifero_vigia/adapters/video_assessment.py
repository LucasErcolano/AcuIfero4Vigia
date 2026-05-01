from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx

from acuifero_vigia.adapters.llm import OpenAICompatibleLLM
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.services.acuifero_assessment import AssessmentVerdict, TemporalEvidencePack


SYSTEM_PROMPT = (
    "Sos Acuifero, un motor de evaluacion temporal de crecidas sobre camaras fijas. "
    "Recibis una secuencia ordenada de frames con metadatos de tiempo y pistas numericas no semanticas. "
    "Tu tarea es decidir el riesgo principal del nodo fijo de forma auditable, priorizando lo que se ve en la secuencia. "
    "Responde SOLO un JSON con estas claves exactas: assessment_level (green|yellow|orange|red), "
    "assessment_score (0.0 a 1.0), temporal_summary (1 o 2 oraciones), reasoning_summary (2 o 3 oraciones), "
    "reasoning_steps (lista corta), critical_evidence (objeto JSON). No markdown, no texto extra."
)


def _level_from_score(score: float) -> str:
    if score >= 0.82:
        return "red"
    if score >= 0.62:
        return "orange"
    if score >= 0.4:
        return "yellow"
    return "green"


def _parse_steps(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()][:5]
    text = str(raw or "").strip()
    if not text:
        return []
    if "->" in text:
        return [piece.strip() for piece in text.split("->") if piece.strip()][:5]
    return [piece.strip() for piece in text.replace("\n", ". ").split(".") if piece.strip()][:5]


def _normalize_verdict_payload(
    payload: dict[str, Any],
    *,
    runner_name: str,
    runner_mode: str,
) -> AssessmentVerdict | None:
    try:
        score = float(payload.get("assessment_score"))
    except (TypeError, ValueError):
        return None

    score = max(0.0, min(1.0, score))
    level = str(payload.get("assessment_level", "")).strip().lower()
    if level not in {"green", "yellow", "orange", "red"}:
        level = _level_from_score(score)

    temporal_summary = str(payload.get("temporal_summary", "")).strip()
    reasoning_summary = str(payload.get("reasoning_summary", "")).strip()
    if not temporal_summary or not reasoning_summary:
        return None

    reasoning_steps = _parse_steps(payload.get("reasoning_steps"))
    if not reasoning_steps:
        reasoning_steps = [f"score={score:.2f}", f"level={level}"]

    critical_evidence = payload.get("critical_evidence")
    if not isinstance(critical_evidence, dict):
        critical_evidence = {"raw": critical_evidence}

    return AssessmentVerdict(
        assessment_level=level,
        assessment_score=round(score, 4),
        temporal_summary=temporal_summary,
        reasoning_summary=reasoning_summary,
        reasoning_steps=reasoning_steps,
        critical_evidence=critical_evidence,
        runner_name=runner_name,
        runner_mode=runner_mode,
        fallback_used=False,
    )


class OllamaGemmaRunner:
    def __init__(self, llm: OpenAICompatibleLLM) -> None:
        self.llm = llm
        self.settings = get_settings()

    def assess(self, pack: TemporalEvidencePack) -> AssessmentVerdict | None:
        if not self.settings.llm_enabled:
            return None

        if self.settings.acuifero_multimodal_enabled:
            verdict = self._assess_multimodal(pack)
            if verdict is not None:
                return verdict
        return self._assess_text(pack)

    def _assess_multimodal(self, pack: TemporalEvidencePack) -> AssessmentVerdict | None:
        if not self.llm._looks_like_ollama():
            return None

        encoded_images = []
        for frame in pack.selected_frames:
            path = Path(frame.frame_path)
            if not path.exists():
                continue
            with path.open("rb") as handle:
                encoded_images.append(base64.b64encode(handle.read()).decode("ascii"))

        if not encoded_images:
            return None

        payload = {
            "model": self.settings.llm_model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(pack),
                    "images": encoded_images,
                },
            ],
            "options": {"temperature": 0.1, "num_predict": 512},
        }
        try:
            with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
                response = client.post(self.llm._ollama_chat_url(), json=payload)
                response.raise_for_status()
            body = response.json()
            content = body.get("message", {}).get("content", "")
        except Exception:
            return None

        parsed = self.llm._extract_json(content)
        if not isinstance(parsed, dict):
            return None
        return _normalize_verdict_payload(
            parsed,
            runner_name=self.settings.llm_model,
            runner_mode="ollama-multimodal-temporal",
        )

    def _assess_text(self, pack: TemporalEvidencePack) -> AssessmentVerdict | None:
        raw = self.llm.generate_text(SYSTEM_PROMPT, self._build_user_prompt(pack), max_tokens=420)
        if not raw:
            return None
        parsed = self.llm._extract_json(raw)
        if not isinstance(parsed, dict):
            return None
        return _normalize_verdict_payload(
            parsed,
            runner_name=self.settings.llm_model,
            runner_mode="text-only-temporal",
        )

    @staticmethod
    def _build_user_prompt(pack: TemporalEvidencePack) -> str:
        frame_lines = []
        for index, frame in enumerate(pack.selected_frames, start=1):
            frame_lines.append(
                " | ".join(
                    [
                        f"frame_{index}",
                        f"t={frame.timestamp_s:.1f}s",
                        f"ratio_hint={frame.waterline_ratio_hint:.2f}",
                        f"motion={frame.motion_score:.3f}",
                        f"edge={frame.edge_strength:.3f}",
                        f"brightness={frame.brightness:.1f}",
                        f"contrast={frame.contrast:.1f}",
                    ]
                )
            )
        return "\n".join(
            [
                f"Sitio: {pack.site_name} ({pack.site_region})",
                f"Fuente: {pack.source_type}",
                f"Frames analizados: {pack.frames_analyzed}",
                f"Resumen metrico: {json.dumps(pack.summary_metrics, ensure_ascii=True)}",
                "Frames curados en orden temporal:",
                *frame_lines,
                (
                    "Decidi el riesgo principal observando la progresion temporal del agua. "
                    "Distingui subida real de ruido visual y explicalo de forma auditable."
                ),
            ]
        )


class LiteRTGemmaRunner:
    def assess(self, pack: TemporalEvidencePack) -> AssessmentVerdict | None:
        return None
