"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Create database tables (in production, use migrations)
# Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import routers
from app.routers import (
    templates, deployments, gateways, validation, opamp, 
    registration_tokens, opamp_protocol, opamp_websocket, opamp_http,
    opamp_config, agent_tags, supervisor, supervisor_ui, settings,
    packages, connection_settings, system_template
)

app.include_router(templates.router, prefix="/api/v1")
app.include_router(opamp_config.router, prefix="/api/v1")
app.include_router(agent_tags.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(gateways.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(opamp.router, prefix="/api/v1")
app.include_router(registration_tokens.router, prefix="/api/v1")
app.include_router(opamp_protocol.router, prefix="/api/v1")
app.include_router(opamp_websocket.router, prefix="/api/v1")
app.include_router(opamp_http.router, prefix="/api/v1")
app.include_router(supervisor.router, prefix="/api/v1")
app.include_router(supervisor_ui.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(packages.router, prefix="/api/v1")
app.include_router(connection_settings.router, prefix="/api/v1")
app.include_router(system_template.router, prefix="/api/v1")

