# knowledge-base-assistant-saqib
## Demo video 
This video was recorded at 90% completion, but it is enough to explain the functionality 
```
https://www.loom.com/share/73bf61d634474c7aa39c9a81369a0d65
```
## Getting started

### Prerequisites

- Docker (tested with 24+)
- Docker Compose (v2 plugin)
- Optional for local (non-Docker) runs:
  - Python 3.11+
  - PostgreSQL 14+

### Configuration

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
# Update values as you like
```

Important variables used by the app (see `config/settings.py`):
- `POSTGRES_HOST` (defaults to `db` in Docker)
- `POSTGRES_PORT` (defaults to `5432`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

### Run with Docker Compose (recommended)

```bash
docker compose up --build
```

This will:
- Start PostgreSQL and the API service
- Initialize tables and seed data automatically on API startup

### Start the fronend

```bash
# Navigate to project directory, then to frontend directory, now run this command to install node modules 
npm install  
# Now run this command to run our frontend
npm run dev
# It will start frontend on a specific port e,g http://localhost:5173
```
Services:
- API: http://localhost:4000 (OpenAPI docs at `/docs`)
- Adminer (DB UI): http://localhost:8081
- Frontend: http://localhost:5173

To stop and remove containers and volumes:

```bash
docker compose down -v
```

### Manual reseeding (optional)

Seeding runs automatically on app startup. To trigger manually inside the API container:

```bash
docker compose exec api python -m data.seed_data
```

### Local development without Docker (optional)

1) Start PostgreSQL locally and create a database matching your `.env`.

2) Create a virtual environment and install deps:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

3) Run the API:
```bash
uvicorn app.backend.v1.api:app --reload --host 0.0.0.0 --port 4000
```

The app will connect, initialize tables, and seed data on startup.

## API

- Swagger UI: http://localhost:4000/docs
- Health/root: `GET /`
- Search: `GET /api/v1/search?query=...&limit=5`
- Ask (LLM): `POST /api/v1/ask` with JSON body containing `question` and `context_ids` (list of article IDs)
- Categories: `GET /api/v1/categories` To fetch all categories

## Database schema and indexing

### Tables

```sql
-- authors
CREATE TABLE IF NOT EXISTS authors (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  bio TEXT
);

-- categories
CREATE TABLE IF NOT EXISTS categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

-- tags
CREATE TABLE IF NOT EXISTS tags (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

-- articles
CREATE TABLE IF NOT EXISTS articles (
  id SERIAL PRIMARY KEY,
  author_id INTEGER REFERENCES authors(id),
  category_id INTEGER REFERENCES categories(id),
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- article_tags (many-to-many)
CREATE TABLE IF NOT EXISTS article_tags (
  id SERIAL PRIMARY KEY,
  article_id INTEGER REFERENCES articles(id),
  tag_id INTEGER REFERENCES tags(id),
  UNIQUE(article_id, tag_id)
);
```

### Indexes and why they were chosen

- Full-text search (FTS) on articles title + content (GIN)
  - Index: `articles_fts_idx` on `to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,''))`
  - Why: Enables fast, ranked full-text search over title and content (used by `/api/v1/search`). GIN is optimized for inverted indexes and text search operators.

- Trigram indexes for fuzzy matching of names (GIN with `pg_trgm`)
  - Indexes: `authors_name_trgm_idx`, `categories_name_trgm_idx`, `tags_name_trgm_idx`
  - Why: Supports ILIKE queries and fuzzy search/autocomplete on human names with good performance.

- Composite B-Tree index for category/date queries
  - Index: `articles_category_published_idx` on `(category_id, published_date DESC)`
  - Why: Common pattern is filtering by category and ordering by newest. This index allows index-only scans or minimizes sorting when running queries like:
    ```sql
    SELECT *
    FROM articles
    WHERE category_id = $1
    ORDER BY published_date DESC
    LIMIT 25;
    ```

### Extensions

- `pg_trgm`: enabled to support trigram-based GIN indexes for fuzzy text matching.

### Query patterns improved by the indexes

- Keyword search with relevance ordering:
  ```sql
  WITH ranked AS (
    SELECT a.*, to_tsvector('english', coalesce(a.title,'') || ' ' || coalesce(a.content,'')) AS document,
           to_tsquery('english', $1) AS q
    FROM articles a
  )
  SELECT *, ts_rank(document, q) AS rank
  FROM ranked
  WHERE document @@ q
  ORDER BY rank DESC, published_date DESC
  LIMIT 25;
  ```
  Uses `articles_fts_idx`.

- Category feed ordered by recency:
  ```sql
  SELECT id, title, content, published_date
  FROM articles
  WHERE category_id = $1
  ORDER BY published_date DESC
  LIMIT 25;
  ```
  Uses `articles_category_published_idx`.

- Fuzzy name search (autocomplete):
  ```sql
  SELECT id, name FROM authors WHERE name ILIKE '%ali%' ORDER BY name LIMIT 10;
  ```
  Uses `authors_name_trgm_idx`.

## LLM Integration and Context Management

### Prompt Structure and Context Management

The system uses a sophisticated approach to manage LLM context and prevent token overflow:

1. **Token Estimation**: Uses character-based approximation (4 chars ≈ 1 token) to estimate content size
2. **Context Chunking**: Automatically chunks content into 500-token segments when needed
3. **Article Prioritization**: Selects top 3-5 most relevant articles based on keyword matching
4. **Context Summarization**: If total context exceeds 4K tokens, uses LLM to summarize before answering

**Context Management Flow**:
```python
# 1. Search and get articles (limited to 5 to control context)
articles = await db.search_articles_fts(query, limit=5)

