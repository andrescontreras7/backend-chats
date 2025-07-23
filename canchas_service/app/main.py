from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routes.cancha_routes import router as cancha_router
from routes.reserva_routes import router as reserva_router
from routes.cancha_disponibilidad_routes import router as disponibilidad_router
from routes.cancha_dia_especial_routes import router as dia_especial_router
from routes.disponibilidad_calendario_routes import router as calendario_router
from auth.auth_middleware import get_current_user

# Crear la aplicación FastAPI
app = FastAPI(
    title="Servicio de Canchas",
    description="API para gestión de canchas deportivas y reservas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas
app.include_router(cancha_router, prefix="/canchas", tags=["Canchas"])
app.include_router(reserva_router, prefix="/reservas", tags=["Reservas"])
app.include_router(disponibilidad_router, tags=["Disponibilidad"])
app.include_router(dia_especial_router, tags=["Días Especiales"])
app.include_router(calendario_router, tags=["Calendario"])

@app.on_event("startup")
def on_startup():
    """Crear las tablas de la base de datos al iniciar"""
    create_db_and_tables()

@app.get("/")
def read_root():
    """Endpoint raíz del servicio de canchas"""
    return {
        "message": "Servicio de Canchas API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy"}

@app.get("/test-auth")
def test_auth(current_user: dict = Depends(get_current_user)):
    """Endpoint de prueba para verificar autenticación"""
    return {"message": "Token válido", "user": current_user}
