from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = ""
    category: str
    location_name: str
    start_time: str
    max_participants: int = Field(default=10, ge=1, le=500)
    host: str = "Wandora user"


class ActivityOut(ActivityCreate):
    id: int
    joined: int
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
