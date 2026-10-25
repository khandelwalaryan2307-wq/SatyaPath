from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, nullable=False)  # e.g., "R001"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # application category
    severity = Column(String, nullable=False, default="medium")  # low, medium, high
    enabled = Column(Boolean, default=True)
    parameters = Column(JSON, nullable=True)  # rule‑specific parameters
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    findings = relationship("Finding", back_populates="rule")
