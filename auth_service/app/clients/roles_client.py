import httpx
import os
from typing import Optional
from fastapi import HTTPException

# URL del servicio de roles
ROLES_SERVICE_URL = os.getenv("ROLES_SERVICE_URL", "http://roles-service:8001")

class RolesServiceClient:
    """Cliente para comunicarse con el servicio de roles"""
    
    def __init__(self):
        self.base_url = ROLES_SERVICE_URL
        self.timeout = 30.0
    
    def _format_uuid(self, uid: str) -> str:
        """Convertir UID sin guiones al formato UUID con guiones"""
        if len(uid) == 32 and '-' not in uid:
            # Formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
        return uid
    
    async def get_user_role(self, user_id: str) -> Optional[str]:
        """Obtener el rol de un usuario desde el servicio de roles"""
        try:
            # Convertir el UID al formato correcto con guiones
            formatted_user_id = self._format_uuid(user_id)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Usar el endpoint interno que no requiere autenticación
                response = await client.get(f"{self.base_url}/roles/internal/user-role/{formatted_user_id}")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("role")  # Cambiado de "role_name" a "role"
                elif response.status_code == 404:
                    # Usuario sin rol asignado, devolver rol por defecto
                    return "usuario"
                else:
                    response.raise_for_status()
        except httpx.RequestError as e:
            print(f"Error conectando con el servicio de roles: {str(e)}")
            # En caso de error, devolver rol por defecto
            return "usuario"
        except httpx.HTTPStatusError as e:
            print(f"Error del servicio de roles: {e.response.text}")
            # En caso de error, devolver rol por defecto
            return "usuario"
        except Exception as e:
            print(f"Error inesperado consultando rol: {str(e)}")
            return "usuario"

# Instancia global del cliente
roles_client = RolesServiceClient()
