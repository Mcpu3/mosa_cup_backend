import os
import urllib.parse

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_CONNECTION_STRING = urllib.parse.quote_plus("Driver={ODBC Driver 17 for SQL Server};Server=tcp:mosa-cup-backend.database.windows.net,1433;Database=mosa_cup_backend;Uid=mosa_cup_backend;Pwd={%s};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" % DATABASE_PASSWORD)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={DATABASE_CONNECTION_STRING}"
database = SQLAlchemy(app)
migrate = Migrate(app, database)


class User(database.Model):
    __tablename__ = "Users"

    user_uuid = database.Column(database.String(48), primary_key=True)
    username = database.Column(database.String(48), unique=True, nullable=False)
    hashed_password = database.Column(database.Unicode, nullable=False)
    display_name = database.Column(database.Unicode, nullable=True)
    line_id = database.Column(database.Unicode, nullable=True)
    created_at = database.Column(database.DateTime, nullable=False)
    updated_at = database.Column(database.DateTime, nullable=True)
    deleted = database.Column(database.Boolean, default=False, nullable=False)

    boards = database.relationship("Board", back_populates="administrator")
    my_boards = database.relationship("Board", secondary="BoardMembers", back_populates="members")
    my_subboards = database.relationship("Subboard", secondary="SubboardMembers", back_populates="members")


class Board(database.Model):
    __tablename__ = "Boards"

    board_uuid = database.Column(database.String(48), primary_key=True)
    board_id = database.Column(database.Unicode, nullable=False)
    board_name = database.Column(database.Unicode, nullable=False)
    administrator_uuid = database.Column(database.String(48), database.ForeignKey("Users.user_uuid"), nullable=False)
    administrator = database.relationship("User", back_populates="boards")
    members = database.relationship("User", secondary="BoardMembers", back_populates="my_boards")
    created_at = database.Column(database.DateTime, nullable=False)
    updated_at = database.Column(database.DateTime, nullable=True)
    deleted = database.Column(database.Boolean, default=False, nullable=False)

    subboards = database.relationship("Subboard", back_populates="board")
    received_messages = database.relationship("Message", back_populates="board")


class BoardMember(database.Model):
    __tablename__ = "BoardMembers"

    user_uuid = database.Column(database.String(48), database.ForeignKey("Users.user_uuid"), primary_key=True)
    board_uuid = database.Column(database.String(48), database.ForeignKey("Boards.board_uuid"), primary_key=True)


class Subboard(database.Model):
    __tablename__ = "Subboards"

    subboard_uuid = database.Column(database.String(48), primary_key=True)
    subboard_name = database.Column(database.Unicode, nullable=False)
    board_uuid = database.Column(database.String(48), database.ForeignKey("Boards.board_uuid"), nullable=False)
    members = database.relationship("User", secondary="SubboardMembers", back_populates="my_subboards")
    created_at = database.Column(database.DateTime, nullable=False)
    updated_at = database.Column(database.DateTime, nullable=True)
    deleted = database.Column(database.Boolean, default=False, nullable=False)

    received_messages = database.relationship("Message", secondary="SubboardMessages", back_populates="subboards")


class SubboardMember(database.Model):
    __tablename__ = "SubboardMembers"

    user_uuid = database.Column(database.String(48), database.ForeignKey("Users.user_uuid"), primary_key=True)
    subboard_uuid = database.Column(database.String(48), database.ForeignKey("Subboards.subboard_uuid"), primary_key=True)


class Message(database.Model):
    __tablename__ = "Messages"

    message_uuid = database.Column(database.String(48), primary_key=True)
    board_uuid = database.Column(database.String(48), database.ForeignKey("Boards.board_uuid"), nullable=True)
    board = database.relationship("Board", back_populates="received_messages")
    subboards = database.relationship("Subboard", secondary="SubboardMessages", back_populates="received_messages")
    body = database.Column(database.String, nullable=False)
    send_time = database.Column(database.DateTime, nullable=True)
    scheduled_send_time = database.Column(database.DateTime, nullable=True)
    created_at = database.Column(database.DateTime, nullable=False)
    updated_at = database.Column(database.DateTime, nullable=True)
    deleted = database.Column(database.Boolean, default=False, nullable=False)


class SubboardMessage(database.Model):
    __tablename__ = "SubboardMessages"

    subboard_uuid = database.Column(database.String(48), database.ForeignKey("Subboards.subboard_uuid"), primary_key=True)
    message_uuid = database.Column(database.String(48), database.ForeignKey("Messages.message_uuid"), primary_key=True)


class DirectMessage(database.Model):
    __tablename__ = "DirectMessages"

    direct_message_uuid = database.Column(database.String(48), primary_key=True)
    send_from_uuid = database.Column(database.String(48), database.ForeignKey("Users.user_uuid"), nullable=False)
    send_from = database.relationship("User", back_populates="sent_direct_messages")
    send_to_uuid = database.Column(database.String(48), database.ForeignKey("Users.user_uuid"), nullable=False)
    send_to = database.relationship("User", back_populates="received_direct_messages")
    body = database.Column(database.Unicode, nullable=False)
    send_time = database.Column(database.DateTime, nullable=True)
    scheduled_send_time = database.Column(database.DateTime, nullable=True)
    created_at = database.Column(database.DateTime, nullable=False)
    updated_at = database.Column(database.DateTime, nullable=True)
    deleted = database.Column(database.Boolean, default=False, nullable=False)

class Form(database.Model):
    __tablename__ = "Forms"

    form_uuid = database.Column(database.String(48),primary_key=True)
    board_uuid  = database.Column(database.String,nullable=False)
    subboard_uuid = database.Column(database.String,nullable=False)
    title = database.Column(database.String,nullable=False)
    send_time = database.Column(database.DateTime,nullable=False)
    scheduled_sending_time = database.Column(database.DateTime,nullable=True)
    created_at = database.Column(database.DateTime,nullable=False)
    updated_at = database.Column(database.DateTime,nullable=True)
    deleted = database.Column(database.Boolean,default=False,nullable=False)

class FormYesNoQuestion(database.Model):
    __tablename__ = "FormYesNoQuestions"

    form_question_uuid = database.Column(database.String(48),primary_key=True)
    form_uuid = database.Column(database.String,nullable=False)
    title = database.Column(database.String,nullable=False)
    yes = database.Column(database.String,nullable=True)
    no = database.Column(database.String,nullable=True)
    created_at = database.Column(database.DateTime,nullable=False)
    updated_at = database.Column(database.DateTime,nullable=True)
    deleted = database.Column(database.Boolean,default=False,nullable=False)

class FormResponse(database.Model):
    __tablename__ = "FormResponses"

    form_response_uuid = database.Column(database.String(48),primary_key=True)
    form_uuid = database.Column(database.String,nullable=False)
    user_uuid = database.Column(database.String,nullable=False)
    created_at = database.Column(database.DateTime,nullable=False)
    updated_at = database.Column(database.DateTime,nullable=True)
    deleted = database.Column(database.Boolean,default=False,nullable=False)

class FormYesNoQuestionResponses(database.Model):
    __tablename__ = "FormYesNoQuestionResponses"

    form_question_response_uuid = database.Column(database.String(48),primary_key=True)
    form_response_uuid = database.Column(database.String,nullable=False)
    form_question_uuid = database.Column(database.String,nullable=False)
    yes = database.Column(database.Boolean,nullable=True)
    no = database.Column(database.Boolean,nullable=True)
    created_at = database.Column(database.DateTime,nullable=False)
    updated_At = database.Column(database.DateTime,nullable=True)
    deleted = database.Column(database.Boolean,default=False,nullable=True)