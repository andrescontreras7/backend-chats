from fastapi import FastAPI
from routes.role_routes import router as role_router
from routes.permission_routes import router as permission_router
from routes.user_management_routes import router as user_management_router
from routes.user_profile_routes import router as user_profile_router
from routes.user_permission_routes import router as user_permission_router
from database import create_db, get_session
from models.role_models import Role
from sqlmodel import Session, select

import asyncio
from events.consumer import consume_user_created

app = FastAPI(title="Roles Service", description="Servicio de Gestión de Roles y Permisos")



def create_default_roles():
    """Crear roles por defecto si no existen"""
    session = next(get_session())
    try:
        # Verificar si ya existen roles
        existing_roles = session.exec(select(Role)).all()
        if not existing_roles:

            admin_role = Role(name="administrador", description="Rol de administrador del sistema")
            user_role = Role(name="usuario", description="Rol de usuario normal")
            
            session.add(admin_role)
            session.add(user_role)
            session.commit()
            session.refresh(admin_role)
            session.refresh(user_role)
            print(" por defecto creados:")
            print(f"   - administrador: {admin_role.uid}")
            print(f"   - usuario: {user_role.uid}")
    except Exception as e:

        session.rollback()
    finally:
        session.close()

@app.on_event("startup")
async def start_event_listener():
    asyncio.create_task(consume_user_created())

@app.get("/")
def root():
    return {"message": "Servicio de Roles - API funcionando correctamente "}
 
@app.on_event("startup")
def on_start():
    create_db()
    create_default_roles()

app.include_router(role_router, prefix="/roles", tags=["Roles"])
app.include_router(permission_router, prefix="/permissions", tags=["Permissions"])
app.include_router(user_management_router, tags=["Gestión de Usuarios"])
app.include_router(user_profile_router, tags=["Perfil de Usuario"])
app.include_router(user_permission_router, tags=["Permisos de Usuario"])
