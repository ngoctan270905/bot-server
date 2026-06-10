from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, auth, profiles, projects, bots, 
    conversations, sources, resources, social, 
    telegram, subscriptions, webhooks
)
from app.ws import router as ws_router

api_router = APIRouter()

# Include các endpoint của v1
api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(bots.router, prefix="/bots", tags=["Bots"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
api_router.include_router(social.router, prefix="/social", tags=["Social"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["Telegram"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(ws_router.router, tags=["WebSocket"])
