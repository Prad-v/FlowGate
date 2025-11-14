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
from app.routers import templates, deployments, gateways, validation, opamp, registration_tokens, opamp_protocol

app.include_router(templates.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(gateways.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(opamp.router, prefix="/api/v1")
app.include_router(registration_tokens.router, prefix="/api/v1")
app.include_router(opamp_protocol.router, prefix="/api/v1")

