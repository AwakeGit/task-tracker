from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    theme: str = "общее"
    executor_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    theme: str | None = None
    executor_id: int | None = None


class TaskStatusUpdate(BaseModel):
    status: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    theme: str
    status: str
    owner_id: int
    executor_id: int | None
    created_at: datetime
    updated_at: datetime
