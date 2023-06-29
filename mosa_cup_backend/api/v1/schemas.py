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


class Board(BaseModel):
    board_uuid: str
    board_id: str
    board_name: Optional[str]
    members:Optional[list[User]]

class Subboard(BaseModel):
    subboard_uuid: str
    subboard_name: str
    members: list[str]

