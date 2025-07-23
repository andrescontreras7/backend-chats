from sqlmodel import SQLModel, create_engine, Session
import os

# Importar todos los modelos para que SQLModel los registre
from models.cancha_model import Cancha
from models.reserva_model import Reserva
from models.cancha_disponibilidad_model import CanchaDisponibilidad
from models.cancha_dia_especial_model import CanchaDiaEspecial

# URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:rootpass@localhost:3309/canchas_service")

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Crear las tablas de la base de datos"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Obtener una sesión de la base de datos"""
    with Session(engine) as session:
        yield session
