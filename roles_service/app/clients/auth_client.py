
import httpx
import os
from typing import List, Dict, Optional
from fastapi import HTTPException

# URL del servicio de autenticación
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

class AuthServiceClient:
    """Cliente para comunicarse con el servicio de autenticacion"""
    
    def __init__(self):
        self.base_url = AUTH_SERVICE_URL
        self.timeout = 30.0
    
    async def get_all_users(self) -> List[Dict]:
        """Obtener todos los usuarios del servicio de auth"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/users")
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Error conectando con el servicio de autenticación: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error del servicio de autenticación: {e.response.text}"
            )
    
    async def get_user_by_id(self, user_id: str) -> Dict:
        """Obtener un usuario por ID"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/users/{user_id}")
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error conectando con el servicio de autenticación: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error del servicio de autenticación: {e.response.text}"
            )
    
    async def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """Actualizar datos de un usuarios"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/users/{user_id}",
                    json=user_data
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error conectando con el servicio de autenticación: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error del servicio de autenticación: {e.response.text}"
            )
    
    async def deactivate_user(self, user_id: str) -> Dict:
        """Desactivar un usuario"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/users/{user_id}/deactivate")
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error conectando con el servicio de autenticación: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error del servicio de autenticación: {e.response.text}"
            )
    
    async def activate_user(self, user_id: str) -> Dict:
        """Reactivar un usuario"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(f"{self.base_url}/users/{user_id}/activate")
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error conectando con el servicio de autenticación: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error del servicio de autenticación: {e.response.text}"
            )

# Instancia global del cliente
auth_client = AuthServiceClient()
