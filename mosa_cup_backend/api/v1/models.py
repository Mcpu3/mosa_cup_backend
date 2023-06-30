from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from mosa_cup_backend.api.v1.database import Base


class User(Base):
    __tablename__ = "Users"

    username = Column(String(48), primary_key=True)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    line_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

class Form(Base):
    __tablename__ = "Forms"

    form_uuid = Column(String(48),primary_key=True)
    board_uuid  = Column(String,nullable=False)
    subboard_uuid = Column(String,nullable=False)
    title = Column(String,nullable=False)
    send_time = Column(DateTime,nullable=False)
    scheduled_sending_time = Column(DateTime,nullable=True)
    created_at = Column(DateTime,nullable=False)
    updated_at = Column(DateTime,nullable=True)
    deleted = Column(Boolean,default=False,nullable=False)

class FormYesNoQuestion(Base):
    __tablename__ = "FormYesNoQuestions"

    form_question_uuid = Column(String(48),primary_key=True)
    form_uuid = Column(String,nullable=False)
    title = Column(String,nullable=False)
    yes = Column(String,nullable=True)
    no = Column(String,nullable=True)
    created_at = Column(DateTime,nullable=False)
    updated_at =Column(DateTime,nullable=True)
    deleted = Column(Boolean,default=False,nullable=False)

class FormResponse(Base):
    __tablename__ = "FormResponses"

    form_response_uuid = Column(String(48),primary_key=True)
    form_uuid = Column(String,nullable=False)
    user_uuid = Column(String,nullable=False)
    created_at = Column(DateTime,nullable=False)
    updated_at = Column(DateTime,nullable=True)
    deleted = Column(Boolean,default=False,nullable=False)

class FormYesNoQuestionResponses(Base):
    __tablename__ = "FormYesNoQuestionResponses"

    form_question_response_uuid = Column(String(48),primary_key=True)
    form_response_uuid = Column(String,nullable=False)
    form_question_uuid = Column(String,nullable=False)
    yes = Column(Boolean,nullable=True)
    no = Column(Boolean,nullable=True)
    created_at = Column(DateTime,nullable=False)
    updated_At = Column(DateTime,nullable=True)
    deleted = Column(Boolean,default=False,nullable=False)
