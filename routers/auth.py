from fastapi import APIRouter, Depends, HTTPException, status 
from fastapi.security import OAuth2PasswordRequestForm 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select, func
from database import get_async_session 
from models import User, UserRole, Task 
from schemas_auth import UserCreate, UserResponse, Token, ChangePasswordRequest, AdminUserStats 
from auth_utils import verify_password, get_password_hash, create_access_token 
from dependencies import get_current_user, get_current_admin
from typing import List


 
 
router = APIRouter( 
    prefix="/auth", 
    tags=["authentication"] 
) 
 
 
@router.post("/register", response_model=UserResponse, 
            status_code=status.HTTP_201_CREATED) # Регистрация нового пользователя 
async def register( 
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_async_session) 
): 
    # Проверяем, не занят ли email 
    result = await db.execute( 
        select(User).where(User.email == user_data.email) 
    ) 
    if result.scalar_one_or_none(): 
        raise HTTPException( 
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Пользователь с таким email уже существует" 
        ) 
    
    # Проверяем, не занят ли nickname 
    result = await db.execute( 
        select(User).where(User.nickname == user_data.nickname) 
    ) 
    if result.scalar_one_or_none(): 
        raise HTTPException( 
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Пользователь с таким никнеймом уже существует" 
        ) 
    
    # Создаем нового пользователя 
    new_user = User( 
        nickname=user_data.nickname, 
        email=user_data.email, 
        hashed_password=get_password_hash(user_data.password), 
        role=UserRole.USER  # По умолчанию обычный пользователь 
    ) 
    
    db.add(new_user) 
    await db.commit() 
    await db.refresh(new_user) 
    
    return new_user 
 
 
@router.post("/login", response_model=Token) 
async def login( 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_async_session) 
): 
    # Ищем пользователя по email (username в форме = email) 
    result = await db.execute( 
        select(User).where(User.email == form_data.username) 
    ) 
    user = result.scalar_one_or_none() 
    
    # Проверяем пользователя и пароль 
    if not user or not verify_password(form_data.password, 
user.hashed_password): 
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Неверный email или пароль", 
            headers={"WWW-Authenticate": "Bearer"}, 
        ) 
    
    # Создаем JWT токен 
    access_token = create_access_token( 
        data={"sub": str(user.id), "role": user.role.value} 
    ) 
    
    return {"access_token": access_token, "token_type": "bearer"} 
 
 
@router.get("/me", response_model=UserResponse) #Получаем информацию о текущем пользователе. 
async def get_me( 
    current_user: User = Depends(get_current_user) 
): 
    from dependencies import get_current_user 
    return current_user

@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    # проверяем старый пароль
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Старый пароль указан неверно",
        )

    # хешируем новый и сохраняем
    current_user.hashed_password = get_password_hash(data.new_password)
    db.add(current_user)
    await db.commit()

    return {"detail": "Пароль успешно изменён"}

@router.get("/admin/users", response_model=list[AdminUserStats])
async def get_users_with_task_counts(
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin),
):
    # current_admin нужен только для проверки прав (get_current_admin выкинет 403 если не админ)

    stmt = (
        select(
            User.id.label("user_id"),
            User.nickname,
            User.email,
            func.count(Task.id).label("tasks_count"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.nickname, User.email)
        .order_by(User.id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        AdminUserStats(
            user_id=row.user_id,
            nickname=row.nickname,
            email=row.email,
            tasks_count=row.tasks_count,
        )
        for row in rows
    ]


