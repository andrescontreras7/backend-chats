from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from schemas.user_schema import UserCreate, UserLogin, UserResponse
from controller.user_controller import register_user, login_user, get_user_by_id
from database import get_session

router = APIRouter()

@router.post("/register")
async def register(data: UserCreate, session: Session = Depends(get_session)):
    return await register_user(data, session)

@router.post("/login")
async def login(data: UserLogin, session: Session = Depends(get_session)):
    return await login_user(data, session)

@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, session: Session = Depends(get_session)):
    """Obtener información de un usuario por su ID"""
    user = get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user
