import os
import urllib.parse

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_CONNECTION_STRING = urllib.parse.quote_plus("Driver={ODBC Driver 18 for SQL Server};Server=tcp:mosa-cup-backend.database.windows.net,1433;Database=mosa_cup_backend;Uid=mosa_cup_backend;Pwd={%s};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" % DATABASE_PASSWORD)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={DATABASE_CONNECTION_STRING}"
database = SQLAlchemy(app)
migrate = Migrate(app, database)


class User(database.Model):
    __tablename__ = "Users"

    username = database.Column(database.String(48), primary_key=True)
    hashed_password = database.Column(database.String, nullable=False)
    display_name = database.Column(database.String, nullable=True)
    line_id = database.Column(database.String, nullable=True)
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
    yes = database.Column(database.Boolean,nullable=False)
    no = database.Column(database.Boolean,nullable=False)
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
    yes = database.Column(database.Boolean,nullable=False)
    no = database.Column(database.Boolean,nullable=False)
    created_at = database.Column(database.DateTime,nullable=False)
    updated_At = database.Column(database.DateTime,nullable=True)
    deleted = database.Column(database.Boolean,default=False,nullable=False)