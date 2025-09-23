import asyncio
from typing import List, Optional, Dict, Any

from app.backend.db import db


async def ensure_author(name: str, bio: Optional[str] = None) -> int:
    async with db.pool.acquire() as conn:  # type: ignore
        row = await conn.fetchrow("SELECT id FROM authors WHERE name = $1", name)
        if row:
            return row["id"]
    return await db.create_author(name=name, bio=bio)


async def ensure_category(name: str) -> int:
    async with db.pool.acquire() as conn:  # type: ignore
        row = await conn.fetchrow("SELECT id FROM categories WHERE name = $1", name)
        if row:
            return row["id"]
    return await db.create_category(name=name)


async def ensure_tag(name: str) -> int:
    async with db.pool.acquire() as conn:  # type: ignore
        row = await conn.fetchrow("SELECT id FROM tags WHERE name = $1", name)
        if row:
            return row["id"]
    return await db.create_tag(name=name)


async def ensure_article(title: str, content: str, author_id: int, category_id: int) -> int:
    async with db.pool.acquire() as conn:  # type: ignore
        row = await conn.fetchrow("SELECT id FROM articles WHERE title = $1", title)
        if row:
            return row["id"]
    return await db.create_article(title=title, content=content, author_id=author_id, category_id=category_id)


async def add_article_tags(article_id: int, tag_ids: List[int]) -> None:
    if not tag_ids:
        return
    async with db.pool.acquire() as conn:  # type: ignore
        for tag_id in tag_ids:
            # UNIQUE(article_id, tag_id) prevents duplicates
            await conn.execute(
                """
                INSERT INTO article_tags (article_id, tag_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                article_id,
                tag_id,
            )


async def seed() -> Dict[str, Any]:
    # Assumes DB is already connected and tables are initialized by the app startup

    # Authors
    author_ids: Dict[str, int] = {}
    for name, bio in [
        ("Saqib", "Full-stack developer and tech writer."),
        ("Alice Johnson", "Backend engineer specializing in Python and FastAPI."),
        ("Bob Smith", "Database enthusiast with a love for PostgreSQL performance."),
    ]:
        author_ids[name] = await ensure_author(name, bio)

    # Categories
    category_ids: Dict[str, int] = {}
    for name in ["Programming", "Databases", "DevOps"]:
        category_ids[name] = await ensure_category(name)

    # Tags
    tag_ids: Dict[str, int] = {}
    for name in ["Python", "FastAPI", "PostgreSQL", "Docker", "AsyncIO"]:
        tag_ids[name] = await ensure_tag(name)

    # Articles (embedded list to avoid import issues when run as module)
    source_articles = [
        {
            "title": "Full stack development",
            "author": "Saqib",
            "category": "Programming",
            "content": (
                "Full stack development combines front-end and back-end expertise to build complete "
                "digital solutions. A full stack developer works with user interfaces, server logic, "
                "and databases, ensuring seamless interaction between all layers. Mastery of frameworks, "
                "APIs, and cloud platforms allows them to deliver scalable, responsive applications."
            ),
            "tags": ["Python", "FastAPI", "Docker"],
        },
        {
            "title": "Mastering PostgreSQL indexing",
            "author": "Bob Smith",
            "category": "Databases",
            "content": (
                "PostgreSQL indexing strategies like B-Tree, GIN, and BRIN can drastically improve "
                "query performance. Learn when to create composite indexes, use partial indexes, and "
                "apply full-text search with GIN to optimize reads without over-indexing."
            ),
            "tags": ["PostgreSQL"],
        },
        {
            "title": "Building fast APIs with FastAPI and AsyncIO",
            "author": "Alice Johnson",
            "category": "Programming",
            "content": (
                "FastAPI leverages Python type hints and AsyncIO to deliver high-performance web services. "
                "Combine async database drivers, background tasks, and validation to build maintainable, "
                "production-ready APIs with excellent developer experience."
            ),
            "tags": ["FastAPI", "AsyncIO", "Python"],
        },
        {
            "title": "Dockerizing your Python app",
            "author": "Saqib",
            "category": "DevOps",
            "content": (
                "Containerizing Python applications with Docker ensures consistent environments across "
                "development and production. Use multi-stage builds, slim base images, and proper caching "
                "to keep images small and deployments fast."
            ),
            "tags": ["Docker", "Python"],
        },
        {
            "title": "AsyncIO patterns for scalable services",
            "author": "Alice Johnson",
            "category": "Programming",
            "content": (
                "Understand event loops, tasks, and synchronization primitives to build scalable async "
                "services. Learn when to apply gather vs. wait and how to avoid deadlocks."
            ),
            "tags": ["AsyncIO", "Python"],
        },
        {
            "title": "Effective schema design in PostgreSQL",
            "author": "Bob Smith",
            "category": "Databases",
            "content": (
                "Normalize for integrity, denormalize for performance. Use constraints, enums, and views "
                "to model complex domains cleanly without sacrificing query speed."
            ),
            "tags": ["PostgreSQL"],
        },
        {
            "title": "Production-ready FastAPI configuration",
            "author": "Saqib",
            "category": "Programming",
            "content": (
                "Structure settings with pydantic, manage dependency injection, and configure logging "
                "to ship robust, maintainable FastAPI applications."
            ),
            "tags": ["FastAPI", "Python"],
        },
        {
            "title": "Optimizing Docker build caching",
            "author": "Saqib",
            "category": "DevOps",
            "content": (
                "Leverage multi-stage builds, order layers wisely, and pin dependencies to speed up "
                "Docker builds and reduce image sizes."
            ),
            "tags": ["Docker"],
        },
        {
            "title": "Connection pooling with async drivers",
            "author": "Alice Johnson",
            "category": "Programming",
            "content": (
                "Use async connection pools to improve throughput. Tune pool sizes and timeouts for "
                "predictable latency under load."
            ),
            "tags": ["AsyncIO", "Python", "PostgreSQL"],
        },
        {
            "title": "Query planning insights in PostgreSQL",
            "author": "Bob Smith",
            "category": "Databases",
            "content": (
                "Read EXPLAIN ANALYZE to understand sequential scans, index usage, and join strategies. "
                "Adjust indexes and rewrite queries for better plans."
            ),
            "tags": ["PostgreSQL"],
        },
    ]

    created_article_ids: List[int] = []
    for art in source_articles:
        author_id = author_ids[art["author"]]
        category_id = category_ids[art["category"]]
        article_id = await ensure_article(
            title=art["title"],
            content=art["content"],
            author_id=author_id,
            category_id=category_id,
        )
        await add_article_tags(article_id, [tag_ids[t] for t in art["tags"]])
        created_article_ids.append(article_id)

    return {
        "authors": author_ids,
        "categories": category_ids,
        "tags": tag_ids,
        "articles": created_article_ids,
    }


if __name__ == "__main__":
    async def _main():
        # Allow running this module directly: connect, init tables, seed, then close
        await db.connect()
        await db.init_tables()
        try:
            result = await seed()
            print("Seed completed:")
            print(result)
        finally:
            await db.close()

    asyncio.run(_main())


