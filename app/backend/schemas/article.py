from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TagBase(BaseModel):
    name: str


class TagResponse(TagBase):
    id: int


class ArticleBase(BaseModel):
    title: str
    content: str


class ArticleResponse(ArticleBase):
    id: int
    published_date: datetime
    author_name: str
    category_name: Optional[str] = None
    tags: List[TagResponse] = []


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int
    limit: int


# Request/Response models for ask endpoint
class AskRequest(BaseModel):
    question: str
    context_ids: List[int]


class AskResponse(BaseModel):
    answer: str
    context_used: List[ArticleResponse]