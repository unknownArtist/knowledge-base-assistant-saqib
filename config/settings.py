from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    
    PROJECT_NAME: str = os.environ.get('PROJECT_NAME', 'Knowledge Base Assistant')
    BACKEND_CORS_ORIGINS: str = os.environ.get('BACKEND_CORS_ORIGINS', '*')

    # database
    POSTGRES_USER: str = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.environ.get('POSTGRES_PASSWORD', 'password')
    POSTGRES_DB: str = os.environ.get('POSTGRES_DB', 'knowledge_base')
    POSTGRES_HOST: str = os.environ.get('POSTGRES_HOST', 'db')
    POSTGRES_PORT: int = int(os.environ.get('POSTGRES_PORT', '5432'))
    

    
settings = Settings()
        
        

        
     