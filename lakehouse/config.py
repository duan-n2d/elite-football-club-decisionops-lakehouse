"""Runtime configuration for local and Azure-style deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    environment: str
    landing_path: Path
    lakehouse_path: Path
    control_path: Path
    pipeline_log_path: Path
    quarantine_path: Path
    copilot_max_rows: int


def load_config() -> ProjectConfig:
    data_root = Path(os.getenv("LOCAL_DATA_ROOT", "data"))
    return ProjectConfig(
        environment=os.getenv("ENVIRONMENT", "local"),
        landing_path=Path(os.getenv("LANDING_PATH", data_root / "landing")),
        lakehouse_path=Path(os.getenv("LAKEHOUSE_PATH", "lakehouse_local")),
        control_path=Path(os.getenv("CONTROL_PATH", data_root / "control")),
        pipeline_log_path=Path(os.getenv("PIPELINE_LOG_PATH", data_root / "monitoring" / "pipeline_runs.jsonl")),
        quarantine_path=Path(os.getenv("QUARANTINE_PATH", data_root / "quarantine")),
        copilot_max_rows=int(os.getenv("COPILOT_MAX_ROWS", "100")),
    )

