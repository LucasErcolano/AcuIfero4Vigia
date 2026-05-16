from __future__ import annotations

from fastapi import APIRouter

from acuifero_vigia.api import deps
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.schemas.api import ConnectivityStatus, RuntimeStatus


router = APIRouter(tags=["runtime"])


@router.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "acuifero_node_profile": settings.acuifero_node_profile,
        "llm_enabled": settings.llm_enabled,
        "hydromet_enabled": settings.hydromet_enabled,
    }


@router.get("/settings/runtime", response_model=RuntimeStatus)
async def get_runtime_status() -> RuntimeStatus:
    settings = get_settings()
    llm_status = deps.llm_client.health()
    acuifero_node_status = deps.acuifero_node_runtime.health()
    hydromet_status = deps.external_data_service.health()
    acuifero_engine_ready = acuifero_node_status.reachable
    acuifero_engine_detail = acuifero_node_status.detail
    if settings.acuifero_node_provider == "ollama":
        acuifero_engine_ready = llm_status.reachable
        acuifero_engine_detail = (
            f"Ollama development runtime for Acuifero. "
            f"LLM detail: {llm_status.detail}"
        )
    return RuntimeStatus(
        is_online=deps.is_online,
        llm={
            "enabled": llm_status.enabled,
            "reachable": llm_status.reachable,
            "base_url": llm_status.base_url,
            "model": llm_status.model,
            "detail": llm_status.detail,
        },
        acuifero={
            "node_profile": settings.acuifero_node_profile,
            "provider": acuifero_node_status.provider,
            "backend": acuifero_node_status.backend,
            "vision_backend": settings.acuifero_node_vision_backend,
            "engine_ready": acuifero_engine_ready,
            "engine_detail": acuifero_engine_detail,
            "model_path": acuifero_node_status.model_path,
            "cache_dir": str(settings.acuifero_node_cache_dir),
            "data_dir": str(settings.data_dir),
            "ffmpeg_bin": settings.ffmpeg_bin,
            "multimodal_enabled": settings.acuifero_multimodal_enabled,
            "multimodal_verifier_enabled": settings.acuifero_multimodal_verifier_enabled,
            "multimodal_base_url": settings.acuifero_multimodal_base_url,
            "multimodal_model": settings.acuifero_multimodal_model,
            "multimodal_min_interval_seconds": settings.acuifero_multimodal_min_interval_seconds,
            "multimodal_score_threshold": settings.acuifero_multimodal_score_threshold,
            "multimodal_confidence_threshold": settings.acuifero_multimodal_confidence_threshold,
            "multimodal_image_max_side": settings.acuifero_multimodal_image_max_side,
            "multimodal_max_frames": settings.acuifero_multimodal_max_frames,
            "multimodal_frame_sample_seconds": settings.acuifero_multimodal_frame_sample_seconds,
            "multimodal_num_ctx": settings.acuifero_multimodal_num_ctx,
            "multimodal_timeout_seconds": settings.acuifero_multimodal_timeout_seconds,
            "max_curated_frames": settings.acuifero_max_curated_frames,
            "artifact_retention_days": settings.acuifero_artifact_retention_days,
        },
        hydromet={
            "enabled": hydromet_status.enabled,
            "reachable": hydromet_status.reachable,
            "detail": hydromet_status.detail,
        },
    )


@router.get("/settings/connectivity")
async def get_connectivity() -> ConnectivityStatus:
    return ConnectivityStatus(is_online=deps.is_online)


@router.post("/settings/connectivity")
async def set_connectivity(payload: ConnectivityStatus) -> ConnectivityStatus:
    deps.is_online = payload.is_online
    return ConnectivityStatus(is_online=deps.is_online)
