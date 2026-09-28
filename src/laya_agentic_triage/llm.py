from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from .config import get_settings


settings = get_settings()


@lru_cache(maxsize=4)
def get_llm(
    provider: str | None = None,
) -> BaseChatModel:

    provider = provider or settings.llm_provider

    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required when "
                "LLM_PROVIDER=groq"
            )

        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0,
            max_retries=2,
        )

    if provider == "ollama":
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )