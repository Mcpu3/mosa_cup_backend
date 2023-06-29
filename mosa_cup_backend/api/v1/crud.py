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
