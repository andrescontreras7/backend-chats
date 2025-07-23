from fastapi import HTTPException
from sqlmodel import Session, select
from models.role_models import Role
from schemas.role_schema import RoleCreate
from models.user_role import UserRole
from database import get_session


def create_role(data: RoleCreate, session: Session):
    exists = session.exec(select(Role).where(Role.name == data.name)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Rol ya existe")

    role = Role(**data.dict())
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

def get_all_roles(session: Session):
    return session.exec(select(Role)).all()

def update_role(role_id: str, data: RoleCreate, session: Session):
    role = session.exec(select(Role).where(Role.uid == role_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Verificar que no exista otro rol con el mismo nombre
    existing = session.exec(select(Role).where(Role.name == data.name, Role.uid != role_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    
    role.name = data.name
    role.description = data.description
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

def delete_role(role_id: str, session: Session):
    role = session.exec(select(Role).where(Role.uid == role_id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Verificar que no sea un rol del sistema
    if role.name in ["administrador", "usuario"]:
        raise HTTPException(status_code=400, detail="No se puede eliminar un rol del sistema")
    
    # Verificar que no tenga usuarios asignados
    users_with_role = session.exec(select(UserRole).where(UserRole.role_id == role_id)).all()
    if users_with_role:
        raise HTTPException(status_code=400, detail="No se puede eliminar un rol que tiene usuarios asignados")
    
    session.delete(role)
    session.commit()
    return {"message": "Rol eliminado correctamente"}

async def assign_default_role(user_id: str):
    from database import engine
    with Session(engine) as session:
        try:
            # Verificar si el usuario ya tiene un rol asignado
            already = session.exec(select(UserRole).where(UserRole.user_id == user_id)).first()
            if not already:
              
                default_role = session.exec(select(Role).where(Role.name == "usuario")).first()
                if default_role:
                    user_role = UserRole(user_id=user_id, role_id=str(default_role.uid))
                    session.add(user_role)
                    session.commit()
                    print(f"✅ Rol 'usuario' asignado al usuario {user_id}")
                    return True
                else:
                    print(f"No se encontró el rol por defecto")
                    return False
            else:
                print(f" Usuario {user_id} ya tiene un rol asignado")
                return True
        except Exception as e:
            print(f" Error asignando rol por defecto: {e}")
            session.rollback()
            return False

# Funciones helper para trabajar con roles por nombre
def get_role_by_name(role_name: str, session: Session):
  
    return session.exec(select(Role).where(Role.name == role_name)).first()

def assign_role_to_user_by_name(user_id: str, role_name: str, session: Session):

    role = get_role_by_name(role_name, session)
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol '{role_name}' no encontrado")
    
    # Verificar si el usuario ya tiene un rol asignado
    existing = session.exec(select(UserRole).where(UserRole.user_id == user_id)).first()
    if existing:
        # Actualizar el rol existente
        existing.role_id = str(role.uid)
        session.add(existing)
    else:
        # Crear nueva asignación
        user_role = UserRole(user_id=user_id, role_id=str(role.uid))
        session.add(user_role)
    
    session.commit()
    return {
        "message": f"Rol '{role.name}' asignado al usuario {user_id}",
        "role_name": role.name,
        "role_uid": str(role.uid),
        "user_id": user_id
    }

def get_user_role_name(user_id: str, session: Session):
    """Obtener el nombre del rol de un usuario"""
    user_role = session.exec(select(UserRole).where(UserRole.user_id == user_id)).first()
    if not user_role:
        return None
    
    # Convertir el role_id string a UUID para la búsqueda
    import uuid
    try:
        role_uuid = uuid.UUID(user_role.role_id)
        role = session.exec(select(Role).where(Role.uid == role_uuid)).first()
        return role.name if role else None
    except ValueError:
        # Si role_id no es un UUID válido
        return None

def assign_role_to_user_by_uid(user_id: str, role_uid: str, session: Session):
    """Asignar un rol a un usuario usando el UID del rol"""
    import uuid
    
    try:
        # Convertir el role_uid string a UUID
        role_uuid = uuid.UUID(role_uid)
        
        # Verificar que el rol existe
        role = session.exec(select(Role).where(Role.uid == role_uuid)).first()
        if not role:
            raise HTTPException(status_code=404, detail=f"Rol con UID '{role_uid}' no encontrado")
        
        # Verificar si el usuario ya tiene un rol asignado
        existing = session.exec(select(UserRole).where(UserRole.user_id == user_id)).first()
        if existing:
            # Actualizar el rol existente
            existing.role_id = str(role.uid)
            session.add(existing)
        else:
            # Crear nueva asignación
            user_role = UserRole(user_id=user_id, role_id=str(role.uid))
            session.add(user_role)
        
        session.commit()
        return {
            "message": f"Rol '{role.name}' (UID: {role.uid}) asignado al usuario {user_id}",
            "role_name": role.name,
            "role_uid": str(role.uid),
            "user_id": user_id
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"UID de rol inválido: '{role_uid}'")

def get_role_permissions(role_name: str, session: Session):
    """
    Obtener permisos básicos por rol desde la base de datos.
    Mapea los roles a permisos específicos almacenados en la tabla Permission.
    """
    if not role_name:
        return []
    
    from models.permission import Permission
    
    # Mapeo de roles a permisos desde la base de datos
    role_permissions_map = {
        "administrador": [
            # Gestión de usuarios
            "crear_usuarios", "editar_usuarios", "eliminar_usuarios", "ver_usuarios",
            # Gestión de canchas
            "crear_canchas", "editar_canchas", "eliminar_canchas", "ver_canchas",
            # Gestión de reservas
            "ver_reservas", "crear_reservas", "editar_reservas", "cancelar_reservas",
            # Gestión de pagos
            "ver_pagos", "procesar_pagos", "generar_facturas",
            # Reportes y estadísticas
            "ver_reportes", "generar_reportes", "ver_estadisticas",
            # Administración del sistema
            "gestionar_roles", "gestionar_permisos", "asignar_roles", "otorgar_permisos",
            "configurar_sistema",
            # Mantenimiento
            "ver_logs", "mantenimiento_sistema", "backup_datos"
        ],
        "usuario": [
            # Permisos básicos de usuario
            "ver_canchas", "crear_reservas", "ver_mis_reservas"
        ],
        "gerente": [
            # Gestión de canchas
            "crear_canchas", "editar_canchas", "ver_canchas",
            # Gestión de reservas
            "ver_reservas", "crear_reservas", "editar_reservas", "cancelar_reservas",
            # Reportes
            "ver_reportes", "ver_estadisticas"
        ]
    }
    
    # Obtener la lista de permisos para el rol
    role_permissions = role_permissions_map.get(role_name.lower(), [])
    
    # Verificar que los permisos existan en la base de datos
    existing_permissions = []
    for perm_name in role_permissions:
        permission = session.exec(select(Permission).where(Permission.name == perm_name)).first()
        if permission:
            existing_permissions.append(permission.name)
    
    return existing_permissions
