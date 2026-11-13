"""Clean generated local data folders."""

from __future__ import annotations

import shutil
from pathlib import Path

from lakehouse.config import load_config


def clean_local() -> None:
    config = load_config()
    project_root = Path(__file__).resolve().parents[1]
    for target in (config.landing_path, config.control_path, config.pipeline_log_path.parent, config.lakehouse_path):
        resolved = target.resolve()
        if not resolved.is_relative_to(project_root):
            raise RuntimeError(f"Refusing to remove path outside project root: {resolved}")
        if resolved.exists():
            shutil.rmtree(resolved)
            print(f"removed {resolved}")


if __name__ == "__main__":
    clean_local()

