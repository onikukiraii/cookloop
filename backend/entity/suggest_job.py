from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from entity.base import Base


class SuggestJob(Base):
    __tablename__ = "suggest_job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(20), nullable=False, default="pending")
    params_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
