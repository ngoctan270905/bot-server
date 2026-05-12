from fastapi import APIRouter
from app.api.v1.endpoints import health, auth

api_router = APIRouter()

# Include các endpoint của v1
api_router.include_router(health.router, tags=["Health Check"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
