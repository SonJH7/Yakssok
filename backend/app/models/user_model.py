from sqlalchemy import Column, String, TEXT, DateTime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    google_refresh_token = Column(TEXT, nullable=False)
    created_at = Column(DateTime, nullable=False)
