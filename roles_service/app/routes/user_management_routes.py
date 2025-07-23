"""
Rutas para gestión de usuarios por parte del admin
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from auth.auth_middleware import require_admin
from controllers.user_management_controller import UserManagementController

router = APIRouter(prefix="/admin/users", tags=["Gestión de Usuarios"])

@router.get("/", response_model=List[Dict])
async def get_all_users(admin_user_id: str = Depends(require_admin)):
    try:
        users = await UserManagementController.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=Dict)
async def get_user(user_id: str, admin_user_id: str = Depends(require_admin)):
    try:
        user = await UserManagementController.get_user_by_id(user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=Dict)
async def update_user(
    user_id: str, 
    user_data: Dict,
    admin_user_id: str = Depends(require_admin)
):


    try:
        updated_user = await UserManagementController.update_user(user_id, user_data)
        return {
            "message": "Usuario actualizado exitosamente",
            "user": updated_user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/deactivate", response_model=Dict)
async def deactivate_user(user_id: str, admin_user_id: str = Depends(require_admin)):
    """
    """
    try:
        result = await UserManagementController.deactivate_user(user_id)
        return {
            "message": "Usuario desactivado exitosamente",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/activate", response_model=Dict)
async def activate_user(user_id: str, admin_user_id: str = Depends(require_admin)):

    try:
        result = await UserManagementController.activate_user(user_id)
        return {
            "message": "Usuario reactivado exitosamente",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))