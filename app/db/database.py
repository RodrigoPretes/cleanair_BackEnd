import pathlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from starlette.config import Config

ROOT = pathlib.Path(__file__).resolve().parent.parent  # app/
BASE_DIR = ROOT.parent  # ./

config = Config(BASE_DIR / ".env")

# Defina a URL de conexão para o PostgreSQL
DATABASE_URL = config("DATABASE_URL", str)


# Cria o engine assíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Configura a sessão assíncrona
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Base para as classes de modelo do banco de dados
Base = declarative_base()

# Função que retorna uma sessão do banco de dados
async def get_db():
    async with SessionLocal() as session:
        yield session
