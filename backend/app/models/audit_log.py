from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    event_type = Column(String, nullable=False)  # e.g., "application_created", "document_uploaded"
    description = Column(JSON, nullable=True)  # free‑form details
    timestamp = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="audit_logs")
