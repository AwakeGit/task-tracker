from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))

    created_tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner", foreign_keys="Task.owner_id"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="executor", foreign_keys="Task.executor_id"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    theme: Mapped[str] = mapped_column(String(100), default="общее")
    status: Mapped[str] = mapped_column(
        Enum("new", "in_progress", "done", "cancelled", name="task_status"),
        default="new",
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    executor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="created_tasks", foreign_keys=[owner_id])
    executor: Mapped[User | None] = relationship(
        back_populates="assigned_tasks", foreign_keys=[executor_id]
    )
