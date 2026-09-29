from __future__ import annotations

from functools import lru_cache
from threading import BoundedSemaphore
from typing import Any

import laya
import torch

from .config import get_settings
from .schemas import ClassificationResult

import warnings
warnings.filterwarnings("ignore", message=".*ships invalid temperatures.*")


settings = get_settings()

_laya_semaphore = BoundedSemaphore(
    value=settings.laya_max_concurrency
)


def resolve_device() -> str:
    if settings.laya_device != "auto":
        return settings.laya_device

    if torch.cuda.is_available():
        return "cuda"

    return "cpu"


@lru_cache(maxsize=1)
def get_laya_agent():
    """
    Singleton Laya model.

    The model is downloaded/loaded once and remains resident
    for the lifetime of this Python process.
    """

    device = resolve_device()

    print(
        f"[Laya] Loading {settings.laya_model} "
        f"on device={device}"
    )

    agent = laya.load(
        settings.laya_model,
        device=device,
    )

    print("[Laya] Model ready.")

    return agent


LAYA_QUESTIONS: dict[str, dict[str, Any]] = {
    "incident_type": {
        "type": "choice",
        "instructions": (
            "Which category best describes this customer "
            "support or operational incident?"
        ),
        "criteria": {
            "security_incident": (
                "security breach, malware, phishing, "
                "compromised credentials or suspicious activity"
            ),
            "account_access": (
                "login problems, authentication, password, "
                "locked accounts or access permissions"
            ),
            "billing": (
                "payments, invoices, refunds, duplicate charges "
                "or subscription billing"
            ),
            "technical_support": (
                "software error, outage, API problem, "
                "integration problem or product malfunction"
            ),
            "service_request": (
                "normal product assistance, configuration, "
                "information or standard request"
            ),
            "other": (
                "does not clearly match the other categories"
            ),
        },
    },

    "severity": {
        "type": "score",
        "instructions": (
            "Assess the operational severity of this incident."
        ),
        "criteria": [
            (
                "low: informational request or minor problem "
                "with no meaningful impact"
            ),
            (
                "medium: degraded experience affecting the "
                "customer but work can continue"
            ),
            (
                "high: significant service disruption, "
                "financial impact or important blocked workflow"
            ),
            (
                "critical: major outage, active security issue, "
                "large financial risk or urgent business impact"
            ),
        ],
    },

    "requires_human": {
        "type": "noul",
        "instructions": (
            "Does this request require escalation to a human "
            "operator because of risk, ambiguity, urgency, "
            "financial impact or security implications?"
        ),
        "criteria": {
            "false": (
                "The issue can safely follow an automated "
                "standard workflow."
            ),
            "true": (
                "A human operator should review or handle "
                "this issue."
            ),
        },
    },

    "sensitive_data": {
        "type": "noul",
        "instructions": (
            "Does the message contain or strongly indicate "
            "sensitive information such as passwords, "
            "credentials, financial data, identity documents, "
            "private keys or security secrets?"
        ),
        "criteria": {
            "false": "No sensitive information is apparent.",
            "true": (
                "Sensitive or security-critical information "
                "is present or likely present."
            ),
        },
    },
}


SEVERITY_LABELS = {
    0: "low",
    1: "medium",
    2: "high",
    3: "critical",
}


def _severity_label(score: float) -> str:
    index = round(score)
    index = max(0, min(index, 3))
    return SEVERITY_LABELS[index]


def classify_incident(
    state: dict[str, Any],
) -> ClassificationResult:
    """
    Run all decisions in Laya's single System-1 inference call.
    """

    agent = get_laya_agent()

    # Conservative concurrency control for initial local testing.
    with _laya_semaphore:
        result = agent.predict(
            state,
            LAYA_QUESTIONS,
        )

    answers = result["answers"]
    incident = answers["incident_type"]
    severity = answers["severity"]
    human = answers["requires_human"]
    sensitive = answers["sensitive_data"]

    category_confidence = float(
        incident["answer_confidence"]
    )

    severity_confidence = float(
        severity["answer_confidence"]
    )

    # Conservative classification confidence.
    overall_confidence = min(
        category_confidence,
        severity_confidence,
    )

    severity_score = float(severity["score"])

    return ClassificationResult(
        incident_type=str(
            incident["choice"]
        ),
        severity_score=severity_score,
        severity=_severity_label(severity_score),
        human_escalation_probability=float(
            human["noul"]
        ),
        sensitive_data_probability=float(
            sensitive["noul"]
        ),
        category_confidence=category_confidence,
        severity_confidence=severity_confidence,
        overall_confidence=overall_confidence,
        raw=result,
    )