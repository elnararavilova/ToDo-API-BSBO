from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    title = Column(
        Text,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    is_important = Column(
        Boolean,
        nullable=False,
        default=False
    )

    is_urgent = Column(
        Boolean,
        nullable=False,
        default=False
    )

    quadrant = Column(
        String(2),
        nullable=False
    )

    completed = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Новый столбец: дедлайн
    deadline_at = Column(
        DateTime(timezone=True),
        nullable=False
    )
