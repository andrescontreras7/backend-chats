from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from database import get_session
from auth.auth_middleware import require_admin, get_current_user_id
from controllers.user_permission_controller import (
    get_user_permissions_complete,
    get_user_individual_permissions,
    get_all_available_permissions,
    grant_multiple_permissions_to_user,
    revoke_multiple_permissions_from_user
)
from typing import List, Dict
from pydantic import BaseModel
import json

router = APIRouter(prefix="/user-permissions", tags=["Permisos de Usuario"])

class UserPermissionsRequest(BaseModel):
    user_id: str
    permission_names: List[str]  # Siempre array para consistencia

@router.post("/grant")
async def grant_permissions(
    request: Request,
    session: Session = Depends(get_session),
    admin_user_id: str = Depends(require_admin)
):
    """Otorgar múltiples permisos a un usuario. Solo administradores."""
    try:
        # Leer el body raw
        body = await request.body()
        print(f"🔍 DEBUG GRANT - Body raw: {body}")
        
        # Intentar parsear el JSON
        try:
            json_data = await request.json()
            print(f"🔍 DEBUG GRANT - JSON parseado: {json_data}")
        except Exception as json_error:
            print(f"❌ DEBUG GRANT - Error parsing JSON: {json_error}")
            raise HTTPException(status_code=400, detail=f"JSON inválido: {json_error}")
        
        # Validar con Pydantic
        try:
            data = UserPermissionsRequest(**json_data)
            print(f"🔍 DEBUG GRANT - Datos validados:")
            print(f"   user_id: {data.user_id}")
            print(f"   permission_names: {data.permission_names}")
            print(f"   admin_user_id: {admin_user_id}")
        except Exception as validation_error:
            print(f"❌ DEBUG GRANT - Error validación Pydantic: {validation_error}")
            raise HTTPException(status_code=422, detail=f"Error validación: {validation_error}")
        
        # Llamar al controlador
        result = grant_multiple_permissions_to_user(
            user_id=data.user_id,
            permission_names=data.permission_names,
            granted_by=admin_user_id,
            session=session
        )
        
        print(f"✅ DEBUG GRANT - Resultado: {result}")
        return result
        
    except HTTPException as he:
        print(f"❌ DEBUG GRANT - Error general: {he.status_code}: {he.detail}")
        print(f"❌ DEBUG GRANT - Tipo error: {type(he)}")
        raise he
    except Exception as e:
        print(f"❌ DEBUG GRANT - Error inesperado: {e}")
        print(f"❌ DEBUG GRANT - Tipo error: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.post("/revoke")
async def revoke_permissions(
    request: Request,
    session: Session = Depends(get_session),
    admin_user_id: str = Depends(require_admin)
):
    """Revocar múltiples permisos de un usuario. Solo administradores."""
    try:
        # Leer el body raw
        body = await request.body()
        print(f"🔍 DEBUG REVOKE - Body raw: {body}")
        
        # Intentar parsear el JSON
        try:
            json_data = await request.json()
            print(f"🔍 DEBUG REVOKE - JSON parseado: {json_data}")
        except Exception as json_error:
            print(f"❌ DEBUG REVOKE - Error parseando JSON: {json_error}")
            raise HTTPException(status_code=422, detail=f"Error parseando JSON: {str(json_error)}")
        
        # Validar con Pydantic
        try:
            data = UserPermissionsRequest(**json_data)
            print(f"🔍 DEBUG REVOKE - Datos validados:")
            print(f"   user_id: {data.user_id}")
            print(f"   permission_names: {data.permission_names}")
            print(f"   admin_user_id: {admin_user_id}")
        except Exception as validation_error:
            print(f"❌ DEBUG REVOKE - Error validación Pydantic: {validation_error}")
            raise HTTPException(status_code=422, detail=f"Error validación: {str(validation_error)}")
        
        result = revoke_multiple_permissions_from_user(
            user_id=data.user_id,
            permission_names=data.permission_names,
            session=session
        )
        print(f"✅ DEBUG REVOKE - Resultado: {result}")
        return result
    except Exception as e:
        print(f"❌ DEBUG REVOKE - Error general: {str(e)}")
        print(f"❌ DEBUG REVOKE - Tipo error: {type(e)}")
        raise e

@router.get("/user/{user_id}/all", response_model=List[str])
def get_all_user_permissions(
    user_id: str,
    session: Session = Depends(get_session),
    admin_user_id: str = Depends(require_admin)
):
    """Obtener TODOS los permisos de un usuario (rol + individuales). Solo administradores."""
    return get_user_permissions_complete(user_id, session)

@router.get("/user/{user_id}/individual", response_model=List[Dict])
def get_individual_permissions(
    user_id: str,
    session: Session = Depends(get_session),
    admin_user_id: str = Depends(require_admin)
):
    """Obtener solo los permisos individuales de un usuario. Solo administradores."""
    return get_user_individual_permissions(user_id, session)

@router.get("/available", response_model=List[str])
def get_available_permissions(
    session: Session = Depends(get_session),
    admin_user_id: str = Depends(require_admin)
):
    """Listar todos los permisos disponibles en el sistema desde la base de datos. Solo administradores."""
    return get_all_available_permissions(session)

@router.get("/my-permissions", response_model=List[str])
def get_my_complete_permissions(
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """Obtener TODOS mis permisos (rol + individuales)."""
    return get_user_permissions_complete(current_user_id, session)
