from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, String, DateTime, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

engine = create_engine("sqlite:///c2.db")


class Base(DeclarativeBase):
    pass


class Beacon(Base):
    __tablename__ = "beacons"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    public_key: Mapped[str] = mapped_column(String)
    system_info: Mapped[str] = mapped_column(String)
    registered_at: Mapped[datetime] = mapped_column(DateTime)
    last_active: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="offline")


class Challenge(Base):
    __tablename__ = "challenges"

    challenge_id: Mapped[str] = mapped_column(String, primary_key=True)
    challenge: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)

    beacon_id: Mapped[str] = mapped_column(String)
    public_key: Mapped[str] = mapped_column(String)
    system_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime)

    used: Mapped[bool] = mapped_column(Boolean, default=False)


Base.metadata.create_all(engine)


def get_session():
    return Session(engine)
