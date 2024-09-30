from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from app.schemas.Users import User as UserModel  # Modelo SQLAlchemy
from app.models.usersModel import User, UserCreate  # Modelos Pydantic
from app.db.database import get_db
from passlib.context import CryptContext
from app.core.auth import get_current_user


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Função para gerar o hash da senha
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# GET - Obter um usuário por ID (ordem alterada para ser o primeiro)
@router.get("/{user_id}", response_model=User, summary="GET user by ID", description="Essa rota busca um Usuário a partir do ID")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# POST - Criar um novo usuário
@router.post("/create", response_model=User, summary="POST user", description="Essa rota cria um usuário")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password
    )
    
    # Tente adicionar o novo usuário e fazer commit
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    # Capturar erro de unicidade (email duplicado)
    except IntegrityError as e:
        await db.rollback()  # Faz o rollback em caso de erro
        # Verificar se o erro é de chave única (UniqueViolationError)
        if 'UniqueViolation' in str(e.orig):
            raise HTTPException(
                status_code=400, 
                detail=f"O email '{user.email}' já está em uso."
            )
        # Relançar outras exceções de integridade que possam ocorrer
        raise HTTPException(
            status_code=500, 
            detail="Erro inesperado no servidor."
        )
# PUT - Atualizar um usuário por ID
@router.put("/{user_id}", response_model=User, summary="PUT user by ID", description="Essa rota Altera um Usuário a partir do ID dele")
async def update_user(user_id: int, user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    db_user = result.scalars().first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = user.name
    db_user.email = user.email
    db_user.hashed_password = get_password_hash(user.password)
    
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

# DELETE - Remover um usuário por ID
@router.delete("/{user_id}", response_model=dict, summary="DELETE user by ID", description="Essa rota exclui um usuário a partir do ID")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    db_user = result.scalars().first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(db_user)
    await db.commit()
    
    return {"message": "Usuário removido com sucesso"}
