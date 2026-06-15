from typing import Optional
from app.core.config import settings
from app.services.ai.chat_models.openai import get_openai_model, get_local_model
from app.services.ai.chat_models.google import get_google_model
from app.services.ai.chat_models.openrouter import get_openrouter_model


def get_chat_model(model_name: Optional[str] = None, temperature: float = 0.5):
    target_model = model_name or settings.ai.llm_model
    
    # 1. Google Gemini Cloud
    if "gemini" in target_model.lower():
        return get_google_model(target_model, temperature)
    
    # 2. OpenAI GPT Cloud
    elif "gpt-" in target_model.lower():
        return get_openai_model(target_model, temperature)

    elif "/" in target_model:  # OpenRouter model IDs đều có dạng "provider/model"
        return get_openrouter_model(target_model, temperature)
        
    # 3. Local LLM
    else:
        return get_local_model(target_model, temperature)
