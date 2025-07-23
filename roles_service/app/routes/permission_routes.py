from fastapi import APIRouter, Depends
from sqlmodel import Session
from database import get_session
from schemas.permission_schema import PermissionCreate, PermissionResponse
from controllers.permission_controller import create_permission, get_all_permissions, delete_permission, update_permission
from auth.auth_middleware import require_admin, get_current_user_with_role

router = APIRouter()

@router.post("/create-permission", response_model=PermissionResponse)
def create(
    data: PermissionCreate, 
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):

    return create_permission(data, session)

@router.get("/", response_model=list[PermissionResponse])
def list_permissions_root(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_with_role)
):
  
    return get_all_permissions(session)

@router.get("/list-permissions", response_model=list[PermissionResponse])
def list_permissions(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_with_role)
):

    return get_all_permissions(session)

@router.put("/update-permission/{permission_id}", response_model=PermissionResponse)
def update(
    permission_id: str,
    data: PermissionCreate,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
    """Actualizar un permiso. Solo administradores."""
    return update_permission(permission_id, data, session)

@router.delete("/delete-permission/{permission_id}")
def delete(
    permission_id: str,
    session: Session = Depends(get_session),
    admin_user: str = Depends(require_admin)
):
  
    return delete_permission(permission_id, session)

