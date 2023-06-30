from pydantic import BaseModel
from typing import List, Optional


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
    board_name: str
    members: List[User]

    class Config:
        orm_mode = True


class NewBoard(BaseModel):
    board_id: str
    board_name: str


class Subboard(BaseModel):
    subboard_uuid: str
    subboard_name: str
    members: List[User]

    class Config:
        orm_mode = True


class NewSubboard(BaseModel):
    board_uuid: str
    subboard_name: str


class BoardWithSubboards(BaseModel):
    board_uuid: str
    board_id: str
    board_name: str
    members: List[User]
    subboards: List[Subboard]

    class Config:
        orm_mode = True

class SubboardWithBoard(BaseModel):
    subboard_uuid: str
    subboard_name: str
    members: List[User]
    board: Board

    class Config:
        orm_mode = True