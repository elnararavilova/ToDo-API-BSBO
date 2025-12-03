from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models import Task, User          # User нужен для type hint
from schemas import TimingStatsResponse, TaskResponse
from routers.auth import get_current_user   # берём текущего юзера

router = APIRouter(
    prefix="/stats",
    tags=["statistics"],
)


@router.get("/", response_model=dict)
async def get_tasks_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> dict:

    user_filter = []
    if current_user.role.value != "admin":
        user_filter = [Task.user_id == current_user.id]

    # Общее количество задач
    total_result = await db.execute(
        select(func.count(Task.id)).where(*user_filter)
    )
    total_tasks = total_result.scalar() or 0

    # Подсчёт по квадрантам
    quadrant_result = await db.execute(
        select(
            Task.quadrant,
            func.count(Task.id).label("count"),
        )
        .where(*user_filter)
        .group_by(Task.quadrant)
    )

    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for row in quadrant_result:
        by_quadrant[row.quadrant] = row.count

    # Подсчёт по статусу
    status_result = await db.execute(
        select(
            func.count(case((Task.completed == True, 1))).label("completed"),
            func.count(case((Task.completed == False, 1))).label("pending"),
        ).where(*user_filter)
    )
    status_row = status_result.one()

    by_status = {
        "completed": status_row.completed or 0,
        "pending": status_row.pending or 0,
    }

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status,
    }


@router.get("/timing", response_model=TimingStatsResponse)
async def get_deadline_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> TimingStatsResponse:

    now_utc = datetime.now(timezone.utc)

    statement = select(
        func.sum(
            case(
                (
                    (Task.completed == True)
                    & (Task.completed_at <= Task.deadline_at),
                    1,
                ),
                else_=0,
            )
        ).label("completed_on_time"),
        func.sum(
            case(
                (
                    (Task.completed == True)
                    & (Task.completed_at > Task.deadline_at),
                    1,
                ),
                else_=0,
            )
        ).label("completed_late"),
        func.sum(
            case(
                (
                    (Task.completed == False)
                    & (Task.deadline_at != None)
                    & (Task.deadline_at > now_utc),
                    1,
                ),
                else_=0,
            )
        ).label("on_plan_pending"),
        func.sum(
            case(
                (
                    (Task.completed == False)
                    & (Task.deadline_at != None)
                    & (Task.deadline_at <= now_utc),
                    1,
                ),
                else_=0,
            )
        ).label("overdue_pending"),
    ).select_from(Task)

    if current_user.role.value != "admin":
        statement = statement.where(Task.user_id == current_user.id)

    result = await db.execute(statement)
    stats_row = result.one()

    return TimingStatsResponse(
        completed_on_time=stats_row.completed_on_time or 0,
        completed_late=stats_row.completed_late or 0,
        on_plan_pending=stats_row.on_plan_pending or 0,
        overtime_pending=stats_row.overdue_pending or 0,
    )


@router.get("/today", response_model=list[TaskResponse])
async def get_today_tasks(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:

    today = datetime.now(timezone.utc).date()

    stmt = select(Task).where(
        Task.deadline_at.is_not(None),
        func.date(Task.deadline_at) == today,
        Task.completed == False,
    )

    if current_user.role.value != "admin":
        stmt = stmt.where(Task.user_id == current_user.id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return tasks
