import json

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Unicode

from mosa_cup_backend.api.v1.database import Base


class User(Base):
    __tablename__ = "Users"

    username = Column(String(48), primary_key=True)
    hashed_password = Column(Unicode, nullable=False)
    display_name = Column(Unicode, nullable=True)
    line_id = Column(Unicode, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class Board(Base):
    __tablename__ = "Boards"

    board_uuid = Column(String(48), primary_key=True)
    administrator = Column(String(48), ForeignKey("Users.username"), nullable=False)
    board_id = Column(Unicode, nullable=False)
    board_name = Column(Unicode, nullable=False)
    members = Column(Unicode, default=json.dumps([]), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)


class Subboard(Base):
    __tablename__ = "Subboards"

    subboard_uuid = Column(String(48), primary_key=True)
    board_uuid = Column(String(48), ForeignKey("Boards.board_uuid"), nullable=False)
    subboard_name = Column(Unicode, nullable=False)
    members = Column(Unicode, default=json.dumps([]), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
