from pydantic import BaseModel, Field

class PersonOut(BaseModel):
    id: int
    username: str
    city: str
    bio: str
    interests: str
    avatar_url: str
    activities_hosted: int = 0

class MessageCreate(BaseModel):
    activity_id: int
    text: str = Field(min_length=1, max_length=1000)

class MessageOut(BaseModel):
    id: int
    activity_id: int
    user_id: int
    username: str
    avatar_url: str
    text: str
    created_at: str

class TripCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=160)
    start_date: str = Field(min_length=2, max_length=40)
    end_date: str = Field(min_length=2, max_length=40)
    description: str = Field(default='', max_length=1000)

class TripOut(BaseModel):
    id: int
    destination: str
    start_date: str
    end_date: str
    description: str
    username: str
