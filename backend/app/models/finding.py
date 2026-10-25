from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high
    status = Column(String, default="pending")  # pending, confirmed, false_positive, resolved
    description = Column(String, nullable=False)
    evidence = Column(JSON, nullable=True)  # list of evidential items (doc names, field values)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="findings")
    rule = relationship("Rule", back_populates="findings")
