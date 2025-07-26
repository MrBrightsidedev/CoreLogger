#!/usr/bin/env python3
"""
CoreLogger FastAPI Entry Point
Eidos OS Logging Module REST API Server
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api import router
from config import settings
from db import init_database
from web.routes import router as web_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CoreLogger API server...")
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down CoreLogger API server...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)  # API routes
    app.include_router(web_router)  # Web dashboard routes
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
    
    # Root endpoint - redirect to dashboard
    @app.get("/")
    async def root():
        """Root endpoint redirects to dashboard."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard")
    
    # API info endpoint for programmatic access
    @app.get("/api")
    async def api_info():
        """API information endpoint."""
        return {
            "name": settings.api_title,
            "description": settings.api_description,
            "version": settings.api_version,
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "health_check": "/api/v1/health",
        }
    
    return app


# Create the app instance
app = create_app()


def main():
    """Run the FastAPI server using uvicorn."""
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
