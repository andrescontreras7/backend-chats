"""
Controlador para gestión de usuarios desde el servicio de roles
"""
from typing import List, Dict, Optional
from fastapi import HTTPException
from clients.auth_client import auth_client

class UserManagementController:
    """Controlador para gestión de usuarios por parte del admin"""
    
    @staticmethod
    async def get_all_users() -> List[Dict]:
    
        try:
            users = await auth_client.get_all_users()
            return users
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo usuarios: {str(e)}"
            )
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Dict:
        """
        Obtener un usuario específico por ID
        
        """
        try:
            user = await auth_client.get_user_by_id(user_id)
            return user
        except HTTPException:
            # Re-lanzar las excepciones HTTP del cliente
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo usuario: {str(e)}"
            )
    
    @staticmethod
    async def update_user(user_id: str, user_data: Dict) -> Dict:
        """
        Actualizar datos de un usuario
        
        """
        try:
            # Validar que no se esté intentando cambiar datos críticos
            forbidden_fields = {'id', 'password_hash', 'created_at'}
            if any(field in user_data for field in forbidden_fields):
                raise HTTPException(
                    status_code=400,
                    detail="No se pueden modificar campos protegidos"
                )
            
            updated_user = await auth_client.update_user(user_id, user_data)
            return updated_user
        except HTTPException:
            # Re-lanzar las excepciones HTTP del cliente
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error actualizando usuario: {str(e)}"
            )
    
    @staticmethod
    async def deactivate_user(user_id: str) -> Dict:
        """
        Desactivar un usuario (soft delete)
        
        """
        try:
            result = await auth_client.deactivate_user(user_id)
            return result
        except HTTPException:
            # Re-lanzar las excepciones HTTP del cliente
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error desactivando usuario: {str(e)}"
            )
    
    @staticmethod
    async def activate_user(user_id: str) -> Dict:
        """
        Reactivar un usuario
        """
        try:
            result = await auth_client.activate_user(user_id)
            return result
        except HTTPException:
            # Re-lanzar las excepciones HTTP del cliente
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reactivando usuario: {str(e)}"
            )
