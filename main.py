"""
Main application entry point
"""
import uvicorn
from app.backend.v1.api import app

if __name__ == "__main__":
    uvicorn.run(
        "app.backend.v1.api:app",
        host="0.0.0.0",
        port=4000,
        reload=True
    )
