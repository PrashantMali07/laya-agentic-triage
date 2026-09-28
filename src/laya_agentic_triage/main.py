from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import router
from .config import get_settings
from .laya_engine import get_laya_agent


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Warm Laya once when the process starts.

    This avoids loading the model during the
    first user request.
    """

    get_laya_agent()

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "system_1": "Laya Typed-Decisions",
        "system_2": settings.llm_provider,
    }