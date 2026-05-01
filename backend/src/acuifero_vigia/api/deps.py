from __future__ import annotations

import json

from sqlmodel import SQLModel, Session

from acuifero_vigia.adapters.image_assessment import GemmaImageAssessmentAdapter
from acuifero_vigia.adapters.llm import OpenAICompatibleLLM
from acuifero_vigia.adapters.text_structuring_gemma_fewshot import GemmaFewShotTextStructurer
from acuifero_vigia.adapters.video_assessment import OllamaGemmaRunner
from acuifero_vigia.models.domain import SyncQueueItem
from acuifero_vigia.services.acuifero_assessment import AcuiferoAssessmentEngine, TemporalEvidenceBuilder
from acuifero_vigia.services.external_data import ExternalDataService


llm_client = OpenAICompatibleLLM()
text_structurer = GemmaFewShotTextStructurer(llm_client)
image_assessor = GemmaImageAssessmentAdapter()
external_data_service = ExternalDataService()
acuifero_engine = AcuiferoAssessmentEngine(
    builder=TemporalEvidenceBuilder(),
    runner=OllamaGemmaRunner(llm_client),
)

is_online = True


def enqueue_entity(session: Session, entity_type: str, entity: SQLModel) -> None:
    entity_id = getattr(entity, "id", None)
    if entity_id is None:
        return
    queue_item = SyncQueueItem(
        entity_type=entity_type,
        entity_id=entity_id,
        payload=json.dumps(entity.model_dump(mode="json"), ensure_ascii=True),
    )
    session.add(queue_item)

