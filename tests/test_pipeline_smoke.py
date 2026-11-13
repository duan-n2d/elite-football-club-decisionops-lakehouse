from __future__ import annotations

from orchestration.run_pipeline import run_pipeline
from lakehouse.io import read_table


def test_local_pipeline_smoke(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("LANDING_PATH", str(tmp_path / "data" / "landing"))
    monkeypatch.setenv("LAKEHOUSE_PATH", str(tmp_path / "lakehouse"))
    monkeypatch.setenv("CONTROL_PATH", str(tmp_path / "data" / "control"))
    monkeypatch.setenv("PIPELINE_LOG_PATH", str(tmp_path / "data" / "monitoring" / "pipeline_runs.jsonl"))
    monkeypatch.setenv("QUARANTINE_PATH", str(tmp_path / "data" / "quarantine"))

    result = run_pipeline(days=14, fans=300, seed=13, force=True)

    assert result["quality_failed"] == 0
    readiness = read_table(tmp_path / "lakehouse", "gold", "fact_player_readiness_daily")
    matchday = read_table(tmp_path / "lakehouse", "gold", "fact_matchday_revenue")
    quarantine = read_table(tmp_path / "lakehouse", "silver", "quarantine_failed_records")
    quality = read_table(tmp_path / "lakehouse", "quality", "quality_results")
    assert readiness
    assert matchday
    assert quarantine
    assert all(row["status"] == "passed" for row in quality)

