from datetime import datetime
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


class Subboard(BaseModel):
    subboard_uuid: str
    subboard_name: str
    members: List[User]

    class Config:
        orm_mode = True


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
    board: Board
    members: List[User]

    class Config:
        orm_mode = True


class NewBoard(BaseModel):
    board_id: str
    board_name: str


class NewSubboard(BaseModel):
    subboard_name: str


class MyBoard(BaseModel):
    board_uuid: str
    board_id: str
    board_name: str
    administrator: User

    class Config:
        orm_mode = True


class MySubboard(BaseModel):
    subboard_uuid: str
    subboard_name: str

    class Config:
        orm_mode = True


class MyBoardWithSubboards(BaseModel):
    board_uuid: str
    board_id: str
    board_name: str
    administrator: User
    subboards: List[MySubboard]

    class Config:
        orm_mode = True


class MySubboardWithBoard(BaseModel):
    subboard_uuid: str
    subboard_name: str
    board: MyBoard

    class Config:
        orm_mode = True


class NewMyBoards(BaseModel):
    new_my_board_uuids: List[str]


class NewMySubboards(BaseModel):
    new_my_subboard_uuids: List[str]


class Message(BaseModel):
    message_uuid: str
    board: Optional[Board]
    subboards: Optional[List[Subboard]]
    body: str
    send_time: Optional[datetime]
    scheduled_send_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted: bool

    class Config:
        orm_mode = True


class NewMessage(BaseModel):
    subboard_uuids: List[str]
    body: str
    scheduled_send_time: Optional[datetime]


class DirectMessage(BaseModel):
    direct_message_uuid: str
    send_from: User
    send_to: User
    body: str
    send_time: Optional[datetime]
    scheduled_send_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted: bool

    class Config:
        orm_mode = True


class NewDirectMessage(BaseModel):
    send_to_uuids: List[str]
    body: str
    scheduled_send_time: Optional[datetime]
