from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
load_dotenv()

from app.core.database import Base, engine
from app.models.user import User
from app.models.activity import Activity
from app.models.message import Message
from app.models.trip import Trip
from app.api.activities import router as activities_router
from app.api.auth import router as auth_router
from app.api.social import router as social_router

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / 'frontend'
app = FastAPI(title='Wandora API', version='0.7.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
    columns={column[1] for column in connection.execute(text('PRAGMA table_info(activities)'))}
    if 'user_id' not in columns:
        connection.execute(text('ALTER TABLE activities ADD COLUMN user_id INTEGER'))
with engine.begin() as connection:
    columns={column[1] for column in connection.execute(text('PRAGMA table_info(users)'))}
    migrations = {
        'google_sub': 'ALTER TABLE users ADD COLUMN google_sub VARCHAR(255)',
        'email_verified': 'ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0 NOT NULL',
        'verification_code_hash': 'ALTER TABLE users ADD COLUMN verification_code_hash VARCHAR(255)',
        'verification_expires_at': 'ALTER TABLE users ADD COLUMN verification_expires_at DATETIME',
        'reset_code_hash': 'ALTER TABLE users ADD COLUMN reset_code_hash VARCHAR(255)',
        'reset_expires_at': 'ALTER TABLE users ADD COLUMN reset_expires_at DATETIME',
    }
    for name, statement in migrations.items():
        if name not in columns:
            connection.execute(text(statement))
    connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)'))
app.include_router(auth_router)
app.include_router(activities_router)
app.include_router(social_router)
if FRONTEND_DIR.exists():
    app.mount('/', StaticFiles(directory=FRONTEND_DIR, html=True), name='frontend')
