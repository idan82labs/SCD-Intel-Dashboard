"""
CI Research Platform - Main FastAPI Application

A universal competitive intelligence research platform that accepts any research query,
plans a comprehensive investigation, executes multi-source data collection,
and generates interactive visual reports.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.api.routes import research, chat, export
from app.agent.research_agent import ResearchAgent
from app.data_sources.registry import DataSourceRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize data sources
    app.state.data_sources = DataSourceRegistry()
    await app.state.data_sources.initialize()

    # Initialize research agent
    app.state.research_agent = ResearchAgent(app.state.data_sources)

    print("All services initialized successfully")

    yield

    # Shutdown
    print("Shutting down services...")
    await app.state.data_sources.close()
    print("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Universal Competitive Intelligence Research API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "api": "up",
            "data_sources": "up",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
