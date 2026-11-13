"""Optional Spark/Delta session factory for Databricks-compatible local runs."""

from __future__ import annotations

from typing import Any


def get_spark(app_name: str = "elite-football-club-decisionops") -> Any:
    """Return a Spark session configured for Delta when dependencies exist.

    The repository's local pipeline does not require Spark, which keeps CI and
    interviews lightweight. In Databricks this function naturally resolves to
    the managed Spark runtime; locally it works when `.[spark]` dependencies are
    installed.
    """

    try:
        from delta import configure_spark_with_delta_pip
        from pyspark.sql import SparkSession
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install the spark extra: pip install -e '.[spark]'") from exc

    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()

