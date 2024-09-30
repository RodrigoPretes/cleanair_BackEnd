from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.Users import User as UserModel  # Modelo SQLAlchemy
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.auth import create_access_token
from app.db.database import get_db
from app.core.auth import Token  # Importar o modelo Token para o response_model
from http import HTTPStatus
from app.core import config

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Função para verificar a senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Função para autenticar o usuário no banco de dados
async def authenticate_user(db: AsyncSession, username: str, password: str):
    # Buscar o usuário no banco de dados
    result = await db.execute(select(UserModel).filter(UserModel.name == username))
    user = result.scalars().first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Endpoint para gerar o token de acesso JWT
@router.post(
    "/token",
    response_model=Token,
    summary="Gerar token de acesso",
    description="Esta rota gera o token de acesso JWT. Insira o nome de usuário e senha para obter o token."
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)  # Passar a sessão do banco de dados
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(seconds=config.API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.name},  # Usar o nome do usuário como "subject"
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
