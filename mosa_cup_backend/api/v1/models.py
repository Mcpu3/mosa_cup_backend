from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Unicode
from sqlalchemy.orm import relationship

from mosa_cup_backend.api.v1.database import Base


class User(Base):
    __tablename__ = "Users"

    user_uuid = Column(String(48), primary_key=True)
    username = Column(String(48), unique=True, nullable=False)
    hashed_password = Column(Unicode, nullable=False)
    display_name = Column(Unicode, nullable=True)
    line_id = Column(Unicode, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    boards = relationship("Board", back_populates="administrator")
    my_boards = relationship("Board", secondary="BoardMembers", back_populates="members")
    my_subboards = relationship("Subboard", secondary="SubboardMembers", back_populates="members")


class Board(Base):
    __tablename__ = "Boards"

    board_uuid = Column(String(48), primary_key=True)
    board_id = Column(Unicode, nullable=False)
    board_name = Column(Unicode, nullable=False)
    administrator_uuid = Column(String(48), ForeignKey("Users.user_uuid"), nullable=False)
    administrator = relationship("User", back_populates="boards")
    members = relationship("User", secondary="BoardMembers", back_populates="my_boards")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)

    subboards = relationship("Subboard", back_populates="board")


class BoardMember(Base):
    __tablename__ = "BoardMembers"

    user_uuid = Column(String(48), ForeignKey("Users.user_uuid"), primary_key=True)
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


class SubboardMember(Base):
    __tablename__ = "SubboardMembers"

    user_uuid = Column(String(48), ForeignKey("Users.user_uuid"), primary_key=True)
    subboard_uuid = Column(String(48), ForeignKey("Subboards.subboard_uuid"), primary_key=True)
