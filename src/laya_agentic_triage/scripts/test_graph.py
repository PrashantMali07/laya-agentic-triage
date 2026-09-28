from pprint import pprint

from laya_agentic_triage.graph import triage_graph
from laya_agentic_triage.schemas import IncidentRequest


examples = [
    IncidentRequest(
        ticket_id="INC-001",
        subject="Duplicate payment",
        message=(
            "We have been charged twice for invoice "
            "INV-9081. Please refund the duplicate."
        ),
        customer_tier="enterprise",
    ),

    IncidentRequest(
        ticket_id="INC-002",
        subject="Possible account compromise",
        message=(
            "Multiple unknown login attempts appeared "
            "on our admin account and our API credential "
            "may have been exposed."
        ),
        customer_tier="enterprise",
    ),

    IncidentRequest(
        ticket_id="INC-003",
        subject="API occasionally returns 504",
        message=(
            "Our API integration intermittently returns "
            "504 responses. It happens several times per "
            "day but retries normally work."
        ),
        customer_tier="premium",
    ),

    IncidentRequest(
        ticket_id="INC-004",
        subject="How do I change timezone?",
        message=(
            "Can you tell me where I can change the "
            "timezone in my account settings?"
        ),
    ),
]


for example in examples:
    print()
    print("=" * 80)
    print(example.ticket_id)
    print("=" * 80)

    result = triage_graph.invoke(
        {
            "request": example,
        }
    )

    pprint(
        {
            "route": result["route"],
            "classification": (
                result[
                    "classification"
                ].model_dump(
                    exclude={"raw"},
                )
            ),
            "response": result[
                "final_response"
            ],
        }
    )