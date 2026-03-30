import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, async_session
from app.models.task import Task, Activity, TaskStatus
from app.schemas.task import TaskCreate, TaskResponse, TaskListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


async def run_task(task_id: int):
    from app.scraper.gyg import scrape_keyword
    from app.analyzer.gemini import analyze_activities

    async with async_session() as db:
        task = await db.get(Task, task_id)
        if not task:
            return

        try:
            task.status = TaskStatus.SCRAPING
            await db.commit()

            activities = await scrape_keyword(
                task.keyword, task.max_pages, task_id, db
            )

            task.status = TaskStatus.ANALYZING
            task.progress = 80
            await db.commit()

            report_md, report_html = await analyze_activities(
                task.keyword, activities
            )

            task.report_markdown = report_md
            task.report_html = report_html
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            logger.exception(f"Task {task_id} failed")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await db.commit()


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task = Task(keyword=body.keyword, max_pages=body.max_pages)
    db.add(task)
    await db.commit()

    result = await db.execute(
        select(Task).where(Task.id == task.id).options(selectinload(Task.activities))
    )
    task = result.scalar_one()

    background_tasks.add_task(run_task, task.id)
    return task


@router.get("/tasks", response_model=list[TaskListResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Task,
            func.count(Activity.id).label("activity_count"),
        )
        .outerjoin(Activity)
        .group_by(Task.id)
        .order_by(Task.created_at.desc())
    )
    tasks = []
    for row in result.all():
        t = row[0]
        tasks.append(
            TaskListResponse(
                id=t.id,
                keyword=t.keyword,
                status=t.status,
                progress=t.progress,
                activity_count=row[1],
                created_at=t.created_at,
                completed_at=t.completed_at,
            )
        )
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.id == task_id).options(selectinload(Task.activities))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"ok": True}


@router.get("/tasks/{task_id}/export")
async def export_pdf(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.report_html:
        raise HTTPException(status_code=400, detail="Report not ready")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(task.report_html, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
            print_background=True,
        )
        await browser.close()

    filename = f"gyg-scout-{task.keyword.replace(' ', '-')}-{task_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
