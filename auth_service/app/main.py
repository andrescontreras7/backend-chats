from fastapi import FastAPI
from routes.user_routes import router as user_router
from routes.admin_routes import router as admin_router
from database import create_db

app = FastAPI(title="Auth Service", description="Servicio de Autenticación")

# CORS manejado por API Gateway - no se configura aquí

create_db()

app.include_router(user_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, tags=["Admin Internal"])

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de reservas de canchas 🎾"}