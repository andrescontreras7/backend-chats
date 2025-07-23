# Backend Canchas - Sistema de Gestión de Canchas Deportivas

Sistema de microservicios para gestión de canchas deportivas desarrollado con FastAPI, MySQL y Docker.

##  Arquitectura del Sistema

El proyecto está compuesto por tres microservicios principales:

- **Auth Service** (Puerto 8000): Gestión de autenticación y usuarios
- **Roles Service** (Puerto 8001): Gestión de roles y permisos
- **Canchas Service** (Puerto 8002): Gestión de canchas y reservas
- **API Gateway** (Puerto 3001): Nginx como proxy reverso

## Prerrequisitos

- [Docker](https://www.docker.com/get-started) 
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Instalacion y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/backend-canchas.git
cd backend-canchas
```

### 2. Construir y levantar los contenedores

#### Opción A: Usar Docker Compose básico
```bash
docker-compose -f compose.yml up --build
```

#### Opción B: Usar Docker Compose con Gateway (Recomendado)
```bash
docker-compose -f compose-with-gateway.yml up --build
```

### 3. Verificar que los servicios estén funcionando

Una vez que los contenedores estén ejecutándose, puedes verificar el estado:

```bash
docker-compose ps
```

## Acceso a los Servicios

### APIs
- **API Gateway**: http://localhost:3001
- **Auth Service**: http://localhost:8000
- **Roles Service**: http://localhost:8001  
- **Canchas Service**: http://localhost:8002

### Documentación de APIs (Swagger)
- **Auth Service**: http://localhost:8000/docs
- **Roles Service**: http://localhost:8001/docs
- **Canchas Service**: http://localhost:8002/docs

### Bases de Datos (phpMyAdmin)
- **Auth DB**: http://localhost:8080
- **Roles DB**: http://localhost:8081
- **Canchas DB**: http://localhost:8082 (si está configurado)

**Credenciales de MySQL:**
- Usuario: `root`
- Contraseña: `rootpass`

### RabbitMQ Management
- **Panel de administración**: http://localhost:15672
- Usuario: `admin`
- Contraseña: `admin`

## 🛠️ Comandos Útiles

### Levantar solo servicios específicos
```bash
# Solo el servicio de autenticación
docker-compose up auth-service auth_mysql

# Solo el servicio de canchas
docker-compose up canchas-service canchas_mysql
```

### Reconstruir contenedores
```bash
# Reconstruir todo
docker-compose up --build --force-recreate

# Reconstruir un servicio específico
docker-compose up --build auth-service
```

### Ver logs de servicios
```bash
# Logs de todos los servicios
docker-compose logs -f

# Logs de un servicio específico
docker-compose logs -f auth-service
```

### Ejecutar comandos dentro de contenedores
```bash
# Acceder al bash del servicio de auth
docker-compose exec auth-service bash

# Ejecutar migraciones (ejemplo)
docker-compose exec auth-service python -m alembic upgrade head
```

### Detener y limpiar
```bash
# Detener contenedores
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Limpiar todo (contenedores, redes, volúmenes, imágenes)
docker-compose down -v --rmi all
```

## Estructura del Proyecto

```
backend-canchas/
├── auth_service/          # Microservicio de autenticación
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── roles_service/         # Microservicio de roles
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── canchas_service/       # Microservicio de canchas
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── compose.yml           # Docker Compose básico
├── compose-with-gateway.yml  # Docker Compose con Gateway
├── nginx.conf            # Configuración del API Gateway
└── README.md
```

## 🔧 Variables de Entorno

Las variables de entorno principales se configuran en los archivos docker-compose:

- `DATABASE_URL`: URL de conexión a MySQL
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo de encriptación (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración de tokens
- `RABBITMQ_URL`: URL de conexión a RabbitMQ

## Desarrollo

### Modo desarrollo
Para desarrollo con hot-reload, los contenedores están configurados con volúmenes que mapean el código fuente:

```bash
docker-compose -f compose.yml up
```

Los cambios en el código se reflejarán automáticamente sin necesidad de reconstruir los contenedores.

### Instalación de dependencias
```bash
# Instalar nuevas dependencias en un servicio
docker-compose exec auth-service pip install nueva-libreria

# Actualizar requirements.txt
docker-compose exec auth-service pip freeze > requirements.txt
```

##  Solución de Problemas

### Los contenedores no se levantan
1. Verificar que Docker esté ejecutándose
2. Verificar que los puertos no estén ocupados
3. Revisar los logs: `docker-compose logs`

### Error de conexión a base de datos
1. Esperar a que los healthchecks de MySQL pasen
2. Verificar las credenciales en docker-compose
3. Revisar los logs de MySQL: `docker-compose logs auth_mysql`

### Puerto ya en uso
```bash
# Verificar qué proceso usa el puerto
netstat -ano | findstr :8000

# Cambiar el puerto en docker-compose.yml si es necesario
```

## API Endpoints Principales

### Auth Service
- `POST /register` - Registrar usuario
- `POST /login` - Iniciar sesión
- `GET /users/me` - Obtener perfil

### Canchas Service
- `GET /canchas/` - Listar canchas
- `POST /canchas/create` - Crear cancha (admin)
- `GET /canchas/{id}` - Obtener cancha específica
- `PUT /canchas/{id}` - Actualizar cancha (admin)

### Roles Service
- `GET /roles/` - Listar roles
- `POST /roles/` - Crear rol (admin)
- `GET /permissions/` - Listar permisos




- Tu Andres cavadia - Desarrollador Principal
