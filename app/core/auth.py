from __future__ import annotations
import jwt
from jwt import *
from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import config
from app.db.database import get_db
from app.schemas.Users import User as UserModel  # Modelo SQLAlchemy

# Modelos Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
router = APIRouter()


# Função para verificar a senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Função para gerar o hash da senha
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Função para buscar o usuário no banco de dados
async def get_user(db: AsyncSession, username: str | None) -> UserInDB | None:
    if username is None:
        return None
    result = await db.execute(select(UserModel).filter(UserModel.name == username))
    user = result.scalars().first()
    if user:
        return UserInDB(username=user.name, hashed_password=user.hashed_password)
    return None


# Função para autenticar o usuário no banco de dados
async def authenticate_user(db: AsyncSession, username: str, password: str) -> UserInDB | bool:
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# Função para criar o token JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        config.API_SECRET_KEY,
        algorithm=config.API_ALGORITHM,
    )
    return encoded_jwt


# Função para obter o usuário atual a partir do token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            config.API_SECRET_KEY,
            algorithms=[config.API_ALGORITHM],
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user
