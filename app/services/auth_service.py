from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    def __init__(self):
        self.user_repository = UserRepository()

    def register(
        self,
        db: Session,
        email: str,
        password: str
    ):

        existing_user = (
            self.user_repository.get_by_email(
                db,
                email
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

        user = User(
            email=email,
            password_hash=hash_password(password)
        )

        return self.user_repository.create(
            db,
            user
        )

    def login(
        self,
        db: Session,
        email: str,
        password: str
    ):

        user = self.user_repository.get_by_email(
            db,
            email
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        if not verify_password(
            password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        token = create_access_token(
            str(user.id)
        )

        return token
