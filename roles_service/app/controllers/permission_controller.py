from fastapi import HTTPException
from sqlmodel import Session, select
from models.permission import Permission
from schemas.permission_schema import PermissionCreate
import uuid

def create_permission(data: PermissionCreate, session: Session):
    exists = session.exec(select(Permission).where(Permission.name == data.name)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Permiso ya existe")

    permission = Permission(**data.dict())
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission

def get_all_permissions(session: Session):
    return session.exec(select(Permission)).all()

def update_permission(permission_id: str, data: PermissionCreate, session: Session):
    try:
        # Convertir string a UUID
        permission_uid = uuid.UUID(permission_id)
        
        permission = session.exec(select(Permission).where(Permission.uid == permission_uid)).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permiso no encontrado")
        
        # Verificar que no exista otro permiso con el mismo nombre
        existing = session.exec(select(Permission).where(Permission.name == data.name, Permission.uid != permission_uid)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un permiso con ese nombre")
        
        permission.name = data.name
        permission.description = data.description
        session.add(permission)
        session.commit()
        session.refresh(permission)
        return permission
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"UUID inválido: {permission_id}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando permiso: {str(e)}")

def delete_permission(permission_id: str, session: Session):
    try:
        # Convertir string a UUID
        permission_uid = uuid.UUID(permission_id)
        
        permission = session.exec(select(Permission).where(Permission.uid == permission_uid)).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permiso no encontrado")
        
        session.delete(permission)
        session.commit()
        return {"message": "Permiso eliminado correctamente"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"UUID inválido: {permission_id}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando permiso: {str(e)}")
