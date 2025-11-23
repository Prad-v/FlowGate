"""FastAPI application entry point"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Configure logging with optimized levels
logging.basicConfig(
    level=logging.WARNING,  # Default to WARNING to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Set specific log levels for different components
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # App-level logs at INFO

# Enable INFO logging for OpAMP components to see detailed message flow
logging.getLogger('app.services.opamp_protocol_service').setLevel(logging.INFO)
logging.getLogger('app.routers.opamp_websocket').setLevel(logging.INFO)

# Reduce verbosity of third-party libraries
logging.getLogger('uvicorn.access').setLevel(logging.ERROR)  # HTTP access logs - only errors
logging.getLogger('uvicorn').setLevel(logging.WARNING)  # Uvicorn server logs - only warnings/errors
logging.getLogger('fastapi').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)  # WebSocket library
logging.getLogger('asyncio').setLevel(logging.WARNING)

# SQLAlchemy logging is already configured in database.py

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
    packages, connection_settings, system_template, otel_builder, mcp_server,
    log_transformation
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
app.include_router(otel_builder.router, prefix="/api/v1")
app.include_router(mcp_server.router, prefix="/api/v1")
app.include_router(log_transformation.router, prefix="/api/v1")

