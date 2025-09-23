from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.backend.db import db


router = APIRouter(tags=["Categories"], prefix="/api/v1")


class CategoryResponse(BaseModel):
    id: int
    name: str


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories() -> List[CategoryResponse]:
    try:
        categories = await db.get_all_categories()
        return [CategoryResponse(**c) for c in categories]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


