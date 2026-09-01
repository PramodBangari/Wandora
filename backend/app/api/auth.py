from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenOut, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please log in")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired login session")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    username = payload.username.strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if db.query(User).filter(User.username.ilike(username)).first():
        raise HTTPException(status_code=409, detail="Username is already taken")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        city=payload.city.strip() or "Bengaluru",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(user.id), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    username = payload.username.strip()
    existing = db.query(User).filter(User.username.ilike(username), User.id != user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username is already taken")

    user.username = username
    user.bio = payload.bio.strip()
    user.interests = payload.interests.strip()
    user.city = payload.city.strip() or "Bengaluru"
    user.avatar_url = payload.avatar_url.strip()
    db.commit()
    db.refresh(user)
    return user
