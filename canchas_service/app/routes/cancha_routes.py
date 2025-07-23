from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from database import get_session
from schemas.cancha_schema import CanchaSchema, CanchaCreateSchema, CanchaUpdateSchema
from controllers.cancha_controller import (
    create_cancha, get_all_canchas, get_cancha_by_id, update_cancha, 
    delete_cancha, get_canchas_by_tipo, get_canchas_disponibles
)
from models.cancha_model import CanchaCreate, CanchaUpdate
from auth.auth_middleware import require_admin, get_current_user
from typing import List

router = APIRouter()

@router.post("/create", response_model=CanchaSchema)
def create_cancha_route(
    cancha_data: CanchaCreateSchema,
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Crear una nueva cancha. Solo administradores."""
    cancha_create = CanchaCreate(**cancha_data.model_dump())
    return create_cancha(cancha_create, session)

@router.get("/", response_model=List[CanchaSchema])
def get_canchas_route(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    incluir_no_disponibles: bool = Query(False, description="Incluir canchas no disponibles (solo admin)"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
  
    if incluir_no_disponibles and current_user.get("role") != "administrador":
        incluir_no_disponibles = False
    
    return get_all_canchas(session, skip, limit, incluir_no_disponibles)

@router.get("/disponibles", response_model=List[CanchaSchema])
def get_canchas_disponibles_route(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener solo las canchas disponibles."""
    return get_canchas_disponibles(session)

@router.get("/admin/todas", response_model=List[CanchaSchema])
def get_all_canchas_admin_route(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Obtener TODAS las canchas incluyendo no disponibles. Solo administradores."""
    return get_all_canchas(session, skip, limit, incluir_no_disponibles=True)

@router.get("/tipo/{tipo_deporte}", response_model=List[CanchaSchema])
def get_canchas_by_tipo_route(
    tipo_deporte: str,
    incluir_no_disponibles: bool = Query(False, description="Incluir canchas no disponibles (solo admin)"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener canchas por tipo de deporte. Por defecto solo muestra canchas disponibles."""
    # Solo permitir ver canchas no disponibles si es admin
    if incluir_no_disponibles and current_user.get("role") != "administrador":
        incluir_no_disponibles = False
    
    return get_canchas_by_tipo(tipo_deporte, session, incluir_no_disponibles)

@router.get("/{cancha_id}", response_model=CanchaSchema)
def get_cancha_route(
    cancha_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener una cancha específica por ID."""
    return get_cancha_by_id(cancha_id, session)

@router.put("/{cancha_id}", response_model=CanchaSchema)
def update_cancha_route(
    cancha_id: str,
    cancha_data: CanchaUpdateSchema,
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Actualizar una cancha. Solo administradores."""
    cancha_update = CanchaUpdate(**cancha_data.model_dump(exclude_unset=True))
    return update_cancha(cancha_id, cancha_update, session)

@router.delete("/{cancha_id}")
def delete_cancha_route(
    cancha_id: str,
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Eliminar una cancha. Solo administradores."""
    return delete_cancha(cancha_id, session)
