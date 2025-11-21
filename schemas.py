from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название задачи"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Описание задачи"
    )
    is_important: bool = Field(
        ...,
        description="Важность задачи"
    )
    deadline_at: datetime = Field(
        ...,
        description="Плановый срок выполнения (дедлайн)"
    )


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Новое название"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Новое описание"
    )
    is_important: Optional[bool] = Field(
        None,
        description="Новая важность"
    )
    deadline_at: Optional[datetime] = Field(
        None,
        description="Новый дедлайн"
    )
    completed: Optional[bool] = Field(
        None,
        description="Статус выполнения"
    )


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_important: bool
    is_urgent: bool
    quadrant: str
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime]
    deadline_at: datetime

    class Config:
        from_attributes = True
