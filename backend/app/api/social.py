from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.activity import Activity
from app.models.message import Message
from app.models.trip import Trip
from app.schemas.social import PersonOut, MessageCreate, MessageOut, TripCreate, TripOut

router = APIRouter(prefix='/api', tags=['social'])

@router.get('/people', response_model=list[PersonOut])
def people(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    query = db.query(User)
    if q:
        like = f'%{q}%'
        query = query.filter((User.username.ilike(like)) | (User.city.ilike(like)) | (User.interests.ilike(like)))
    users = query.order_by(User.id.desc()).all()
    result=[]
    for u in users:
        hosted = db.query(func.count(Activity.id)).filter(Activity.user_id == u.id).scalar() or 0
        result.append(PersonOut(id=u.id, username=u.username, city=u.city or 'Bengaluru', bio=u.bio or '', interests=u.interests or '', avatar_url=u.avatar_url or '', activities_hosted=hosted))
    return result

@router.get('/activities/{activity_id}/messages', response_model=list[MessageOut])
def get_messages(activity_id: int, db: Session = Depends(get_db)):
    if not db.get(Activity, activity_id):
        raise HTTPException(404, 'Activity not found')
    rows = db.query(Message, User).join(User, Message.user_id == User.id).filter(Message.activity_id == activity_id).order_by(Message.id.asc()).all()
    return [MessageOut(id=m.id, activity_id=m.activity_id, user_id=m.user_id, username=u.username, avatar_url=u.avatar_url or '', text=m.text, created_at=m.created_at.isoformat()) for m,u in rows]

@router.post('/messages', response_model=MessageOut, status_code=201)
def send_message(payload: MessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Activity, payload.activity_id):
        raise HTTPException(404, 'Activity not found')
    m=Message(activity_id=payload.activity_id, user_id=user.id, text=payload.text.strip())
    db.add(m); db.commit(); db.refresh(m)
    return MessageOut(id=m.id, activity_id=m.activity_id, user_id=m.user_id, username=user.username, avatar_url=user.avatar_url or '', text=m.text, created_at=m.created_at.isoformat())

@router.get('/trips', response_model=list[TripOut])
def trips(db: Session = Depends(get_db)):
    rows=db.query(Trip, User).join(User, Trip.user_id == User.id).order_by(Trip.id.desc()).all()
    return [TripOut(id=t.id,destination=t.destination,start_date=t.start_date,end_date=t.end_date,description=t.description or '',username=u.username) for t,u in rows]

@router.post('/trips', response_model=TripOut, status_code=201)
def create_trip(payload: TripCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t=Trip(user_id=user.id,destination=payload.destination.strip(),start_date=payload.start_date.strip(),end_date=payload.end_date.strip(),description=payload.description.strip())
    db.add(t); db.commit(); db.refresh(t)
    return TripOut(id=t.id,destination=t.destination,start_date=t.start_date,end_date=t.end_date,description=t.description or '',username=user.username)
