"""API routers."""
from .templates import router as templates_router
from .deployments import router as deployments_router
from .gateways import router as gateways_router

__all__ = [
    "templates_router",
    "deployments_router",
    "gateways_router",
]
