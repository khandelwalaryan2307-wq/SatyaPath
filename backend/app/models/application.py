from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String, unique=True, nullable=False)
    institution_name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    category = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, under_review, completed, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="application", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")
