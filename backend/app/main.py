import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.endpoints import items, resolution_plan
from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.repositories.user_repository import get_or_create_mock_user

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(resolution_plan.router, prefix=f"{settings.API_V1_STR}/resolution-plan", tags=["resolution-plan"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.upload_dir_path, exist_ok=True)
    os.makedirs(settings.generated_dir_path, exist_ok=True)
    async with AsyncSessionLocal() as db:
        await get_or_create_mock_user(db)
    print("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")

