from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_openai_model(model_name: str = "gpt-3.5-turbo", temperature: float = 0.5):
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=settings.ai.openai_key
    )

def get_local_model(model_name: str, temperature: float = 0.5):
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=settings.ai.openai_key or "local-no-key",
        openai_api_base=settings.ai.llm_url.replace("/chat/completions", ""),
    )
