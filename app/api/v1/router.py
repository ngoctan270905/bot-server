from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, profiles, projects, bots
from app.ws import router as ws_router

api_router = APIRouter()

# Include các endpoint của v1
api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(bots.router, prefix="/bots", tags=["Bots"])
api_router.include_router(ws_router.router, tags=["WebSocket"])
