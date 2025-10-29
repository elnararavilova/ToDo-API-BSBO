from fastapi import APIRouter
from database import tasks_db

router = APIRouter(
    prefix="/stats",           # все endpoints начнутся с /stats
    tags=["stats"],            # группировка в Swagger UI
    responses={404: {"description": "Stats not found"}},
)

@router.get("")
async def get_tasks_stats() -> dict:
    # Общее количество задач
    total_tasks = len(tasks_db)

    # Количество задач по квадрантам
    by_quadrant = {
        "Q1": len([task for task in tasks_db if task["quadrant"] == "Q1"]),
        "Q2": len([task for task in tasks_db if task["quadrant"] == "Q2"]),
        "Q3": len([task for task in tasks_db if task["quadrant"] == "Q3"]),
        "Q4": len([task for task in tasks_db if task["quadrant"] == "Q4"]),
    }

    # Количество задач по статусу выполнения
    completed_tasks = len([task for task in tasks_db if task["completed"]])
    pending_tasks = len([task for task in tasks_db if not task["completed"]])

    by_status = {
        "completed": completed_tasks,
        "pending": pending_tasks,
    }

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status,
    }
