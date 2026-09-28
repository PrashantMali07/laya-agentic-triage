# Laya Agentic Incident Triage

Laya Agentic Triage is an AI-powered system designed to automatically classify, route, and resolve incoming customer support incidents and operational tickets. It implements a dual-system architecture (System-1 + System-2) using LangGraph to balance speed, cost, and reliability.

## System Architecture

```text
                    ┌───────────────────┐
Incoming Request -->│ FastAPI / Webhook │
                    └─────────┬─────────┘
                              ↓
                     LangGraph Workflow
                              ↓
                  ┌───────────────────────┐
                  │ Normalize / Validate  │
                  └───────────┬───────────┘
                              ↓
                    SYSTEM-1 : LAYA
                 Typed decision classifier
                  /        |        \
                 /         |         \
             category   severity   confidence
             choice      score       noul
                 \         |         /
                  └────────┬────────┘
                           ↓
                  Confidence Router
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         High confidence  Medium       Low
              ↓            ↓            ↓
        deterministic     LLM         human/
          workflow      reasoning     fallback
                           ↓
                    SYSTEM-2 LLM
                  Ollama / Groq API
                           ↓
                 Action / Explanation
                           ↓
                PostgreSQL + Langfuse
```

## Detailed Workflow

The core of the system is built on **LangGraph**, which orchestrates a state machine consisting of several nodes:

1. **`normalize_input`**: Cleans and validates incoming tickets.
2. **`laya_classify` (System-1)**: Fast, typed inference to categorize the issue and assign scores.
3. **`confidence_router`**: Makes a deterministic routing decision based on Laya's classification output.
4. **Action Nodes**:
   - `deterministic_action`: Automatically routes the ticket to the correct team.
   - `llm_reasoning`: Uses System-2 LLM to analyze ambiguous requests.
   - `human_review`: Escalates critical or sensitive issues to human operators.

## System-1 vs System-2: How Laya and LLM Participate

The architecture relies on two distinct AI systems working together:

| Feature | SYSTEM-1: Laya | SYSTEM-2: Reasoning Engine (LLM) |
|---|---|---|
| **Role** | Frontline classifier & router | Deep analysis & reasoning |
| **Provider** | Laya Typed-Decisions | Groq / Ollama |
| **Speed/Cost** | Fast & Cheap | Slower & Expensive |
| **Output Type** | Typed Decisions (Categories, Scores, Booleans) | Natural Language Output |
| **Tasks** | Identify category, assess severity, flag sensitive data, determine human escalation | Handle ambiguous cases, explain routing decisions |

### What Laya Does (System-1)
Laya operates as a fast, deterministic decision engine. In a **single inference call**, it answers four structured questions:
1. **Category**: Which queue does this belong to? (e.g., billing, technical support).
2. **Severity**: How severe is the issue? (Score 0-3).
3. **Requires Human**: Does it need human escalation? (Boolean probability).
4. **Sensitive Data**: Does the ticket contain PII/secrets? (Boolean probability).

### What the LLM Does (System-2)
The LLM (Groq/Ollama) is only invoked when Laya encounters an ambiguous ticket (medium/low confidence). The LLM reads the normalized request and Laya's uncertain classification, and uses complex reasoning to determine the best next step and provide a natural language explanation.

## Scoring & Graph Routing

The system routes tickets based on the exact scores and probabilities returned by Laya.

### 1. Scoring Mechanics
- **Severity Score**: Maps to labels `low` (0), `medium` (1), `high` (2), `critical` (3).
- **Confidence Scores**: Laya provides `answer_confidence` for its category and severity choices. The system uses the lowest of these as the `overall_confidence`.
- **Probabilities (Noul)**: Laya outputs `noul` (probability) values for boolean questions (e.g., `human_escalation_probability` and `sensitive_data_probability`).

### 2. Graph Routing Logic
The `confidence_router` applies the following rules in order:

1. **Safety-Critical Escalations (`human_review`)**:
   - If severity is `critical`.
   - If `human_escalation_probability` >= Threshold (default `0.65`).
   - If `sensitive_data_probability` >= Threshold (default `0.65`).
2. **Confident Auto-Routing (`deterministic_action`)**:
   - If `overall_confidence` >= Threshold (default `0.80`), the system automatically routes the ticket to the appropriate team (e.g., Billing Operations) without LLM intervention.
3. **Ambiguity Fallback (`llm_reasoning`)**:
   - If the ticket is not critical but Laya's confidence is below `0.80`, it is routed to System-2 for deep LLM reasoning.

## API Endpoints

The application is served via FastAPI with the following endpoints:

### `GET /health`
Returns the health status of the API.
```json
{
  "status": "ok"
}
```

### `POST /triage`
The main ingestion endpoint. It executes the LangGraph workflow asynchronously to prevent blocking the event loop.

**Request Body (`IncidentRequest`)**
```json
{
  "ticket_id": "INC-001",
  "subject": "Duplicate payment",
  "message": "We have been charged twice for invoice INV-9081. Please refund the duplicate.",
  "customer_tier": "enterprise"
}
```

**Response Body (`IncidentResponse`)**
Returns the final route taken, the detailed classification scores from Laya, and the final response/action string.
