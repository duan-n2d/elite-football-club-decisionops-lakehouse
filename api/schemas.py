"""API request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):
    question: str = Field(..., min_length=3)
    user_persona: str = "Data Platform Lead"
    execute: bool = True


class CopilotResponse(BaseModel):
    answer: str
    generated_sql: str | None = None
    source_tables: list[str] = []
    refused: bool = False
    refusal_reason: str | None = None
    latency_ms: int
    estimated_cost_usd: float

