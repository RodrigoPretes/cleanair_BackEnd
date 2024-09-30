from fastapi import FastAPI
from app.db.database import engine, Base
from app.api.v1.endpoints import users, login, temperatura
from app.api.v1.endpoints import login
from starlette.middleware.cors import CORSMiddleware

# Definir as tags no OpenAPI
tags_metadata = [
    {"name": "Authentication", "description": "Autenticação"},
    {"name": "Users", "description": "Rotas de Usuários"},
    {"name": "MQTT", "description": "Rotas de Inserção de dados e recebimento via MQTT"}
]

app = FastAPI(openapi_tags=tags_metadata)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o banco de dados (cria as tabelas no PostgreSQL)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
# login
app.include_router(
    login.router,
    prefix="/auth",
    tags=["Authentication"]
)
# Usuarios
app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)
# MQTT
app.include_router(
    temperatura.router,
    prefix="/MQTT",
    tags=["MQTT"]
)


