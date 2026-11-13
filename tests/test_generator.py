from __future__ import annotations

from data_generator.generate import generate_all


def test_generator_writes_all_sources(tmp_path) -> None:
    generated = generate_all(output_dir=tmp_path / "landing", days=14, fans=250, seed=11)
    assert generated.batch_id == "20260101_11"
    assert generated.row_counts["players"] > 30
    assert generated.row_counts["gps_tracking_aggregates"] > 0
    assert (tmp_path / "landing" / "players").exists()

