from sqlalchemy import (
    Column,
    String,
    TEXT,
    DateTime,
    Integer,
    Enum,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Appointments(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    creator_id = Column(String(255))
    max_participants = Column(Integer, nullable=False)
    status = Column(Enum("VOTING", "CONFIRMED", "CANCELED"), nullable=False)
    invite_link = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.now)

    appointment_dates = relationship(
        "AppointmentDates", back_populates="appointment", cascade="all, delete-orphan"
    )
    participations = relationship(
        "Participations", back_populates="appointment", cascade="all, delete-orphan"
    )


class AppointmentDates(Base):
    __tablename__ = "appointment_dates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    candidate_date = Column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("appointment_id", "candidate_date"),)

    appointment = relationship("Appointments", back_populates="appointment_dates")


class Participations(Base):
    __tablename__ = "participations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False)
    appointment_id = Column(
        Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum("ATTENDING", "NOT_ATTENDING", "MAYBE"), nullable=False, default="ATTENDING"
    )
    available_slots = Column(TEXT)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    appointment = relationship("Appointments", back_populates="participations")
