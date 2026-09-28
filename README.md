## Proposed Architecture

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

## LangGraph Workflow

```text

START
  ↓
validate_input
  ↓
laya_classify
  ↓
confidence_router
  ├── high_confidence → deterministic_action
  ├── uncertain → reasoning_agent
  └── critical → human_review
                         ↓
                   response_agent
                         ↓
                       END
```

## LLM Provider 

```text
  SYSTEM-1: LAYA      |  SYSTEM-2: Reasoning Engine 
----------------------|--------------------------------
  - Groq LLM          |  - Groq LLM
  - Fast / Cheap      |  - Slower / Expensive
  - Decision-based    |  - Explanation-based
  - Typed Output      |  - Natural Language Output
  
```
