from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str


class User(BaseModel):
    username: str
    display_name: Optional[str]
    line_id: Optional[str]

    class Config:
        orm_mode = True


class Signup(BaseModel):
    username: str
    password: str


class Password(BaseModel):
    new_password: str


class DisplayName(BaseModel):
    new_display_name: str


class LineId(BaseModel):
    new_line_id: str


class Message(BaseModel):
    message_uuid: str
    board: Optional[Board]
    subboards: Optional[Subboard]
    body: str
    send_time: Optional[datetime]
    scheduled_send_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted: bool
