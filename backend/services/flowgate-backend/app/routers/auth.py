"""Authentication router for login, logout, and token management"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.session_service import get_session_service
from app.services.oidc_service import OIDCService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    UserResponse,
    OIDCProviderResponse,
    OIDCAuthorizeRequest,
    OIDCCallbackRequest,
    OIDCCallbackResponse,
)
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.oidc_provider import OIDCProvider
from app.config import settings
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Login with username/email and password
    
    Returns JWT tokens and optionally sets session cookie for web UI.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_local_user(
        login_data.username_or_email,
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Check if password change is required
    requires_password_change = auth_service.require_password_change(user)
    
    # Determine org_id for token
    org_id = login_data.org_id
    if not org_id:
        org_id = user.org_id
    
    # Create tokens
    access_token, refresh_token = auth_service.create_access_token(user, org_id)
    
    # Create session for web UI
    session_service = get_session_service()
    session_data = {
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }
    session_id = session_service.create_session(user.id, org_id, session_data)
    
    # Set session cookie
    response.set_cookie(
        key="flowgate_session",
        value=session_id,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
        requires_password_change=requires_password_change,
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    session_id: Optional[str] = None,  # From cookie
):
    """
    Logout user and invalidate session
    """
    session_service = get_session_service()
    
    if session_id:
        session_service.delete_session(session_id)
    
    # Clear session cookie
    response.delete_cookie(
        key="flowgate_session",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token
    """
    from app.core.security import verify_refresh_token, create_access_token
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get user
    auth_service = AuthService(db)
    user_id = UUID(payload.get("user_id") or payload.get("sub"))
    user = auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new access token
    org_id = UUID(payload.get("org_id")) if payload.get("org_id") else user.org_id
    claims = {
        "sub": str(user.id),
        "user_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }
    if org_id:
        claims["org_id"] = str(org_id)
    
    access_token = create_access_token(claims)
    
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change user password
    
    For first login (password_changed_at is NULL), old_password is not required.
    """
    auth_service = AuthService(db)
    
    # Check if this is first login
    is_first_login = current_user.password_changed_at is None
    
    if is_first_login:
        # First login - set password without old password
        auth_service.set_password(current_user, password_data.new_password)
    else:
        # Regular password change - require old password
        if not password_data.old_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is required",
            )
        
        success = auth_service.change_password(
            current_user,
            password_data.old_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid old password",
            )
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user information
    """
    return UserResponse.model_validate(current_user)


@router.get("/oidc/providers", response_model=list[OIDCProviderResponse])
async def list_oidc_providers(
    org_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """
    List available OIDC providers
    
    Returns system-wide providers and organization-specific providers.
    """
    query = db.query(OIDCProvider).filter(OIDCProvider.is_active == True)
    
    if org_id:
        # Include system-wide (org_id is NULL) and org-specific providers
        query = query.filter(
            (OIDCProvider.org_id == org_id) | (OIDCProvider.org_id.is_(None))
        )
    else:
        # Only system-wide providers
        query = query.filter(OIDCProvider.org_id.is_(None))
    
    providers = query.all()
    return [OIDCProviderResponse.model_validate(p) for p in providers]


@router.get("/oidc/{provider_id}/authorize")
async def oidc_authorize(
    provider_id: UUID,
    redirect_uri: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get OIDC authorization URL
    
    Returns the authorization URL to redirect the user to the OIDC provider.
    """
    oidc_service = OIDCService(db)
    
    auth_url = oidc_service.get_authorization_url(provider_id, redirect_uri, state)
    
    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OIDC provider or configuration",
        )
    
    return {"authorization_url": auth_url}


@router.get("/oidc/{provider_id}/callback")
@router.post("/oidc/{provider_id}/callback", response_model=OIDCCallbackResponse)
async def oidc_callback(
    provider_id: UUID,
    code: str = None,
    state: Optional[str] = None,
    redirect_uri: str = None,
    callback_data: Optional[OIDCCallbackRequest] = None,
    response: Response = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Handle OIDC callback and create/login user
    
    This endpoint processes the OAuth callback from the OIDC provider.
    Supports both GET (redirect) and POST (JSON) requests.
    """
    from fastapi.responses import RedirectResponse
    
    # Get parameters from query (GET) or body (POST)
    if request and request.method == "GET":
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        redirect_uri = request.query_params.get("redirect_uri")
    elif callback_data:
        code = callback_data.code
        state = callback_data.state
        redirect_uri = callback_data.redirect_uri
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameters"
        )
    
    oidc_service = OIDCService(db)
    auth_service = AuthService(db)
    
    # Handle OIDC callback
    user = await oidc_service.handle_oidc_callback(
        provider_id,
        code,
        redirect_uri,
        state
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC authentication failed",
        )
    
    # Create tokens
    access_token, refresh_token = auth_service.create_access_token(user, user.org_id)
    
    # Create session for web UI
    session_service = get_session_service()
    session_data = {
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
    }
    session_id = session_service.create_session(user.id, user.org_id, session_data)
    
    # Set session cookie
    if response:
        response.set_cookie(
            key="flowgate_session",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
        )
    
    # If GET request (redirect), redirect to frontend with token in URL fragment
    if request and request.method == "GET":
        frontend_redirect = redirect_uri or "/"
        # Store tokens in session, redirect to frontend
        redirect_url = f"{frontend_redirect}?auth_success=true"
        return RedirectResponse(url=redirect_url)
    
    # POST request returns JSON
    return OIDCCallbackResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
        requires_password_change=False,  # OIDC users don't need password
    )

