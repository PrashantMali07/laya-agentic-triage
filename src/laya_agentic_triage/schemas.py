from typing import Any, Literal

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    ticket_id: str
    subject: str
    message: str

    customer_id: str | None = None
    customer_tier: Literal[
        "free",
        "standard",
        "premium",
        "enterprise",
    ] = "standard"

    metadata: dict[str, Any] = Field(default_factory=dict)


class ClassificationResult(BaseModel):
    incident_type: str

    severity_score: float
    severity: str

    human_escalation_probability: float
    sensitive_data_probability: float

    category_confidence: float
    severity_confidence: float

    overall_confidence: float

    raw: dict[str, Any] = Field(default_factory=dict)


class IncidentResponse(BaseModel):
    ticket_id: str

    route: Literal[
        "deterministic",
        "llm_reasoning",
        "human_review",
    ]

    classification: ClassificationResult

    response: str