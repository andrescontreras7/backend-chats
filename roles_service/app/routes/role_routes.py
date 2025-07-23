from fastapi import APIRouter, Depends
from sqlmodel import Session
from database import get_session
from schemas.role_schema import RoleCreate, RoleResponse, AssignRoleByName, AssignRoleByUID, RoleAssignmentResponse
from controllers.role_controller import (
    create_role, get_all_roles, delete_role, update_role,
    get_role_by_name, assign_role_to_user_by_name, assign_role_to_user_by_uid, get_user_role_name
)
from auth.auth_middleware import require_admin, get_current_user_with_role

router = APIRouter()

@router.post("/create-role", response_model=RoleResponse)
def create(
    data: RoleCreate, 
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Crear un nuevo rol. Solo administradores."""
    return create_role(data, session)

@router.get("/list-roles", response_model=list[RoleResponse])
def list_roles(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_with_role)
):
    """Listar roles. Requiere autenticación."""
    return get_all_roles(session)

@router.put("/update-role/{role_id}", response_model=RoleResponse)
def update(
    role_id: str,
    data: RoleCreate,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Actualizar un rol. Solo administradores."""
    return update_role(role_id, data, session)

@router.delete("/delete-role/{role_id}")
def delete(
    role_id: str,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Eliminar un rol. Solo administradores."""
    return delete_role(role_id, session)

# Nuevas rutas para trabajar con roles por nombre
@router.get("/get-role-by-name/{role_name}", response_model=RoleResponse)
def get_role_by_name_route(
    role_name: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_with_role)
):
    """Obtener un rol por su nombre. Requiere autenticación."""
    role = get_role_by_name(role_name, session)
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Rol '{role_name}' no encontrado")
    return role

@router.post("/assign-role-by-name", response_model=RoleAssignmentResponse)
def assign_role_by_name_route(
    assign_data: AssignRoleByName,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Asignar un rol a un usuario usando el nombre del rol. Solo administradores."""
    return assign_role_to_user_by_name(assign_data.user_id, assign_data.role_name, session)

@router.post("/assign-role-by-uid", response_model=RoleAssignmentResponse)
def assign_role_by_uid_route(
    assign_data: AssignRoleByUID,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Asignar un rol a un usuario usando el UID del rol. Solo administradores."""
    return assign_role_to_user_by_uid(assign_data.user_id, assign_data.role_uid, session)

# Endpoint público para consultas externas (requiere autenticación)
@router.get("/user-role/{user_id}")
def get_user_role_route(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_with_role)
):
    """Obtener el rol de un usuario. Requiere autenticación."""
    role_name = get_user_role_name(user_id, session)
    if not role_name:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuario no tiene rol asignado")
    return {"user_id": user_id, "role": role_name}

# Endpoint interno para comunicación entre servicios (sin autenticación)
@router.get("/internal/user-role/{user_id}")
def get_user_role_internal(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Obtener el rol de un usuario. Endpoint interno para comunicación entre servicios."""
    role_name = get_user_role_name(user_id, session)
    if not role_name:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Usuario no tiene rol asignado")
    return {"user_id": user_id, "role": role_name}
