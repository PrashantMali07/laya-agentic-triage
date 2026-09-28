from typing import Any, TypedDict

from .schemas import ClassificationResult, IncidentRequest


class TriageState(TypedDict, total=False):
    request: IncidentRequest

    normalized_input: dict[str, Any]

    classification: ClassificationResult

    route: str

    llm_analysis: str

    final_response: str