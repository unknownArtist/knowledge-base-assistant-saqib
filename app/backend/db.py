import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import settings


class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Create database connection pool with simple retry while DB starts up"""
        retries = 10
        last_exc: Optional[Exception] = None
        for _ in range(retries):
            try:
                self.pool = await asyncpg.create_pool(
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT,
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    database=settings.POSTGRES_DB,
                    min_size=1,
                    max_size=10
                )
                return
            except Exception as exc:
                last_exc = exc
                await asyncio.sleep(1.0)
        # If still failing after retries, raise the last exception
        if last_exc:
            raise last_exc
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def init_tables(self):
        """Initialize database tables"""
        async with self.pool.acquire() as conn:
            # Create authors table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS authors (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    bio TEXT
                )
            """)
            
            # Create categories table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """)
            
            # Create tags table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """)
            
            # Create articles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    author_id INTEGER REFERENCES authors(id),
                    category_id INTEGER REFERENCES categories(id),
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create article_tags association table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS article_tags (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER REFERENCES articles(id),
                    tag_id INTEGER REFERENCES tags(id),
                    UNIQUE(article_id, tag_id)
                )
            """)

            # Enable and create full-text search index for performance
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS articles_fts_idx
                ON articles
                USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,'')))
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS authors_name_trgm_idx
                ON authors USING GIN (name gin_trgm_ops)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS categories_name_trgm_idx
                ON categories USING GIN (name gin_trgm_ops)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS tags_name_trgm_idx
                ON tags USING GIN (name gin_trgm_ops)
            """)
            # Composite index to speed up category-filtered queries ordered by published_date
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS articles_category_published_idx
                ON articles (category_id, published_date DESC)
            """)
    
    # Author operations
    async def create_author(self, name: str, bio: Optional[str] = None) -> int:
        """Create a new author"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "INSERT INTO authors (name, bio) VALUES ($1, $2) RETURNING id",
                name, bio
            )
            return result
    
    async def get_author(self, author_id: int) -> Optional[Dict[str, Any]]:
        """Get author by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, bio FROM authors WHERE id = $1",
                author_id
            )
            return dict(row) if row else None
    
    async def get_all_authors(self) -> List[Dict[str, Any]]:
        """Get all authors"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name, bio FROM authors")
            return [dict(row) for row in rows]
    
    # Category operations
    async def create_category(self, name: str) -> int:
        """Create a new category"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "INSERT INTO categories (name) VALUES ($1) RETURNING id",
                name
            )
            return result
    
    async def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name FROM categories WHERE id = $1",
                category_id
            )
            return dict(row) if row else None
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name FROM categories")
            return [dict(row) for row in rows]
    
    # Tag operations
    async def create_tag(self, name: str) -> int:
        """Create a new tag"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "INSERT INTO tags (name) VALUES ($1) RETURNING id",
                name
            )
            return result
    
    async def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """Get tag by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name FROM tags WHERE id = $1",
                tag_id
            )
            return dict(row) if row else None
    
    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name FROM tags")
            return [dict(row) for row in rows]
    
    # Article operations
    async def create_article(self, title: str, content: str, author_id: int, 
                           category_id: int, tag_ids: List[int] = None) -> int:
        """Create a new article"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Create article
                article_id = await conn.fetchval(
                    """INSERT INTO articles (title, content, author_id, category_id) 
                       VALUES ($1, $2, $3, $4) RETURNING id""",
                    title, content, author_id, category_id
                )
                
                # Add tags if provided
                if tag_ids:
                    for tag_id in tag_ids:
                        await conn.execute(
                            "INSERT INTO article_tags (article_id, tag_id) VALUES ($1, $2)",
                            article_id, tag_id
                        )
                
                return article_id
    
    
    async def get_articles_by_ids(self, article_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple articles by their IDs with related data"""
        if not article_ids:
            return []
        
        async with self.pool.acquire() as conn:
            # Create placeholders for the IN clause
            placeholders = ','.join([f'${i+1}' for i in range(len(article_ids))])
            
            articles = await conn.fetch(f"""
                SELECT a.id, a.title, a.content, a.published_date,
                       a.author_id, a.category_id,
                       au.name as author_name, au.bio as author_bio,
                       c.name as category_name
                FROM articles a
                LEFT JOIN authors au ON a.author_id = au.id
                LEFT JOIN categories c ON a.category_id = c.id
                WHERE a.id IN ({placeholders})
                ORDER BY a.published_date DESC
            """, *article_ids)
            
            result = []
            for article in articles:
                article_dict = dict(article)
                
                # Get tags for each article
                tags = await conn.fetch("""
                    SELECT t.id, t.name
                    FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    WHERE at.article_id = $1
                """, article['id'])
                
                article_dict['tags'] = [dict(tag) for tag in tags]
                result.append(article_dict)
            
            return result
    
    
    async def search_articles(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search articles by title or content"""
        async with self.pool.acquire() as conn:
            articles = await conn.fetch("""
                SELECT a.id, a.title, a.content, a.published_date,
                       a.author_id, a.category_id,
                       au.name as author_name, au.bio as author_bio,
                       c.name as category_name
                FROM articles a
                LEFT JOIN authors au ON a.author_id = au.id
                LEFT JOIN categories c ON a.category_id = c.id
                WHERE a.title ILIKE $1 OR a.content ILIKE $1
                ORDER BY a.published_date DESC
                LIMIT $2 OFFSET $3
            """, f"%{query}%", limit, offset)
            
            result = []
            for article in articles:
                article_dict = dict(article)
                
                # Get tags for each article
                tags = await conn.fetch("""
                    SELECT t.id, t.name
                    FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    WHERE at.article_id = $1
                """, article['id'])
                
                article_dict['tags'] = [dict(tag) for tag in tags]
                result.append(article_dict)
            
            return result
    
    
    async def search_articles_fts(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Full-text search with joins and relevance sorting.
        - Joins authors, categories, tags
        - Optional category filter by category name
        - Orders by full-text rank then published_date desc
        - Limits results to avoid overwhelming the LLM
        """
        # Convert simple text into a tsquery AND pattern
        # e.g., "full stack" -> "full & stack"
        ts_query = ' & '.join([part for part in query.strip().split() if part])
        if not ts_query:
            ts_query = query or ''

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH ranked AS (
                    SELECT
                        a.id,
                        a.title,
                        a.content,
                        a.published_date,
                        a.author_id,
                        a.category_id,
                        au.name AS author_name,
                        au.bio AS author_bio,
                        c.name AS category_name,
                        to_tsvector('english', coalesce(a.title,'') || ' ' || coalesce(a.content,'')) AS document,
                        to_tsquery('english', $1) AS q
                    FROM articles a
                    LEFT JOIN authors au ON a.author_id = au.id
                    LEFT JOIN categories c ON a.category_id = c.id
                    WHERE ($2::text IS NULL OR c.name ILIKE $2)
                )
                SELECT
                    r.id,
                    r.title,
                    r.content,
                    r.published_date,
                    r.author_id,
                    r.category_id,
                    r.author_name,
                    r.author_bio,
                    r.category_name,
                    CASE WHEN $1 <> '' THEN ts_rank(r.document, r.q) ELSE 0 END AS rank
                FROM ranked r
                WHERE ($1 = '' OR r.document @@ r.q)
                ORDER BY rank DESC, r.published_date DESC
                LIMIT $3
                """,
                ts_query,
                f"%{category}%" if category else None,
                limit,
            )

            results: List[Dict[str, Any]] = []
            for row in rows:
                article_dict = dict(row)
                # Fetch tags for each article
                tags = await conn.fetch(
                    """
                    SELECT t.id, t.name
                    FROM tags t
                    JOIN article_tags at ON t.id = at.tag_id
                    WHERE at.article_id = $1
                    ORDER BY t.name ASC
                    """,
                    article_dict['id'],
                )
                article_dict['tags'] = [dict(tag) for tag in tags]
                results.append(article_dict)

            return results


# Global database instance
db = Database()


# Database dependency for FastAPI
async def get_db():
    """Database dependency for FastAPI"""
    return db


