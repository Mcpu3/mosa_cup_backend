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

class Board(Base):
    __tablename__ = "Boards"

    board_uuid = Column(String(48),primary_key=True)
    board_id = Column(String,nullable=False)
    board_name = Column(String,nullable=False)
    administrater = Column(String,nullable=False)
    members = Column(String,nullable=False)
    created_at = Column(DateTime,nullable=False)
    updated_at = Column(DateTime,nullable=True)
    deleted = Column(Boolean,default=False,nullable=False)

class Subboard(Base):
    __tablename__ = "Subboards"

    subboard_uuid = Column(String(48),primary_key=True)
    board_uuid = Column(String,nullable=False)
    subboard_name = Column(String,nullable=False)
    members = Column(String,nullable=False)
    created_at = Column(DateTime,nullable=False)
    updated_at = Column(DateTime,nullable=True)
    deleted_at = Column(Boolean,default=False,nullable=False)
