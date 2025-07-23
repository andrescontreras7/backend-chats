from fastapi import HTTPException
from sqlmodel import Session, select
from models.user_permission import UserPermission
from controllers.role_controller import get_user_role_name, get_role_permissions
from typing import List
import uuid
from datetime import datetime

def get_all_available_permissions(session: Session):
    """Lista todos los permisos disponibles desde la base de datos"""
    from models.permission import Permission
    
    permissions = session.exec(select(Permission)).all()
    return [permission.name for permission in permissions]

def list_available_permissions() -> List[str]:
    """Lista todos los permisos disponibles en el sistema (Función legacy - usar get_all_available_permissions)"""
    return [
        "create_user", "edit_user", "delete_user", "view_users",
        "create_role", "edit_role", "delete_role", "view_roles", "manage_permissions",
        "create_court", "edit_court", "delete_court", "view_courts",
        "view_all_bookings", "cancel_any_booking", "create_booking", 
        "view_own_bookings", "cancel_own_booking", "edit_profile"
    ]

def _validate_user_exists(user_id: str, session: Session):
    """Función helper para validar que el usuario existe"""
    user_role = get_user_role_name(user_id, session)
    if not user_role:
        raise HTTPException(status_code=404, detail=f"Usuario con ID '{user_id}' no encontrado")

def _validate_permissions(permission_names: List[str], session: Session):
    """Función helper para validar permisos usando la base de datos"""
    available = get_all_available_permissions(session)
    invalid = [p for p in permission_names if p not in available]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Permisos inválidos: {invalid}")

def manage_user_permissions(user_id: str, permission_names: List[str], granted_by: str, session: Session, grant: bool = True):
    """Función unificada para otorgar/revocar múltiples permisos"""
    try:
        _validate_user_exists(user_id, session)
        _validate_permissions(permission_names, session)
        
        processed = []
        updated = []
        not_found = []
        
        for permission_name in permission_names:
            existing = session.exec(
                select(UserPermission).where(
                    UserPermission.user_id == user_id,
                    UserPermission.permission_name == permission_name
                )
            ).first()
            
            if existing:
                existing.granted = grant
                if grant:
                    existing.granted_by = granted_by
                session.add(existing)
                updated.append(permission_name)
            elif grant:  # Solo crear si estamos otorgando
                user_permission = UserPermission(
                    user_id=user_id,
                    permission_name=permission_name,
                    granted=True,
                    granted_by=granted_by,
                    created_at=datetime.now().isoformat()
                )
                session.add(user_permission)
                processed.append(permission_name)
            else:  # Intentando revocar permiso que no existe
                not_found.append(permission_name)
        
        session.commit()
        
        action = "otorgados" if grant else "revocados"
        return {
            "message": f"Permisos {action} para usuario {user_id}",
            "processed" if grant else "revoked": processed if grant else updated,
            "updated" if grant else "not_found": updated if grant else not_found,
            "total": len(processed + updated)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando permisos: {str(e)}")

def grant_multiple_permissions_to_user(user_id: str, permission_names: List[str], granted_by: str, session: Session):
    """Otorgar múltiples permisos a un usuario"""
    return manage_user_permissions(user_id, permission_names, granted_by, session, grant=True)

def revoke_multiple_permissions_from_user(user_id: str, permission_names: List[str], session: Session):
    """Revocar múltiples permisos de un usuario"""
    return manage_user_permissions(user_id, permission_names, "", session, grant=False)

def get_user_permissions_complete(user_id: str, session: Session) -> List[str]:
    """Obtener TODOS los permisos de un usuario (rol + individuales)"""
    try:
        # Permisos del rol
        user_role_name = get_user_role_name(user_id, session)
        role_permissions = get_role_permissions(user_role_name, session) if user_role_name else []
        
        # Permisos individuales
        individual_permissions = session.exec(
            select(UserPermission).where(
                UserPermission.user_id == user_id,
                UserPermission.granted == True
            )
        ).all()
        
        individual_names = [p.permission_name for p in individual_permissions]
        
        # Combinar sin duplicados
        return list(set(role_permissions + individual_names))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo permisos: {str(e)}")

def get_user_individual_permissions(user_id: str, session: Session):
    """Obtener detalles de permisos individuales de un usuario"""
    try:
        permissions = session.exec(
            select(UserPermission).where(UserPermission.user_id == user_id)
        ).all()
        
        return [
            {
                "permission_name": p.permission_name,
                "granted": p.granted,
                "granted_by": p.granted_by,
                "created_at": p.created_at
            }
            for p in permissions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo permisos individuales: {str(e)}")