# 2. Prioritize by relevance to question
prioritized = await llm_service.prioritize_articles(articles, question, max_articles=5)

# 3. Check token count and summarize if needed
if estimate_tokens(full_context) > 4000:
    context = await llm_service.summarize_context(articles)

# 4. Generate answer with structured prompt
prompt = f"""Based on this context:
{context}

Question: {question}

Please provide a concise and accurate answer based on the information above."""
```

**Sample Context Structure**:
```
Title: Python Async Programming
Author: John Doe
Category: Programming
Content: [article content...]
Tags: Python, Async, Programming

---

Title: SQL Joins Explained  
Author: Jane Smith
Category: Database
Content: [article content...]
Tags: SQL, Database, Joins
```

### Design Decisions and Challenges Overcome

1. **Full-Text Search vs Simple LIKE**: 
   - **Challenge**: Simple ILIKE queries were slow and lacked relevance ranking
   - **Solution**: Implemented PostgreSQL full-text search with GIN indexes for fast, ranked results
   - **Result**: Sub-100ms search queries with relevance scoring

2. **LLM Context Window Management**:
   - **Challenge**: GPT-3.5-turbo has 4K token limit, but articles could be much larger
   - **Solution**: Multi-tier approach: search filtering → relevance prioritization → summarization
   - **Result**: Never exceed token limits while preserving key information

3. **N+1 Query Problem in Tag Fetching**:
   - **Challenge**: Fetching tags for each article individually was inefficient
   - **Solution**: Used separate queries but optimized with proper indexing
   - **Alternative Considered**: Single complex JOIN, but chose readability over micro-optimization

4. **Async Database Operations**:
   - **Challenge**: Synchronous database calls were blocking the API
   - **Solution**: Full async/await pattern with connection pooling
   - **Result**: Concurrent request handling with 10-connection pool

## Demo Script: Complex Search Examples

### Example 1: Complex Multi-Keyword Search with Category Filter

```bash
# Search for Python async programming articles in the Programming category
curl -X GET "http://localhost:4000/api/v1/search?query=python%20async%20programming&category=Programming&limit=3"

# Response includes articles with:
# - Full-text search ranking
# - Author and category joins
# - Tag associations
# - Relevance scoring
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "title": "Python Async Programming: A Complete Guide",
    "content": "Async programming in Python allows...",
    "author_name": "John Doe",
    "category_name": "Programming", 
    "tags": [{"id": 1, "name": "Python"}, {"id": 2, "name": "Async"}],
    "rank": 0.876543
  }
]
```

### Example 2: LLM Question Answering with Context

```bash
# Ask a complex question using multiple articles as context
curl -X POST "http://localhost:4000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do Python async joins work with database queries?",
    "context_ids": [1, 3, 5]
  }'
```

**Expected LLM Response**:
```
Based on the provided articles about Python async programming and SQL joins:

Python async joins with database queries work through several mechanisms:

1. **Async Database Drivers**: Use asyncpg or aiosqlite for non-blocking database operations
2. **Connection Pooling**: Maintain pools of database connections for concurrent queries  
3. **Awaitable Queries**: Database operations return awaitable objects that yield control during I/O
4. **Join Operations**: SQL joins happen at the database level while Python handles the async orchestration

The key is separating the async coordination (Python) from the join execution (SQL), allowing multiple queries to run concurrently without blocking the event loop.
```
