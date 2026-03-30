from datetime import datetime
from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    keyword: str
    max_pages: int = 3


class ActivityResponse(BaseModel):
    id: int
    title: str
    url: str | None = None
    price: float | None = None
    currency: str | None = None
    rating: float | None = None
    review_count: int | None = None
    supplier: str | None = None
    duration: str | None = None
    description: str | None = None
    highlights: list[str] | None = None
    includes: list[str] | None = None
    excludes: list[str] | None = None
    cancellation_policy: str | None = None
    image_url: str | None = None

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: int
    keyword: str
    status: TaskStatus
    max_pages: int
    progress: int
    error: str | None = None
    report_markdown: str | None = None
    report_html: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    activities: list[ActivityResponse] = []

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    id: int
    keyword: str
    status: TaskStatus
    progress: int
    activity_count: int = 0
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
