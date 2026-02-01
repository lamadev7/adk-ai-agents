import logging
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from app.routes.mental_health import router as mental_health_router

async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    logging.info("Server is starting up...")
    yield
    logging.info("Server is shutting down...")

app = FastAPI(
    title="AI Agent Service",
    description="A multi-agent AI service built with FastAPI and Google Gemini",
    version="0.1.0",
    lifespan=lifespan,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)

@app.get("/")
async def root():
    return {"message": "AI Agent Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# routers
app.include_router(mental_health_router, prefix="/api")