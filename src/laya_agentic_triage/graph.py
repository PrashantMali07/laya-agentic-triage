from __future__ import annotations

import json
from typing import Literal

from langgraph.graph import END, START, StateGraph

from .config import get_settings
from .laya_engine import classify_incident
from .llm import get_llm
from .prompts import INCIDENT_REASONING_PROMPT
from .state import TriageState


settings = get_settings()


# Node 1

def normalize_input(
    state: TriageState,
) -> dict:

    request = state["request"]

    normalized = {
        "ticket_id": request.ticket_id,
        "subject": request.subject.strip(),
        "message": " ".join(
            request.message.split()
        ),
        "customer_id": request.customer_id,
        "customer_tier": request.customer_tier,
        "metadata": request.metadata,
    }

    return {
        "normalized_input": normalized
    }


# Node 2 : System-1

def laya_classification(
    state: TriageState,
) -> dict:

    classification = classify_incident(
        state["normalized_input"]
    )

    return {
        "classification": classification
    }

# Router
def route_after_laya(
    state: TriageState,
) -> Literal[
    "deterministic",
    "llm_reasoning",
    "human_review",
]:
    result = state["classification"]

    # Safety-critical cases

    if result.severity == "critical":
        return "human_review"

    if (
        result.human_escalation_probability
        >= settings.laya_human_threshold
    ):
        return "human_review"

    if (
        result.sensitive_data_probability
        >= settings.laya_human_threshold
    ):
        return "human_review"

    # Confident System-1 answer

    if (
        result.overall_confidence
        >= settings.laya_confidence_threshold
    ):
        return "deterministic"

    # Ambiguous → invoke System-2

    return "llm_reasoning"



# Node 3A : deterministic path

QUEUE_MAP = {
    "security_incident": "Security Operations",
    "account_access": "Identity & Access",
    "billing": "Billing Operations",
    "technical_support": "Technical Support",
    "service_request": "Customer Success",
    "other": "General Support",
}


def deterministic_action(
    state: TriageState,
) -> dict:

    classification = state["classification"]

    team = QUEUE_MAP.get(
        classification.incident_type,
        "General Support",
    )

    response = (
        f"Automatically routed to {team}. "
        f"Category={classification.incident_type}, "
        f"severity={classification.severity}, "
        f"confidence="
        f"{classification.overall_confidence:.3f}."
    )

    return {
        "route": "deterministic",
        "final_response": response,
    }


# Node 3B : System-2

def llm_reasoning(
    state: TriageState,
) -> dict:

    llm = get_llm()

    request = state["normalized_input"]
    classification = state["classification"]

    chain = (
        INCIDENT_REASONING_PROMPT
        | llm
    )

    response = chain.invoke(
        {
            "incident": json.dumps(
                request,
                indent=2,
                default=str,
            ),
            "classification": (
                classification.model_dump_json(
                    indent=2,
                    exclude={"raw"},
                )
            ),
        }
    )

    return {
        "route": "llm_reasoning",
        "llm_analysis": response.content,
        "final_response": response.content,
    }

# Node 3C : Human review

def human_review(
    state: TriageState,
) -> dict:

    classification = state["classification"]

    reasons: list[str] = []

    if classification.severity == "critical":
        reasons.append(
            "critical severity"
        )

    if (
        classification.human_escalation_probability
        >= settings.laya_human_threshold
    ):
        reasons.append(
            "human escalation requested"
        )

    if (
        classification.sensitive_data_probability
        >= settings.laya_human_threshold
    ):
        reasons.append(
            "possible sensitive information"
        )

    if not reasons:
        reasons.append(
            "policy-based manual review"
        )

    response = (
        "Human review required: "
        + ", ".join(reasons)
        + "."
    )

    return {
        "route": "human_review",
        "final_response": response,
    }



# Graph

def build_graph():
    graph = StateGraph(TriageState)

    graph.add_node(
        "normalize_input",
        normalize_input,
    )

    graph.add_node(
        "laya_classification",
        laya_classification,
    )

    graph.add_node(
        "deterministic_action",
        deterministic_action,
    )

    graph.add_node(
        "llm_reasoning",
        llm_reasoning,
    )

    graph.add_node(
        "human_review",
        human_review,
    )

    graph.add_edge(
        START,
        "normalize_input",
    )

    graph.add_edge(
        "normalize_input",
        "laya_classification",
    )

    graph.add_conditional_edges(
        "laya_classification",
        route_after_laya,
        {
            "deterministic":
                "deterministic_action",

            "llm_reasoning":
                "llm_reasoning",

            "human_review":
                "human_review",
        },
    )

    graph.add_edge(
        "deterministic_action",
        END,
    )

    graph.add_edge(
        "llm_reasoning",
        END,
    )

    graph.add_edge(
        "human_review",
        END,
    )

    return graph.compile()


triage_graph = build_graph()