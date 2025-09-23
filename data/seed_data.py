import asyncio
import random
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

    def generate_content(min_words: int = 500, max_words: int = 2000) -> str:
        tech_sentences = [
            "Modern distributed systems prioritize observability, tracing, and structured logging to accelerate incident response and root cause analysis.",
            "FastAPI leverages Python type hints to generate OpenAPI schemas and enables high-throughput IO using AsyncIO primitives like tasks and streams.",
            "PostgreSQL offers powerful indexing strategies such as B-Tree, GIN, BRIN, and partial indexes to optimize diverse query workloads.",
            "Container images built with multi-stage Dockerfiles reduce attack surface and improve deployment speed by keeping runtime layers minimal.",
            "Careful schema design balances normalization for integrity with denormalization for read performance and analytics use cases.",
            "Effective pagination avoids OFFSET for large tables, using keyset or cursor-based approaches to deliver consistent latency.",
            "Asynchronous workers offload heavy tasks from request lifecycles, improving P99 latencies and overall system resilience.",
            "Caching strategies must consider invalidation semantics, data freshness requirements, and failure modes to avoid serving stale content.",
            "Background task orchestration benefits from idempotent handlers, deduplication, and exponential backoff for transient failures.",
            "Automated CI pipelines enforce code quality gates, run tests in parallel, and push signed images to registries for traceable releases.",
            "Security practices include secrets management, least-privilege access, SBOM generation, and regular image scanning for vulnerabilities.",
            "Performance tuning starts with profiling and measuring real user metrics before selecting targeted optimizations.",
            "Database migrations should be backward compatible, supporting rolling deployments without downtime via additive changes.",
            "Feature flags enable trunk-based development, progressive delivery, and safe rollbacks by decoupling deploys from releases.",
            "Correctly configured connection pooling protects the database under load while maximizing throughput and minimizing tail latency.",
            "Full-text search with to_tsvector and to_tsquery supports flexible relevance ranking and linguistic normalization in PostgreSQL.",
            "WebSockets and server-sent events allow low-latency updates for collaborative and real-time applications.",
            "Robust error handling distinguishes between retryable and terminal failures to preserve system stability and user trust.",
            "Structured configuration via environment variables and typed settings harmonizes local and production environments.",
            "Comprehensive tests cover unit, integration, and contract layers to detect regressions and ensure API compatibility.",
        ]

        target = random.randint(min_words, max_words)
        words: List[str] = []
        while len(words) < target:
            sentence = random.choice(tech_sentences)
            # Add minor variation
            if random.random() < 0.2:
                sentence += " This pattern reduces operational toil and enhances maintainability."
            if random.random() < 0.15:
                sentence += " Benchmarks should reflect production-like traffic and data distributions."
            words.extend(sentence.split())
        # Trim to target boundary within a small tolerance
        return " ".join(words[:target])

    base_titles = [
        "Designing resilient FastAPI microservices",
        "PostgreSQL indexing deep dive",
        "AsyncIO patterns for production",
        "Observability for Python services",
        "Scaling full-text search with PostgreSQL",
        "Optimizing Docker images for CI",
        "Connection pooling strategies",
        "Reliable background processing",
        "API versioning and compatibility",
        "Secure configuration management",
        "WebSockets at scale",
        "Effective schema evolution",
        "Testing strategies for async code",
        "Cursor-based pagination techniques",
        "Tuning query performance",
        "Streaming large responses",
        "Idempotent endpoint design",
        "Monitoring query hotspots",
        "Graceful shutdown patterns",
        "Dependency injection best practices",
        "Container security essentials",
        "Partitioning strategies for time-series",
        "JSONB patterns and GIN indexes",
        "Task scheduling with AsyncIO",
        "Operational dashboards that matter",
    ]

    authors_cycle = ["Saqib", "Alice Johnson", "Bob Smith"]
    categories_cycle = ["Programming", "Databases", "DevOps"]
    tags_pool = ["Python", "FastAPI", "PostgreSQL", "Docker", "AsyncIO"]

    # Create at least 20 articles; use up to len(base_titles)
    num_articles = max(20, min(25, len(base_titles)))
    source_articles: List[Dict[str, Any]] = []
    for i in range(num_articles):
        title = base_titles[i % len(base_titles)]
        # Ensure uniqueness by appending an index for repeated titles
        if base_titles.count(title) > 1 or i >= len(base_titles):
            title = f"{title} #{i+1}"
        author = authors_cycle[i % len(authors_cycle)]
        category = categories_cycle[i % len(categories_cycle)]
        # Pick 2-3 tags randomly
        tags = random.sample(tags_pool, k=random.randint(2, 3))
        content = generate_content(500, 2000)
        source_articles.append({
            "title": title,
            "author": author,
            "category": category,
            "content": content,
            "tags": tags,
        })

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


