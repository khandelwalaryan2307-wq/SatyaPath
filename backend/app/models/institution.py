from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    approved_programmes = Column(JSON, nullable=True)  # list of programme names
    approved_intake = Column(Integer, nullable=True)
    faculty_count = Column(Integer, nullable=True)
    accreditation_status = Column(String, nullable=True)  # e.g., "valid", "expired"
    last_updated = Column(DateTime, default=datetime.utcnow)

    # relationship back to applications (optional)
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")
