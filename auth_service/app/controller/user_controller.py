from sqlmodel import Session, select
from fastapi import HTTPException, status
from models.user_model import User
from auth.auth_utils import hash_password, verify_password, create_access_token
from schemas.user_schema import UserCreate, UserLogin, UserUpdate, UserResponse
from typing import Dict, List
from events.publisher import publish_user_created
from clients.roles_client import roles_client
import asyncio
import uuid






async def register_user(data: UserCreate, session: Session) -> Dict[str, str]:
    # Verificar si el usuario ya existe
    existing_user = session.exec(select(User).where(User.email == data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )

    # Crear nuevo usuario
    new_user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        last_name=data.last_name,
        is_active=data.is_active
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    await publish_user_created({
        "event": "user_created",
        "user_id": str(new_user.uid),
        "email": new_user.email
    })

    return {
        "msg": "Usuario registrado correctamente", 
        "email": new_user.email,
        "id": str(new_user.uid),
        "username": new_user.username
    }


async def login_user(data: UserLogin, session: Session) -> Dict[str, str]:
    # Buscar al usuario por email
    user = session.exec(select(User).where(User.email == data.email)).first()

    # Validar credenciales
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Cambiar a 400 para login inválido
            detail="Credenciales inválidas"
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    # Obtener el rol del usuario desde el servicio de roles
    user_role = await roles_client.get_user_role(str(user.uid))
    
    # Generar token de acceso con el rol incluido
    token_payload = {
        "sub": str(user.uid),
        "username": user.username,
        "email": user.email,
        "role": user_role or "usuario"  # Rol por defecto si no se encuentra
    }

    access_token = create_access_token(token_payload)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.uid),
        "username": user.username,
        "email": user.email,
        "role": user_role or "usuario"
    }

def get_user_by_id(user_id: str, session: Session) -> UserResponse:
    """Obtener información de un usuario por su ID"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    user = session.exec(select(User).where(User.uid == user_uuid)).first()
    if not user:
        return None
    
    return UserResponse(
        uid=str(user.uid),
        username=user.username,
        email=user.email,
        last_name=user.last_name,
        is_active=user.is_active
    )

# === FUNCIONES DE GESTIÓN DE USUARIOS (Para administradores) ===

def get_all_users(session: Session) -> List[UserResponse]:
    """Obtener todos los usuarios (para administradores)"""
    users = session.exec(select(User)).all()
    return [
        UserResponse(
            uid=str(user.uid),
            username=user.username,
            email=user.email,
            last_name=user.last_name,
            is_active=user.is_active
        ) for user in users
    ]

def get_user_by_id(user_id: str, session: Session) -> UserResponse:
    """Obtener un usuario por ID"""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return UserResponse(
            uid=str(user.uid),
            username=user.username,
            email=user.email,
            last_name=user.last_name,
            is_active=user.is_active
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

def update_user(user_id: str, data: UserUpdate, session: Session) -> UserResponse:
    """Actualizar un usuario (solo administradores)"""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar email único si se está cambiando
        if data.email and data.email != user.email:
            existing_email = session.exec(select(User).where(User.email == data.email)).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo electrónico ya está en uso"
                )
        
        # Actualizar campos proporcionados
        if data.username is not None:
            user.username = data.username
        if data.email is not None:
            user.email = data.email
        if data.last_name is not None:
            user.last_name = data.last_name
        
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

def deactivate_user(user_id: str, session: Session) -> Dict[str, str]:
    """Desactivar usuario (en lugar de eliminar)"""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user.is_active = False
        session.add(user)
        session.commit()
        
        return {"message": f"Usuario {user.username} desactivado correctamente"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

def activate_user(user_id: str, session: Session) -> Dict[str, str]:
    """Reactivar usuario"""
    try:
        user_uuid = uuid.UUID(user_id)
        user = session.exec(select(User).where(User.uid == user_uuid)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user.is_active = True
        session.add(user)
        session.commit()
        
        return {"message": f"Usuario {user.username} activado correctamente"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

# ...
