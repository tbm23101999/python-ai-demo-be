from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
)

from app.services.auth_service import (
    AuthService
)

router = APIRouter()

auth_service = AuthService()


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    auth_service.register(
        db,
        request.email,
        request.password
    )

    return {
        "message": "registered"
    }


@router.post(
    "/login",
    response_model=AuthResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    token = auth_service.login(
        db,
        request.email,
        request.password
    )

    return AuthResponse(
        access_token=token
    )
