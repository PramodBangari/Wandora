from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.core.database import Base, engine
from app.models.user import User  # noqa: F401 - registers the model
from app.models.activity import Activity  # noqa: F401 - registers the model
from app.api.activities import router as activities_router
from app.api.auth import router as auth_router

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Wandora API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Small SQLite migration so an existing local MVP database keeps working.
with engine.begin() as connection:
    columns = {column[1] for column in connection.execute(text("PRAGMA table_info(activities)"))}
    if "user_id" not in columns:
        connection.execute(text("ALTER TABLE activities ADD COLUMN user_id INTEGER"))

app.include_router(auth_router)
app.include_router(activities_router)

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
