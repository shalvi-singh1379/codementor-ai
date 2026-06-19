import os
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid

DATABASE_URL = "postgresql://postgres:codementor123@localhost:5432/codementor"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    code_submitted = Column(Text)
    lint_issues_json = Column(Text)  # stored as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    issue_symbol = Column(String, nullable=False)
    issue_type = Column(String, nullable=False)  # error/warning/convention
    occurrence_count = Column(Integer, default=1)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """creates all tables if they don't exist"""
    Base.metadata.create_all(engine)
    print("database tables created successfully")


def get_session():
    """returns a new database session"""
    return SessionLocal()


if __name__ == "__main__":
    init_db()