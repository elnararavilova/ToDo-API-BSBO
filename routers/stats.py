from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Task
from database import get_async_session
from datetime import datetime, timezone

router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)


@router.get("/", response_model=dict)
async def get_tasks_stats(
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    total_tasks = len(tasks)
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}

    for task in tasks:
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1

        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }


@router.get("/deadlines", response_model=list)
async def urgent_deadline_stats(
    db: AsyncSession = Depends(get_async_session)
) -> list:

    result = await db.execute(
        select(Task).where(Task.completed == False)  
    )
    tasks = result.scalars().all()

    today = datetime.now(timezone.utc).date()
    output = []

    for task in tasks:
        # если дедлайн не задан (NULL в БД) — пропускаем такую задачу
        if task.deadline_at is None:
            continue

        remaining_days = (task.deadline_at.date() - today).days

        output.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "created_at": task.created_at,
            "deadline_at": task.deadline_at,
            "remaining_days": remaining_days
        })

    return output
