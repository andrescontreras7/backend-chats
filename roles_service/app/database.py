from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os


try:
    load_dotenv()
except:
    pass

# Leer DATABASE_URL desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno")

# Crear motor de conexion
engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
