from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.users import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.response import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest, db: AsyncSession = Depends(get_db)
) -> ApiResponse[TokenResponse]:
    token = await auth_service.authenticate(db, body)
    return ApiResponse(
        status=status.HTTP_200_OK, message="Login successful", data=token
    )


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Current user",
        data=UserResponse.model_validate(current_user),
    )
