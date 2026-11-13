"""FastAPI application exposing governed lakehouse data products."""

from __future__ import annotations

from fastapi import FastAPI, Query

from ai_assistant.copilot import answer_question
from api import repository
from api.schemas import CopilotRequest, CopilotResponse


app = FastAPI(
    title="Elite Football Club DecisionOps API",
    description="Forward-deployed data product API over trusted Silver/Gold club lakehouse data.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness/players")
def get_player_readiness(limit: int = Query(25, ge=1, le=100)) -> list[dict[str, object]]:
    return repository.player_readiness(limit=limit)


@app.get("/readiness/{player_id}")
def get_readiness_for_player(player_id: str) -> list[dict[str, object]]:
    return repository.readiness_for_player(player_id)


@app.get("/matchday/revenue")
def get_matchday_revenue() -> list[dict[str, object]]:
    return repository.matchday_revenue()


@app.get("/fans/segments")
def get_fan_segments() -> list[dict[str, object]]:
    return repository.fan_segments()


@app.get("/campaigns/performance")
def get_campaign_performance() -> list[dict[str, object]]:
    return repository.campaign_performance()


@app.get("/adoption/metrics")
def get_adoption_metrics() -> list[dict[str, object]]:
    return repository.adoption_metrics()


@app.get("/quality/status")
def get_quality_status() -> dict[str, object]:
    return repository.quality_status()


@app.post("/copilot/query", response_model=CopilotResponse)
def query_copilot(request: CopilotRequest) -> CopilotResponse:
    return CopilotResponse(**answer_question(request.question, request.user_persona, execute=request.execute))

