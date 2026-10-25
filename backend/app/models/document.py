from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    category = Column(String, nullable=False)  # e.g., "Application Form", "Accreditation Certificate"
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)  # absolute path on server
    file_hash = Column(String, nullable=False)  # SHA-256 for duplicate detection
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    extraction_status = Column(String, default="pending")  # pending, success, failed
    extracted_data = Column(JSON, nullable=True)  # key/value pairs extracted via OCR / manual entry

    application = relationship("Application", back_populates="documents")
