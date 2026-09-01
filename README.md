# Wandora

Wandora is an early-stage activity discovery MVP. Users can create activities, select a Bengaluru location, view activities on a map, search/filter activities, and join activities.

## Project structure

- `frontend/index.html` - web UI
- `backend/app/` - FastAPI backend
- `backend/requirements.txt` - Python dependencies
- `Dockerfile` - cloud deployment
- `render.yaml` - Render deployment configuration

## Run locally

### Windows PowerShell

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

Open http://127.0.0.1:8000/

API docs: http://127.0.0.1:8000/docs

## GitHub

Create a new GitHub repository and upload/push this folder. Do not commit `.venv`, `.env`, or local database files.

## Cloud deployment

This repository includes a Dockerfile and Render configuration. For an initial public MVP, connect the GitHub repository to Render and deploy it as a Docker web service.

### Important

The current MVP uses SQLite. Many cloud free tiers use ephemeral storage, so database data may be lost after a redeploy/restart. Before real users, migrate the database to PostgreSQL (ideally PostgreSQL + PostGIS) and add authentication, moderation, image storage, notifications, and production security.

## User login and profiles

This version adds:
- Email/password registration and login
- JWT-based login sessions
- User profile with username, city, bio, interests and optional avatar URL
- Activities require a logged-in user to create or join
- New activities automatically use the logged-in user's username as host
- Profile editing and logout

Set `WANDORA_SECRET_KEY` in production. Render generates this automatically from `render.yaml`.
