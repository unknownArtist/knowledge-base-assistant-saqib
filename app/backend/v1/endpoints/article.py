from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.backend.db import db
from app.backend.schemas.article import (
    ArticleBase, ArticleResponse, ArticleListResponse,
    TagResponse
)
from app.backend.services.llm_service import llm_service

router = APIRouter(tags=["Articles"], prefix="/api/v1")





# Search endpoint (full-text search with joins)
@router.get("/search", response_model=List[ArticleResponse])
async def search_articles(
    query: str = Query(..., min_length=1, description="Search term"),
    category: Optional[str] = Query(None, description="Optional category name filter"),
    limit: int = Query(5, ge=1, le=25, description="Max results; capped to protect LLM context")
):
    try:
        results = await db.search_articles_fts(query=query, category=category, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))