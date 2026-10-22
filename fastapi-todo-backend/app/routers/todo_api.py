from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models import todos
from app.schemas.response import ApiResponse
from app.schemas.todo import TodoBase, TodoResponse, TodoUpdate
from app.services import todo_service


router = APIRouter(prefix="/todos", tags=["todos"])




@router.get("/", status_code=status.HTTP_200_OK)
async def get_todos(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[TodoResponse]]:

    todos = await todo_service.get_all_todos(db)

    return ApiResponse(
        status=status.HTTP_200_OK, 
        message="todos gotten successfully",
        data=todos
    )






@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_in: TodoBase,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TodoResponse]:
    new_todo = await todo_service.create_todo(db, todo_in)

    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Todo created successfully",
        data=new_todo,
    )




@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TodoResponse]:
    todo = await todo_service.get_todo_by_id(db, todo_id)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Todo retrieved successfully",
        data=todo,
    )




@router.put("/update/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(
    todo_id: int,
    todo_in: TodoUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TodoResponse]:
    
    todo = await todo_service.update_todo(db, todo_id, todo_in)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Todo updated successfully",
        data=todo,
    )




@router.delete("/delete/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(
    todo_id: int, 
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    await todo_service.delete_todo(db, todo_id)
    
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Todo deleted successfully",
    )