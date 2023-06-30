from datetime import datetime
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import and_
from sqlalchemy.orm import Session

from mosa_cup_backend.api.v1 import models, schemas


def read_user(database: Session, username: str) -> models.User:
    return database.query(models.User).filter(models.User.username == username).first()

def create_user(database: Session, signup: schemas.Signup) -> models.User:
    hashed_password = CryptContext(["bcrypt"]).hash(signup.password)
    created_at = datetime.now()
    user = models.User(
        username=signup.username,
        hashed_password=hashed_password,
        created_at=created_at
    )
    database.add(user)
    database.commit()
    database.refresh(user)

    return user

def read_board_forms(database: Session,board_uuid: str) -> list[models.Form]:
    return database.query(models.Form).filter(models.Form.board_uuid == board_uuid).all()

def read_subboard_forms(database: Session,board_uuid: str,subboard_uuid: str) ->list[models.Form]:
    return database.query(models.Form).filter(and_(models.Form.board_uuid == board_uuid,models.Form.subboard_uuid == subboard_uuid)).all()

def create_question(database: Session,form_uuid: str,new_question: schemas.FormYesNoQuestion) -> models.FormYesNoQuestion:
    form_question_uuid =str(uuid4())
    created_at = datetime.now()
    question = models.FormYesNoQuestion(
        form_question_uuid = form_question_uuid,
        form_uuid = form_uuid,
        title = new_question.title,
        yes = new_question.yes,
        no = new_question.no,
        created_at = created_at
    )
    database.add(question)
    database.commit()
    database.refresh(question)

    return question


def create_board_form(database: Session,board_uuid: str,new_board_form: schemas.NewForm) -> models.Form:
    form_uuid = str(uuid4())
    created_at = datetime.now()
    board_form = models.Form(
        form_uuid = form_uuid,
        board_uuid = board_uuid,
        title = new_board_form.title,
        created_at = created_at
    )
    database.add(board_form)
    database.commit()
    database.refresh(board_form)

def create_subboard_form(database: Session,board_uuid: str,subboard_uuid: str,new_subboard_form: schemas.NewForm) -> models.Form:
    form_uuid = str(uuid4())
    created_at = datetime.now()
    subboard_form = models.Form(
        form_uuid = form_uuid,
        board_uuid = board_uuid,
        subboard_uuid = subboard_uuid,
        title = new_subboard_form.title,
        created_at = created_at
    )
    database.add(subboard_form)
    database.commit()
    database.refresh(subboard_form)
