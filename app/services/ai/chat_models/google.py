from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_google_model(model_name: str = "gemini-1.5-flash", temperature: float = 0.5):
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.ai.gemini_key,
        temperature=temperature
    )
