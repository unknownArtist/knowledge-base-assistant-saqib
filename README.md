# knowledge-base-assistant-saqib

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
# Navigate to project directory, then to frontend directory, now run this command 
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