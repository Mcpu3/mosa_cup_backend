from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import and_
from sqlalchemy.orm import Session

from mosa_cup_backend.api.v1 import models, schemas


def read_user(database: Session, user_uuid: Optional[str]=None, username: Optional[str]=None) -> Optional[models.User]:
    user = None
    if user_uuid:
        user = read_user_by_uuid(database, user_uuid)
    if username:
        user = read_user_by_username(database, username)

    return user

def read_user_by_uuid(database: Session, user_uuid: str) -> Optional[models.User]:
    return database.query(models.User).filter(and_(models.User.user_uuid == user_uuid, models.User.deleted == False)).first()

def read_user_by_username(database: Session, username: str) -> Optional[models.User]:
    return database.query(models.User).filter(and_(models.User.username == username, models.User.deleted == False)).first()

def create_user(database: Session, signup: schemas.Signup) -> Optional[models.User]:
    user_uuid = str(uuid4())
    hashed_password = CryptContext(["bcrypt"]).hash(signup.password)
    created_at = datetime.now()
    user = models.User(
        user_uuid=user_uuid,
        username=signup.username,
        hashed_password=hashed_password,
        created_at=created_at
    )
    database.add(user)
    database.commit()
    database.refresh(user)

    return user

def update_password(database: Session, user_uuid: str, password: schemas.Password) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        hashed_password = CryptContext(["bcrypt"]).hash(password.new_password)
        updated_at = datetime.now()

        user.hashed_password = hashed_password
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def update_display_name(database: Session, user_uuid: str, display_name: schemas.DisplayName) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        updated_at = datetime.now()

        user.display_name = display_name.new_display_name
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def update_line_id(database: Session, user_uuid: str, line_id: schemas.LineId) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        updated_at = datetime.now()

        user.line_id = line_id.new_line_id
        user.updated_at = updated_at
        database.commit()
        database.refresh(user)

    return user

def delete_user(database: Session, user_uuid: str) -> Optional[models.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        updated_at = datetime.now()

        user.updated_at = updated_at
        user.deleted = True
        database.commit()
        database.refresh(user)

    return user

def read_boards(database: Session, user_uuid: str) -> List[models.Board]:
    return database.query(models.Board).filter(and_(models.Board.administrator_uuid == user_uuid, models.Board.deleted == False)).all()

def read_board(database: Session, board_uuid: str) -> models.Board:
    return database.query(models.Board).filter(and_(models.Board.board_uuid == board_uuid, models.Board.deleted == False)).first()

def create_board(database: Session, user_uuid: str, new_board: schemas.NewBoard) -> models.Board:
    board_uuid = str(uuid4())
    created_at = datetime.now()
    board = models.Board(
        board_uuid=board_uuid,
        board_id=new_board.board_id,
        board_name=new_board.board_name,
        administrator_uuid=user_uuid,
        created_at=created_at
    )
    database.add(board)
    database.commit()
    database.refresh(board)

    return board

def delete_board(database: Session, board_uuid: str) -> Optional[models.Board]:
    board = read_board(database, board_uuid)
    if board:
        updated_at = datetime.now()
        
        board.updated_at = updated_at
        board.deleted = True
        for subboard in board.subboards:
            subboard.updated_at = updated_at
            subboard.deleted = True
        database.commit()
        database.refresh(board)

    return board

def read_my_boards(database: Session, user_uuid: str) -> List[models.Board]:
    return database.query(models.Board).filter(and_(models.Board.members.any(user_uuid=user_uuid), models.Board.deleted == False)).all()

def update_my_boards(database: Session, user_uuid: str, new_my_boards: schemas.NewMyBoards) -> Optional[schemas.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        user.my_boards.clear()
        for new_my_board_uuid in new_my_boards.new_my_board_uuids:
            board = read_board(database, new_my_board_uuid)
            if board:
                user.my_boards.append(board)
        database.commit()
        database.refresh(user)

    return user

def read_subboards(database: Session, board_uuid: str) -> List[models.Subboard]:
    return database.query(models.Subboard).filter(and_(models.Subboard.board_uuid == board_uuid, models.Subboard.deleted == False)).all()

def read_subboard(database: Session, board_uuid: str, subboard_uuid: str) -> Optional[models.Subboard]:
    return database.query(models.Subboard).filter(and_(models.Subboard.board_uuid == board_uuid, models.Subboard.subboard_uuid == subboard_uuid, models.Subboard.deleted == False)).first()

def create_subboard(database: Session, board_uuid: str, new_subboard: schemas.NewSubboard) -> Optional[models.Subboard]:
    subboard_uuid = str(uuid4())
    created_at = datetime.now()
    subboard = models.Subboard(
        subboard_uuid=subboard_uuid,
        subboard_name=new_subboard.subboard_name,
        board_uuid=board_uuid,
        created_at=created_at
    )
    database.add(subboard)
    database.commit()
    database.refresh(subboard)

    return subboard

def delete_subboard(database: Session, board_uuid: str, subboard_uuid: str) -> Optional[models.Subboard]:
    subboard = read_subboard(database, board_uuid, subboard_uuid)
    if subboard:
        updated_at = datetime.now()
        
        subboard.updated_at = updated_at
        subboard.deleted = True
        database.commit()
        database.refresh(subboard)

    return subboard

def update_my_subboards(database: Session, user_uuid: str, board_uuid: str, new_my_subboards: schemas.NewMySubboards) -> Optional[schemas.User]:
    user = read_user(database, user_uuid=user_uuid)
    if user:
        user.my_subboards = [my_subboard for my_subboard in user.my_subboards if my_subboard.board_uuid != board_uuid]
        for new_my_subboard_uuid in new_my_subboards.new_my_subboard_uuids:
            subboard = read_subboard(database, board_uuid, new_my_subboard_uuid)
            if subboard:
                user.my_subboards.append(subboard)
        database.commit()
        database.refresh(user)

    return user
