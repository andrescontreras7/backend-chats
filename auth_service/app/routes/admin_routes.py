from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models.user_model import User
from schemas.user_schema import UserUpdate, UserResponse
from typing import List, Dict, Any
import uuid

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
def get_all_users(session: Session = Depends(get_session)):
    """Obtener todos los usuarios. Endpoint interno para roles service."""
    users = session.exec(select(User)).all()
    # Convertir UUID a string para cada usuario
    return [
        UserResponse(
            uid=str(user.uid),
            username=user.username,
            email=user.email,
            last_name=user.last_name,
            is_active=user.is_active
        ) for user in users
    ]

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, session: Session = Depends(get_session)):
    """Obtener un usuario por ID. Endpoint interno para roles service."""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UserResponse(
            uid=str(user.uid),
            username=user.username,
            email=user.email,
            last_name=user.last_name,
            is_active=user.is_active
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str, 
    user_data: Dict[str, Any], 
    session: Session = Depends(get_session)
):
    """Actualizar información de un usuario. Endpoint interno para roles service."""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Actualizar solo los campos permitidos
        allowed_fields = ['username', 'email', 'last_name']
        for field in allowed_fields:
            if field in user_data:
                setattr(user, field, user_data[field])
        
        session.add(user)
        session.commit()
        session.refresh(user)
        return UserResponse(
            uid=str(user.uid),
            username=user.username,
            email=user.email,
            last_name=user.last_name,
            is_active=user.is_active
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

@router.put("/users/{user_id}/deactivate")
def deactivate_user(user_id: str, session: Session = Depends(get_session)):
    """Desactivar un usuario. Endpoint interno para roles service."""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.is_active = False
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {
            "message": f"Usuario {user.username} desactivado correctamente", 
            "user": {
                "uid": str(user.uid),
                "username": user.username,
                "email": user.email,
                "last_name": user.last_name,
                "is_active": user.is_active
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

@router.put("/users/{user_id}/activate")
def activate_user(user_id: str, session: Session = Depends(get_session)):
    """Reactivar un usuario. Endpoint interno para roles service."""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.is_active = True
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {
            "message": f"Usuario {user.username} reactivado correctamente", 
            "user": {
                "uid": str(user.uid),
                "username": user.username,
                "email": user.email,
                "last_name": user.last_name,
                "is_active": user.is_active
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")
