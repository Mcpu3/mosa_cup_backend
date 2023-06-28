from datetime import datetime
from uuid import uuid4

from passlib.context import CryptContext
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
