import asyncio

from fastapi import APIRouter, HTTPException

from .graph import triage_graph
from .schemas import (
    IncidentRequest,
    IncidentResponse,
)


router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
    }


@router.post(
    "/triage",
    response_model=IncidentResponse,
)
async def triage(
    request: IncidentRequest,
) -> IncidentResponse:

    try:
        # The graph currently contains synchronous
        # PyTorch + LangChain nodes.
        #
        # Keep FastAPI's event loop free.
        result = await asyncio.to_thread(
            triage_graph.invoke,
            {
                "request": request,
            },
        )

        return IncidentResponse(
            ticket_id=request.ticket_id,
            route=result["route"],
            classification=result[
                "classification"
            ],
            response=result[
                "final_response"
            ],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc