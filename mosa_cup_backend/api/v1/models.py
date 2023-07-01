from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Unicode
from sqlalchemy.orm import relationship

from mosa_cup_backend.api.v1.database import Base


class User(Base):
    __tablename__ = "Users"

    user_uuid = Column(String(48), primary_key=True)
    username = Column(String(48), unique=True, nullable=False)
    hashed_password = Column(Unicode, nullable=False)
    display_name = Column(Unicode, nullable=True)
    line_id = Column(Unicode, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    boards = relationship("Board", back_populates="administrator")
    my_boards = relationship("Board", secondary="BoardMembers", back_populates="members")
    my_subboards = relationship("Subboard", secondary="SubboardMembers", back_populates="members")


class Board(Base):
    __tablename__ = "Boards"

    board_uuid = Column(String(48), primary_key=True)
    board_id = Column(Unicode, nullable=False)
    board_name = Column(Unicode, nullable=False)
    administrator_uuid = Column(String(48), ForeignKey("Users.user_uuid"), nullable=False)
    administrator = relationship("User", back_populates="boards")
    members = relationship("User", secondary="BoardMembers", back_populates="my_boards")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    subboards = relationship("Subboard", back_populates="board")
    received_messages = relationship("Message", back_populates="board")


class BoardMember(Base):
    __tablename__ = "BoardMembers"

    user_uuid = Column(String(48), ForeignKey("Users.user_uuid"), primary_key=True)
    board_uuid = Column(String(48), ForeignKey("Boards.board_uuid"), primary_key=True)


class Subboard(Base):
    __tablename__ = "Subboards"

    subboard_uuid = Column(String(48), primary_key=True)
    subboard_name = Column(Unicode, nullable=False)
    board_uuid = Column(String(48), ForeignKey("Boards.board_uuid"), nullable=False)
    board = relationship("Board", back_populates="subboards")
    members = relationship("User", secondary="SubboardMembers", back_populates="my_subboards")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    received_messages = relationship("Message", secondary="SubboardMessages", back_populates="subboards")


class SubboardMember(Base):
    __tablename__ = "SubboardMembers"

    user_uuid = Column(String(48), ForeignKey("Users.user_uuid"), primary_key=True)
    subboard_uuid = Column(String(48), ForeignKey("Subboards.subboard_uuid"), primary_key=True)


class Message(Base):
    __tablename__ = "Messages"

    message_uuid = Column(String(48), primary_key=True)
    board_uuid = Column(String(48), ForeignKey("Boards.board_uuid"), nullable=True)
    board = relationship("Board", back_populates="received_messages")
    subboards = relationship("Subboard", secondary="SubboardMessages", back_populates="received_messages")
    body = Column(Unicode, nullable=False)
    send_time = Column(DateTime, nullable=True)
    scheduled_send_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class SubboardMessage(Base):
    __tablename__ = "SubboardMessages"

    subboard_uuid = Column(String(48), ForeignKey("Subboards.subboard_uuid"), primary_key=True)
    message_uuid = Column(String(48), ForeignKey("Messages.message_uuid"), primary_key=True)


class DirectMessage(Base):
    __tablename__ = "DirectMessages"

    direct_message_uuid = Column(String(48), primary_key=True)
    send_from_uuid = Column(String(48), ForeignKey("Users.user_uuid"), nullable=False)
    send_from = relationship("User", back_populates="sent_direct_messages")
    send_to_uuid = Column(String(48), ForeignKey("Users.user_uuid"), nullable=False)
    send_to = relationship("User", back_populates="received_direct_messages")
    body = Column(Unicode, nullable=False)
    send_time = Column(DateTime, nullable=True)
    scheduled_send_time = Column(DateTime, nullable=True)
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
