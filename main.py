from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import init_db, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from routers import tasks, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("Запуск приложения...")
    print("Инициализация базы данных...")
    await init_db()
    print("Приложение готово к работе!")
    yield
    
    print("Остановка приложения...")


app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="2.0.0",
    contact={
        "name": "Ваше Имя",
    },
    lifespan=lifespan
)


app.include_router(tasks.router, prefix="/api/v2")
app.include_router(stats.router, prefix="/api/v2")


@app.get("/")
async def read_root() -> dict:
    return {
        "message": "Task Manager API — управление задачами по матрице Эйзенхауэра",
        "version": "2.0.0",
        "database": "PostgreSQL (Supabase)",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Проверка здоровья API и динамическая проверка подключения к БД.
    """
    try:
        
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status
    }
