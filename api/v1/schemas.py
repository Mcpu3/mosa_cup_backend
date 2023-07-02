from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class Token(BaseModel):
    access_token: str


class LINEUser(BaseModel):
    line_user_uuid: str
    user_id: str

    class Config:
        orm_mode = True


class User(BaseModel):
    user_uuid: str
    username: str
    display_name: Optional[str]
    line_user: Optional[LINEUser]

    class Config:
        orm_mode = True


class Signup(BaseModel):
    username: str
    password: str
    line_user_uuid: Optional[str]


class Password(BaseModel):
    new_password: str


class DisplayName(BaseModel):
    new_display_name: str


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
    board: Board
    subboards: List[Subboard]
    body: str
    send_time: Optional[datetime]
    scheduled_send_time: Optional[datetime]

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

    class Config:
        orm_mode = True


class NewDirectMessage(BaseModel):
    send_to_uuids: List[str]
    body: str
    scheduled_send_time: Optional[datetime]


class FormYesNoQuestionResponse(BaseModel):
    form_quetion_response_uuid: str
    form_question_uuid: str
    yes: bool
    no: bool

    class Config:
        orm_mode = True


class FormYesNoQuestion(BaseModel):
    form_question_uuid: str
    title: str
    yes: str
    no: str

    class Config:
        orm_mode = True


class FormResponse(BaseModel):
    form_response_uuid: str
    respondent: User
    form_uuid: str
    form_question_responses: List[FormYesNoQuestionResponse]
    
    class Config:
        orm_mode = True


class Form(BaseModel):
    form_uuid: str
    board: Board
    subboards: List[Subboard]
    title: str
    send_time: Optional[datetime]
    scheduled_send_time: Optional[datetime]
    form_questions: List[FormYesNoQuestion]
    form_responses: List[FormResponse]

    class Config:
        orm_mode = True


class Forms(BaseModel):
    forms: list[Form]

    class Config:
        orm_mode = True


class NewForm(BaseModel):
    subboard_uuids: List[str]
    title: str
    scheduled_send_time: Optional[datetime]
    form_questions: List[FormYesNoQuestion]

    class Config:
        orm_mode = True


class NewMyFormResponse(BaseModel):
    form_question_responses: List[FormYesNoQuestionResponse]
