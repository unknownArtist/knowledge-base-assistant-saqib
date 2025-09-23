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


# Request/Response models for ask endpoint
class AskRequest(BaseModel):
    question: str
    context_ids: List[int]


class AskResponse(BaseModel):
    answer: str
    context_used: List[ArticleResponse]


# Ask endpoint (LLM question answering)
@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Answer a question using LLM with provided article context"""
    try:
        # Get articles by IDs
        articles = await db.get_articles_by_ids(request.context_ids)
        
        if not articles:
            return AskResponse(
                answer="No relevant context found to answer your question.",
                context_used=[]
            )
        
        # Prioritize articles based on question relevance
        prioritized_articles = await llm_service.prioritize_articles(
            articles, request.question, max_articles=5
        )
        
        # Generate answer using LLM
        answer = await llm_service.answer_question(request.question, prioritized_articles)
        
        return AskResponse(
            answer=answer,
            context_used=prioritized_articles
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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