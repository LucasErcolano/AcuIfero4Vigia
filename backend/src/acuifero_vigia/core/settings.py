from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path



def _as_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    acuifero_node_profile: str
    project_root: Path
    backend_root: Path
    data_dir: Path
    upload_dir: Path
    edge_db_path: Path
    central_db_path: Path
    llm_enabled: bool
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_timeout_seconds: float
    acuifero_multimodal_enabled: bool
    hydromet_enabled: bool
    hydromet_timeout_seconds: float
    acuifero_max_curated_frames: int
    acuifero_artifact_retention_days: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[3]
    project_root = backend_root.parent
    data_dir = Path(os.environ.get("ACUIFERO_DATA_DIR", str(backend_root / "data")))
    acuifero_node_profile = os.environ.get("ACUIFERO_NODE_PROFILE", "raspberry-pi-8gb")
    is_raspberry_profile = acuifero_node_profile.strip().lower() in {
        "raspberry-pi-8gb",
        "raspberry-pi",
        "rpi8gb",
        "rpi",
    }
    upload_dir = Path(os.environ.get("ACUIFERO_UPLOAD_DIR", str(data_dir / "uploads")))

    edge_db_path = Path(os.environ.get("ACUIFERO_EDGE_DB_PATH", str(data_dir / "edge.db")))
    central_db_path = Path(os.environ.get("ACUIFERO_CENTRAL_DB_PATH", str(data_dir / "central.db")))

    return Settings(
        acuifero_node_profile=acuifero_node_profile,
        project_root=project_root,
        backend_root=backend_root,
        data_dir=data_dir,
        upload_dir=upload_dir,
        edge_db_path=edge_db_path,
        central_db_path=central_db_path,
        llm_enabled=_as_bool("ACUIFERO_LLM_ENABLED", True),
        llm_base_url=os.environ.get("ACUIFERO_LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
        llm_model=os.environ.get("ACUIFERO_LLM_MODEL", "gemma4:e2b"),
        llm_api_key=os.environ.get("ACUIFERO_LLM_API_KEY", "ollama"),
        llm_timeout_seconds=float(os.environ.get("ACUIFERO_LLM_TIMEOUT_SECONDS", "30")),
        acuifero_multimodal_enabled=_as_bool("ACUIFERO_MULTIMODAL_ENABLED", not is_raspberry_profile),
        hydromet_enabled=_as_bool("ACUIFERO_HYDROMET_ENABLED", True),
        hydromet_timeout_seconds=float(os.environ.get("ACUIFERO_HYDROMET_TIMEOUT_SECONDS", "12")),
        acuifero_max_curated_frames=int(
            os.environ.get("ACUIFERO_MAX_CURATED_FRAMES", "3" if is_raspberry_profile else "6")
        ),
        acuifero_artifact_retention_days=int(
            os.environ.get("ACUIFERO_ARTIFACT_RETENTION_DAYS", "7" if is_raspberry_profile else "14")
        ),
    )
