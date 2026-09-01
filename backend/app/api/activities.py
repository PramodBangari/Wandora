from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityOut

router = APIRouter(prefix="/api/activities", tags=["activities"])

BENGALURU_LOCATIONS = {
    "Indiranagar": (12.9784, 77.6408),
    "Koramangala": (12.9352, 77.6245),
    "HSR Layout": (12.9116, 77.6474),
    "Whitefield": (12.9698, 77.7500),
    "Bellandur": (12.9304, 77.6784),
    "Marathahalli": (12.9591, 77.6974),
    "Brookfield": (12.9690, 77.7499),
    "Hebbal": (13.0358, 77.5970),
    "MG Road": (12.9756, 77.6066),
    "Jayanagar": (12.9250, 77.5938),
    "JP Nagar": (12.9063, 77.5857),
    "Electronic City": (12.8452, 77.6602),
    "Yelahanka": (13.1007, 77.5963),
    "Rajajinagar": (12.9912, 77.5553),
    "Malleshwaram": (13.0031, 77.5640),
    "BTM Layout": (12.9166, 77.6101),
    "Banashankari": (12.9255, 77.5468),
    "Kalyan Nagar": (13.0221, 77.6403),
    "Kundalahalli": (12.9698, 77.7150),
    "Cubbon Park": (12.9763, 77.5929),
    "Lalbagh": (12.9507, 77.5848),
    "Bangalore Palace": (13.0035, 77.5891),
    "Church Street": (12.9757, 77.6040),
    "Richmond Town": (12.9622, 77.6011),
    "Frazer Town": (12.9987, 77.6190),
    "JP Nagar 7th Phase": (12.9067, 77.5850),
    "Sarjapur Road": (12.9100, 77.6870),
    "Manyata Tech Park": (13.0475, 77.6200),
    "Devanahalli": (13.1986, 77.7066),
}

@router.get("", response_model=list[ActivityOut])
def list_activities(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Activity).order_by(Activity.id.desc())

    if category:
        query = query.filter(Activity.category == category)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Activity.title.ilike(like))
            | (Activity.location_name.ilike(like))
            | (Activity.category.ilike(like))
        )

    return query.all()

@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.post("", response_model=ActivityOut, status_code=201)
def create_activity(payload: ActivityCreate, db: Session = Depends(get_db)):
    coords = BENGALURU_LOCATIONS.get(payload.location_name)

    if not coords:
        raise HTTPException(
            status_code=400,
            detail="Please select a supported Bengaluru location."
        )

    latitude, longitude = coords

    activity = Activity(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location_name=payload.location_name,
        latitude=latitude,
        longitude=longitude,
        start_time=payload.start_time,
        joined=0,
        max_participants=payload.max_participants,
        host=payload.host,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

@router.post("/{activity_id}/join", response_model=ActivityOut)
def join_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if activity.joined >= activity.max_participants:
        raise HTTPException(status_code=409, detail="Activity is full")

    activity.joined += 1
    db.commit()
    db.refresh(activity)
    return activity
