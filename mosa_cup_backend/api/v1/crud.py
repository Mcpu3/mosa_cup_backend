from datetime import datetime
from typing import Optional
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from mosa_cup_backend.api.v1 import models, schemas


def read_user(database: Session, username: str) -> Optional[models.User]:
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

def update_password(database: Session, username: str, password: schemas.Password) -> Optional[models.User]:
    user = read_user(database, username)
    if user:
        hashed_password = CryptContext(["bcrypt"]).hash(password.new_password)
        updated_at = datetime.now()

        user.hashed_password = hashed_password
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def update_display_name(database: Session, username: str, display_name: schemas.DisplayName) -> Optional[models.User]:
    user = read_user(database, username)
    if user:
        updated_at = datetime.now()

        user.display_name = display_name.new_display_name
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def update_line_id(database: Session, username: str, line_id: schemas.LineId) -> Optional[models.User]:
    user = read_user(database, username)
    if user:
        updated_at = datetime.now()

        user.line_id = line_id.new_line_id
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def read_boards(database: Session, username: str) -> list[models.Board]:
    return database.query(models.Board).filter(models.Board.administrater == username).all()

def read_board(database: Session, board_uuid: str) -> models.Board:
    return database.query(models.Board).filter(models.Board.board_uuid == board_uuid).first()

def create_board(database: Session, new_board: schemas.Board) -> models.Board:
    created_at = datetime.now()
    board = models.Board(
        board_id = new_board.board_id,
        board_name = new_board.board_name,
        created_at = created_at
    )
    database.add(board)
    database.commit()
    database.refresh(board)

    return board

def read_subboards(database: Session,board_uuid: str) ->list[models.Subboard]:
    return database.query(models.Subboard).filter(models.Subboard.board_uuid == board_uuid).all()

def read_subboard(database: Session,subboard_uuid: str) -> models.Subboard:
    return database.query(models.Subboard).filter(models.Subboard.subboard_uuid == subboard_uuid).first()

def create_subboard(database: Session,new_subboard: schemas.Subboard) -> models.Subboard:
    created_at = datetime.now()
    subboard = models.Subboard(
        subboard_name = new_subboard.subboard_name,
        created_at = created_at
    )
    database.add(subboard)
    database.commit()
    database.refresh(subboard)

    return subboard
