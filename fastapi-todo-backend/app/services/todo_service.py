import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import telemetry
from app.models.todos import Todo
from app.schemas.todo import TodoBase, TodoUpdate

logger = logging.getLogger("app.todos")
tracer = telemetry.tracer


async def get_all_todos(db: AsyncSession) -> list[Todo]:
    with tracer.start_as_current_span("todo.list") as span:
        result = await db.execute(select(Todo).order_by(Todo.created_at.desc()))
        todos = list(result.scalars().all())
        span.set_attribute("todo.count", len(todos))
        return todos


async def get_todo_by_id(db: AsyncSession, todo_id: int) -> Todo:
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    todo_data = result.scalar_one_or_none()

    if not todo_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return todo_data


async def create_todo(db: AsyncSession, todo_to_create: TodoBase) -> Todo:
    with tracer.start_as_current_span("todo.create") as span:
        new_todo = Todo(**todo_to_create.model_dump())

        db.add(new_todo)
        await db.commit()
        await db.refresh(new_todo)

        span.set_attribute("todo.id", new_todo.id)
        telemetry.todos_created.add(1)
        logger.info("todo created", extra={"event": "todo.created", "todo_id": new_todo.id})
        return new_todo


async def update_todo(
    db: AsyncSession, todo_id: int, todo_to_update: TodoUpdate
) -> Todo:
    with tracer.start_as_current_span("todo.update") as span:
        span.set_attribute("todo.id", todo_id)
        existing_todo = await get_todo_by_id(db, todo_id=todo_id)
        was_completed = existing_todo.is_completed

        update_data = todo_to_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(existing_todo, key, value)
        await db.commit()
        await db.refresh(existing_todo)

        telemetry.todos_updated.add(1)
        if existing_todo.is_completed and not was_completed:
            telemetry.todos_completed.add(1)
        logger.info(
            "todo updated",
            extra={"event": "todo.updated", "todo_id": todo_id,
                   "is_completed": existing_todo.is_completed},
        )
        return existing_todo


async def delete_todo(db: AsyncSession, todo_id: int) -> None:
    with tracer.start_as_current_span("todo.delete") as span:
        span.set_attribute("todo.id", todo_id)
        todo = await get_todo_by_id(db, todo_id)

        await db.delete(todo)
        await db.commit()

        telemetry.todos_deleted.add(1)
        logger.info("todo deleted", extra={"event": "todo.deleted", "todo_id": todo_id})
