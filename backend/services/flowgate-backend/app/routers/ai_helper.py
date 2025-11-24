"""AI Helper Router

API endpoints for AI-powered user assistance.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from app.database import get_db
from app.services.ai_helper_service import AIHelperService
from app.utils.auth import get_current_user_org_id

router = APIRouter(prefix="/ai-helper", tags=["ai-helper"])


class HelpRequest(BaseModel):
    question: str
    context: Optional[str] = None
    page: Optional[str] = None


class HelpResponse(BaseModel):
    answer: str
    suggestions: list[str]
    page: Optional[str] = None
    error: Optional[str] = None


@router.post("/help", response_model=HelpResponse)
async def get_help(
    request: HelpRequest,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered help for user questions.
    
    Args:
        request: Help request with question, optional context and page
        org_id: Organization ID (automatically extracted from authenticated user)
        db: Database session
        
    Returns:
        Help response with answer and suggestions
    """
    service = AIHelperService(db)
    result = await service.get_help(
        org_id=org_id,
        question=request.question,
        context=request.context,
        page=request.page
    )
    return HelpResponse(**result)

