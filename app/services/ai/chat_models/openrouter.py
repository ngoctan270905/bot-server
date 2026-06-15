from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_openrouter_model(model_name: str = "google/gemma-4-31b-it:free", temperature: float = 0.5):
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=settings.ai.openrouter_key,
        openai_api_base="https://openrouter.ai/api/v1",
    )