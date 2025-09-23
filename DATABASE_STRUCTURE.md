# Database Structure Documentation

## Overview
This project now uses a plain `db.py` file for all database operations instead of SQLAlchemy and Alembic. The database schema and queries are managed directly through asyncpg.

## Database Schema

### Tables Created
1. **authors** - Stores author information
   - id (SERIAL PRIMARY KEY)
   - name (VARCHAR(255) NOT NULL)
   - bio (TEXT)

2. **categories** - Stores article categories
   - id (SERIAL PRIMARY KEY)
   - name (VARCHAR(255) NOT NULL)

3. **tags** - Stores article tags
   - id (SERIAL PRIMARY KEY)
   - name (VARCHAR(255) NOT NULL)

4. **articles** - Stores article content
   - id (SERIAL PRIMARY KEY)
   - author_id (INTEGER REFERENCES authors(id))
   - category_id (INTEGER REFERENCES categories(id))
   - title (VARCHAR(255) NOT NULL)
   - content (TEXT NOT NULL)
   - published_date (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

5. **article_tags** - Many-to-many relationship between articles and tags
   - id (SERIAL PRIMARY KEY)
   - article_id (INTEGER REFERENCES articles(id))
   - tag_id (INTEGER REFERENCES tags(id))
   - UNIQUE(article_id, tag_id)

## API Endpoints

### Articles
- `POST /api/v1/articles` - Create article
- `GET /api/v1/articles` - List articles (with pagination and search)
- `GET /api/v1/articles/{id}` - Get article by ID
- `PUT /api/v1/articles/{id}` - Update article
- `DELETE /api/v1/articles/{id}` - Delete article

### Authors
- `POST /api/v1/authors` - Create author
- `GET /api/v1/authors` - List all authors
- `GET /api/v1/authors/{id}` - Get author by ID

### Categories
- `POST /api/v1/categories` - Create category
- `GET /api/v1/categories` - List all categories
- `GET /api/v1/categories/{id}` - Get category by ID

### Tags
- `POST /api/v1/tags` - Create tag
- `GET /api/v1/tags` - List all tags
- `GET /api/v1/tags/{id}` - Get tag by ID

### Search
- `GET /api/v1/search?query=<term>&category=<optional>&limit=5` - Full-text search over articles joined with authors, categories, and tags. Uses PostgreSQL full-text search and trigram indexes.

### Question Answering
- `POST /api/v1/ask` - Answer questions using LLM with article context. Accepts `{"question": "...", "context_ids": [array of article IDs]}`. Returns structured answer with context used.

## Full-Text Search and Indexing

- We enable the `pg_trgm` extension and add GIN indexes:
  - `articles_fts_idx` on `to_tsvector('english', title || ' ' || content)`
  - Trigram GIN indexes on `authors.name`, `categories.name`, `tags.name`
- Query ranks results by `ts_rank` (relevance) and then `published_date DESC`.
- Optional `category` filter matches `categories.name ILIKE %category%`.
- Limit defaults to 5 to avoid overwhelming downstream LLMs.

Performance note:
- Without indexes, full-text queries on large corpora can be slow (hundreds of ms to seconds).
- With GIN FTS and trigram indexes, typical search latency drops significantly (often to low tens of ms for moderate datasets). Measure using `EXPLAIN ANALYZE` to capture execution time before/after indexing.

This query fetches articles (optionally filtered by category) and performs full-text search on title + content. If a search string is provided, results are ranked by relevance and then by publish date. If no search string is provided, it just shows recent articles.

## Running the Application

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Set environment variables:
   ```bash
   export POSTGRES_USER=your_user
   export POSTGRES_PASSWORD=your_password
   export POSTGRES_DB=your_database
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   ```

3. Run the application:
   ```bash
   python main.py
   ```

]]