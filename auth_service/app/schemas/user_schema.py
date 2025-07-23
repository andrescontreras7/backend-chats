from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    last_name: str = Field(min_length=1, max_length=50)
    is_active: bool = True

    class Config:
        orm_mode = True

    class Config:
        orm_mode = True


# Login
class UserLogin(BaseModel):
    email: EmailStr 
    password: str = Field(min_length=1, max_length=128)

# Actualización de usuario
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)

# Respuesta segura (sin el password)
class UserResponse(BaseModel):
    uid: str  # Cambiar id por uid para consistencia
    username: str
    email: EmailStr
    last_name: str
    is_active: bool

    class Config:
        from_attributes = True  # Para usar con SQLAlchemy
