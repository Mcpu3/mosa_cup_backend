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

class FormYesNoQuestion(BaseModel):
    form_question_uuid: str
    title: str
    type: str
    yes: str
    no: str

class FormYesNoQuestionResponses(BaseModel):
    form_question_response_uuid: str
    form_question_uuid: str
    yes: bool
    no: bool


class Response(BaseModel):
    form_response_uuid: str
    respondent: list[User]
    question_responses: list[FormYesNoQuestionResponses]

    class Config:
        orm_mode = True

class Form(BaseModel):
    form_uuid: str
    title: str
    questions: list[FormYesNoQuestion]
    respnses: list[Response]

    class Config:
        orm_mode = True

class Forms(BaseModel):
    forms: list[Form]

    class Config:
        orm_mode = True

class NewForm(BaseModel):
    title: str
    questions: list[FormYesNoQuestion]

    class Config:
        orm_mode = True
