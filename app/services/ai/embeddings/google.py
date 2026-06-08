from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

def get_google_embeddings(model_name: str = "models/embedding-001"):
    return GoogleGenerativeAIEmbeddings(
        model=model_name if "models/" in model_name else "models/embedding-001",
        google_api_key=settings.ai.gemini_key
    )
