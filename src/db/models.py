from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Barber(Base):
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    specialties = Column(String, nullable=False)
    working_days = Column(String, default="mon,tue,wed,thu,fri,sat")
    start_hour = Column(Integer, default=9)
    end_hour = Column(Integer, default=18)
    slot_duration_minutes = Column(Integer, default=30)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    customer_phone = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    cut_type = Column(String, nullable=True)
    status = Column(String, default="confirmed")
    reminder_sent = Column(String, default="false")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("barber_id", "start_time", name="uq_barber_start_time"),)


class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, unique=True, nullable=False)
    preferred_cut = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_phone_number", "phone_number"),)
