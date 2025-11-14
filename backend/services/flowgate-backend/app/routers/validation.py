"""Validation API router"""

from fastapi import APIRouter, Depends
from app.services.validation_service import ValidationService
from app.schemas.validation import ValidationRequest, ValidationResponse

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("", response_model=ValidationResponse)
async def validate_config(
    validation_request: ValidationRequest,
):
    """Validate OTel collector configuration"""
    service = ValidationService()
    return service.validate_config(validation_request)

