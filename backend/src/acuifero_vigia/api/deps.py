from __future__ import annotations

import json
from datetime import datetime

from sqlmodel import SQLModel, Session, select

from acuifero_vigia.adapters.asr import FasterWhisperASRAdapter
from acuifero_vigia.adapters.image_assessment import GemmaImageAssessmentAdapter
from acuifero_vigia.adapters.litert_node import LiteRTNodeRuntime
from acuifero_vigia.adapters.llm import OpenAICompatibleLLM
from acuifero_vigia.adapters.text_structuring_gemma_fewshot import GemmaFewShotTextStructurer
from acuifero_vigia.adapters.video_assessment import LiteRTGemmaRunner, OllamaGemmaRunner
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.models.domain import SyncQueueItem
from acuifero_vigia.services.acuifero_assessment import AcuiferoAssessmentEngine, TemporalEvidenceBuilder
from acuifero_vigia.services.external_data import ExternalDataService


def _build_acuifero_runtime_components() -> tuple[object, GemmaImageAssessmentAdapter]:
    settings = get_settings()
    provider = settings.acuifero_node_provider
    if provider == "litert":
        return (
            LiteRTGemmaRunner(acuifero_node_runtime),
            GemmaImageAssessmentAdapter(runtime=acuifero_node_runtime, force_embedded=True),
        )
    if provider == "ollama":
        return (
            OllamaGemmaRunner(llm_client),
            GemmaImageAssessmentAdapter(),
        )
    raise ValueError(
        f"Unsupported ACUIFERO_NODE_PROVIDER={provider!r}. Expected 'litert' or 'ollama'."
    )


llm_client = OpenAICompatibleLLM()
text_structurer = GemmaFewShotTextStructurer(llm_client)
acuifero_node_runtime = LiteRTNodeRuntime()
acuifero_runner, acuifero_image_assessor = _build_acuifero_runtime_components()
image_assessor = GemmaImageAssessmentAdapter()
asr_client = FasterWhisperASRAdapter()
external_data_service = ExternalDataService()
acuifero_engine = AcuiferoAssessmentEngine(
    builder=TemporalEvidenceBuilder(),
    runner=acuifero_runner,
)

is_online = True


def enqueue_entity(session: Session, entity_type: str, entity: SQLModel) -> None:
    entity_id = getattr(entity, "id", None)
    if entity_id is None:
        return
    existing = session.exec(
        select(SyncQueueItem)
        .where(SyncQueueItem.entity_type == entity_type)
        .where(SyncQueueItem.entity_id == entity_id)
        .where(SyncQueueItem.status == "pending")
    ).first()
    if existing is not None:
        existing.payload = json.dumps(entity.model_dump(mode="json"), ensure_ascii=True)
        existing.updated_at = datetime.utcnow()
        existing.last_error = None
        session.add(existing)
        return
    queue_item = SyncQueueItem(
        entity_type=entity_type,
        entity_id=entity_id,
        payload=json.dumps(entity.model_dump(mode="json"), ensure_ascii=True),
    )
    session.add(queue_item)

