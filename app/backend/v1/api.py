from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.backend.v1.endpoints import article
from app.backend.db import db
from data.seed_data import seed


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and create tables"""
    await db.connect()
    await db.init_tables()
    # Seed data on app startup
    try:
        await seed()
    except Exception:
        # Ignore seeding errors to not block startup (e.g., if already seeded)
        pass


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main():
    return {"message": "API is getting ready..."}

app.include_router(article.router)