from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Unicode
from sqlalchemy.orm import relationship

from api.v1.database import Base


class LINEUser(Base):
    __tablename__ = "LINEUsers"

    line_user_uuid = Column(String(48), primary_key=True)
    user_id = Column(String(48), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class User(Base):
    __tablename__ = "Users"

    user_uuid = Column(String(48), primary_key=True)
    user_id = Column(String(48), unique=True, nullable=False)
    username = Column(String(48), unique=True, nullable=False)
    hashed_password = Column(Unicode, nullable=False)
    display_name = Column(Unicode, nullable=True)
    line_user_uuid = Column(String(48), ForeignKey("LINEUsers.line_user_uuid"), nullable=True)
    line_user = relationship("LINEUser")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    boards = relationship("Board", back_populates="administrator")
    my_boards = relationship("Board", secondary="BoardMembers", back_populates="members")
    my_subboards = relationship("Subboard", secondary="SubboardMembers", back_populates="members")
    sent_direct_messages = relationship("DirectMessage", back_populates="send_from", foreign_keys="DirectMessage.send_from_name")
    received_direct_messages = relationship("DirectMessage", back_populates="send_to", foreign_keys="DirectMessage.send_to_name")
    sent_form_responses = relationship("FormResponse", back_populates="respondent")


class Board(Base):
    __tablename__ = "Boards"

    board_uuid = Column(String(48), primary_key=True)
    board_id = Column(String(48), unique=True, nullable=False)
    board_name = Column(Unicode, nullable=False)
    administrator_name = Column(String(48), ForeignKey("Users.username"), nullable=False)
    administrator = relationship("User", back_populates="boards", foreign_keys=[administrator_name])
    members = relationship("User", secondary="BoardMembers", back_populates="my_boards")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    subboards = relationship("Subboard", back_populates="board")
    received_messages = relationship("Message", back_populates="board")
    received_forms = relationship("Form", back_populates="board")


class BoardMember(Base):
    __tablename__ = "BoardMembers"

    username = Column(String(48), ForeignKey("Users.username"), primary_key=True)
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
    received_forms = relationship("Form", secondary="SubboardForms", back_populates="subboards")


class SubboardMember(Base):
    __tablename__ = "SubboardMembers"

    username = Column(String(48), ForeignKey("Users.username"), primary_key=True)
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
    send_from_name = Column(String(48), ForeignKey("Users.username"), nullable=False)
    send_from = relationship("User", back_populates="sent_direct_messages", foreign_keys=[send_from_name])
    send_to_name = Column(String(48), ForeignKey("Users.username"), nullable=False)
    send_to = relationship("User", back_populates="received_direct_messages", foreign_keys=[send_to_name])
    body = Column(Unicode, nullable=False)
    send_time = Column(DateTime, nullable=True)
    scheduled_send_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class Form(Base):
    __tablename__ = "Forms"

    form_uuid = Column(String(48), primary_key=True)
    board_uuid = Column(String(48), ForeignKey("Boards.board_uuid"), nullable=True)
    board = relationship("Board", back_populates="received_forms")
    subboards = relationship("Subboard", secondary="SubboardForms", back_populates="received_forms")
    title = Column(Unicode, nullable=False)
    send_time = Column(DateTime, nullable=True)
    scheduled_send_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    form_questions = relationship("FormYesNoQuestion", back_populates="form")
    form_responses = relationship("FormResponse", back_populates="form")


class FormYesNoQuestion(Base):
    __tablename__ = "FormYesNoQuestions"

    form_question_uuid = Column(String(48), primary_key=True)
    form_uuid = Column(String(48), ForeignKey("Forms.form_uuid"), nullable=False)
    form = relationship("Form", back_populates="form_questions")
    title = Column(Unicode, nullable=False)
    yes = Column(Unicode, nullable=False)
    no = Column(Unicode, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at =Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    form_question_responses = relationship("FormYesNoQuestionResponse", back_populates="form_question")


class SubboardForm(Base):
    __tablename__ = "SubboardForms"

    subboard_uuid = Column(String(48), ForeignKey("Subboards.subboard_uuid"), primary_key=True)
    form_uuid = Column(String(48), ForeignKey("Forms.form_uuid"), primary_key=True)


class FormResponse(Base):
    __tablename__ = "FormResponses"

    form_response_uuid = Column(String(48), primary_key=True)
    respondent_name = Column(String(48), ForeignKey("Users.username"), nullable=False)
    respondent = relationship("User", back_populates="sent_form_responses")
    form_uuid = Column(String(48), ForeignKey("Forms.form_uuid"), nullable=False)
    form = relationship("Form", back_populates="form_responses")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    form_question_responses = relationship("FormYesNoQuestionResponse", back_populates="form_response")


class FormYesNoQuestionResponse(Base):
    __tablename__ = "FormYesNoQuestionResponses"

    form_question_response_uuid = Column(String(48), primary_key=True)
    form_response_uuid = Column(String(48), ForeignKey("FormResponses.form_response_uuid"), nullable=False)
    form_response = relationship("FormResponse", back_populates="form_question_responses")
    form_question_uuid = Column(String(48), ForeignKey("FormYesNoQuestions.form_question_uuid"), nullable=False)
    form_question = relationship("FormYesNoQuestion", back_populates="form_question_responses")
    yes = Column(Boolean, nullable=False)
    no = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
