import os

files = {
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: argus
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/argus
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=change-me-in-production
      - ENVIRONMENT=development
    depends_on:
      - db
      - redis

  worker:
    build:
      context: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/argus
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=change-me-in-production
      - ENVIRONMENT=development
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
""",
    ".env.example": """DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/argus
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
""",
    "README.md": "# Argus Sentinel\n\nAI-Powered Cybersecurity Reasoning Engine.\n",
    "backend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]
""",
    "backend/requirements.txt": """fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic-settings
celery[redis]
redis
httpx
python-dotenv
psycopg2-binary
""",
    "backend/start.sh": """#!/bin/sh

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
""",
    "backend/alembic.ini": """[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@db:5432/argus

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "backend/alembic/env.py": """import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",
    "backend/alembic/versions/.gitkeep": "",
    "backend/app/__init__.py": "",
    "backend/app/main.py": """from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="Argus Sentinel API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Argus Sentinel"}
""",
    "backend/app/config.py": """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/argus"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
""",
    "backend/app/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
""",
    "backend/app/models/__init__.py": "",
    "backend/app/schemas/__init__.py": "",
    "backend/app/routers/__init__.py": "",
    "backend/app/engines/__init__.py": "",
    "backend/app/intelligence/__init__.py": "",
    "backend/app/tasks/__init__.py": """from celery import Celery
from app.config import settings

celery_app = Celery('worker', broker=settings.REDIS_URL, backend=settings.REDIS_URL)
""",
    "frontend/Dockerfile": """FROM node:18-alpine
WORKDIR /app
COPY package.json vite.config.js ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
""",
    "frontend/package.json": """{
  "name": "argus-sentinel-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.1",
    "vite": "^5.0.8"
  }
}""",
    "frontend/vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  }
})
""",
    "frontend/index.html": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Argus Sentinel</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
    "frontend/src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
    "frontend/src/App.jsx": """import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...')
  const [isOnline, setIsOnline] = useState(false)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setApiStatus('API Online')
          setIsOnline(true)
        }
      })
      .catch(() => {
        setApiStatus('API Offline')
        setIsOnline(false)
      })
  }, [])

  return (
    <div style={{ backgroundColor: '#0a0f1a', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
      <h1 style={{ color: 'white', fontSize: '3rem', margin: '0 0 10px 0' }}>Argus Sentinel</h1>
      <p style={{ color: 'gray', fontSize: '1.2rem', marginBottom: '30px' }}>AI-Powered Cybersecurity Reasoning Engine</p>
      
      <div style={{
        padding: '8px 16px',
        borderRadius: '20px',
        backgroundColor: isOnline ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
        color: isOnline ? '#22c55e' : '#ef4444',
        fontWeight: 'bold'
      }}>
        {apiStatus}
      </div>
    </div>
  )
}

export default App
""",
    "frontend/src/index.css": """body {
  margin: 0;
  padding: 0;
}
""",
    "argus-intelligence/services/.gitkeep": "",
    "argus-intelligence/technologies/.gitkeep": "",
    "argus-intelligence/vulnerabilities/.gitkeep": ""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Scaffolding complete.")
