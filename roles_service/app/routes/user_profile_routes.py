"""
Rutas para obtener perfil del usuario autenticado y navegación
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from auth.auth_middleware import get_current_user_id
from controllers.role_controller import get_user_role_name
from controllers.user_permission_controller import get_user_permissions_complete
from database import get_session
from typing import Dict, List

router = APIRouter(prefix="/user", tags=["Perfil de Usuario"])

@router.get("/profile", response_model=Dict)
async def get_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Obtener perfil completo del usuario con rol, permisos y navegación
    """
    try:
        # Obtener rol del usuario
        user_role_name = get_user_role_name(current_user_id, session)
        
        if not user_role_name:
            raise HTTPException(status_code=404, detail="Usuario sin rol asignado")
        
        # Obtener todos los permisos del usuario (rol + individuales)
        permissions = get_user_permissions_complete(current_user_id, session)
        
        # Determinar rutas permitidas según el rol
        allowed_routes = get_allowed_routes_by_role(user_role_name)
        
        return {
            "user_id": current_user_id,
            "role": user_role_name,
            "permissions": permissions,
            "navigation": {
                "default_route": get_default_route_by_role(user_role_name),
                "allowed_routes": allowed_routes
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo perfil: {str(e)}")

def get_allowed_routes_by_role(role_name: str) -> List[str]:
    """Definir rutas permitidas según el rol"""
    routes_by_role = {
        "administrador": [
            "/admin/dashboard",
            "/admin/users",
            "/admin/roles", 
            "/admin/permissions",
            "/admin/courts",
            "/courts",
            "/bookings",
            "/profile"
        ],
        "usuario": [
            "/user/dashboard",
            "/courts",
            "/bookings",
            "/profile"
        ]
    }
    
    return routes_by_role.get(role_name, ["/user/dashboard"])

def get_default_route_by_role(role_name: str) -> str:
    """Ruta por defecto después del login según el rol"""
    default_routes = {
        "administrador": "/admin/dashboard",
        "usuario": "/user/dashboard"
    }
    
    return default_routes.get(role_name, "/user/dashboard")
