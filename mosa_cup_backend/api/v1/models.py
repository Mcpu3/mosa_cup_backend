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
