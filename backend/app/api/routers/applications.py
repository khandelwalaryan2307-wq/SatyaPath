import hashlib
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import settings
from ...dependencies import get_db
from ...models.application import Application
from ...models.audit_log import AuditLog
from ...models.document import Document
from ...models.finding import Finding
from ...models.institution import Institution

router = APIRouter()
ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class ApplicationCreate(BaseModel):
    reference_number: str = Field(min_length=4, max_length=64)
    institution_code: str
    category: str = "Extension of Approval"
    academic_year: str = "2026-27"


class ReviewUpdate(BaseModel):
    status: str
    note: str = ""
    reviewer: str = "Demo reviewer"


@router.get("/")
async def list_applications(db: Session = Depends(get_db)):
    from .dashboard import application_summary
    items = db.query(Application).order_by(Application.updated_at.desc()).all()
    return [application_summary(item) for item in items]


@router.get("/evidence")
async def list_evidence(db: Session = Depends(get_db)):
    findings = db.query(Finding).order_by(Finding.created_at.desc()).all()
    return [{"id": f.id, "application_id": f.application_id,
        "reference_number": f.application.reference_number,
        "institution_name": f.application.institution.name,
        "field": f.rule.name if f.rule else "Review finding", "description": f.description,
        "severity": f.severity, "rule_id": f.rule.rule_id if f.rule else "",
        "status": f.status, "evidence": f.evidence or {},
        "created_at": f.created_at.isoformat() if f.created_at else None} for f in findings]


@router.post("/evidence/{finding_id}/review")
async def review_evidence(finding_id: int, payload: dict, db: Session = Depends(get_db)):
    choices = {"Confirmed discrepancy", "False positive", "Needs further verification", "Resolved after correction"}
    if payload.get("status") not in choices:
        raise HTTPException(status_code=422, detail="Unsupported reviewer classification")
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    previous = finding.status
    finding.status = payload["status"]
    db.add(AuditLog(application_id=finding.application_id, event_type="finding_reviewed",
        description={"finding_id": finding.id, "previous_status": previous,
                     "status": finding.status, "reviewer": payload.get("reviewer", "Demo reviewer")}))
    db.commit()
    return {"message": "Finding classification saved", "status": finding.status}


@router.post("/demo/seed")
async def load_demo_data(db: Session = Depends(get_db)):
    from ...db.seed import seed_demo_data
    seed_demo_data(db)
    return {"message": "Synthetic demo data is ready", "application_count": db.query(Application).count()}


@router.post("/create")
async def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    institution = db.query(Institution).filter(Institution.institution_id == payload.institution_code).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found in synthetic demo directory")
    if db.query(Application).filter(Application.reference_number == payload.reference_number).first():
        raise HTTPException(status_code=409, detail="Application reference already exists")
    app = Application(reference_number=payload.reference_number, institution_name=institution.name,
        institution_id=institution.id, category=payload.category, academic_year=payload.academic_year,
        status="Pending Verification")
    db.add(app)
    db.flush()
    db.add(AuditLog(application_id=app.id, event_type="application_created",
        description={"reference_number": app.reference_number, "actor": "Demo reviewer"}))
    db.commit()
    return {"id": app.id, "message": "Application created"}


@router.post("/{app_id}/documents")
async def upload_documents(app_id: int, category: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a PDF, PNG or JPG document")
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Maximum file size is 15 MB")
    digest = hashlib.sha256(contents).hexdigest()
    safe_name = f"{app_id}-{digest[:16]}{extension}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    destination = os.path.abspath(os.path.join(settings.UPLOAD_DIR, safe_name))
    if not destination.startswith(os.path.abspath(settings.UPLOAD_DIR) + os.sep):
        raise HTTPException(status_code=400, detail="Invalid file path")
    with open(destination, "wb") as output:
        output.write(contents)
    duplicate = db.query(Document).filter(Document.file_hash == digest).first()
    doc = Document(application_id=app.id, category=category, filename=Path(file.filename or safe_name).name,
        filepath=destination, file_hash=digest, mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents), extraction_status="manual_review_required",
        extracted_data={"note": "No OCR output claimed; human extraction is required"})
    db.add(doc)
    db.add(AuditLog(application_id=app.id, event_type="document_uploaded",
        description={"filename": doc.filename, "category": category, "sha256": digest,
                     "duplicate_file": duplicate is not None}))
    db.commit()
    db.refresh(doc)
    return {"document_id": doc.id, "filename": doc.filename, "size_bytes": len(contents),
            "duplicate": duplicate is not None, "extraction_status": doc.extraction_status}


@router.get("/{app_id}")
async def get_application(app_id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    institution = app.institution
    return {"id": app.id, "reference_number": app.reference_number,
        "institution_name": institution.name, "institution_code": institution.institution_id,
        "state": institution.state, "district": institution.district, "category": app.category,
        "academic_year": app.academic_year, "status": app.status,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "institution_record": {"approved_programmes": institution.approved_programmes,
            "approved_intake": institution.approved_intake, "faculty_count": institution.faculty_count,
            "accreditation_status": institution.accreditation_status, "source": "Synthetic demo record"},
        "documents": [{"id": d.id, "category": d.category, "filename": d.filename,
            "size_bytes": d.size_bytes, "extraction_status": d.extraction_status,
            "extracted_data": d.extracted_data, "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None}
            for d in app.documents],
        "findings": [{"id": f.id, "rule_id": f.rule.rule_id if f.rule else "",
            "rule_name": f.rule.name if f.rule else "Review finding", "description": f.description,
            "severity": f.severity, "status": f.status, "evidence": f.evidence or {},
            "confidence": f.confidence, "created_at": f.created_at.isoformat() if f.created_at else None}
            for f in app.findings],
        "audit": [{"id": a.id, "event_type": a.event_type, "description": a.description,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None}
            for a in db.query(AuditLog).filter(AuditLog.application_id == app.id).order_by(AuditLog.timestamp.desc()).all()]}


@router.post("/{app_id}/review")
async def update_review(app_id: int, payload: ReviewUpdate, db: Session = Depends(get_db)):
    allowed = {"Pending Verification", "Manual Review Required", "Under Review",
               "No Issues Detected by Configured Checks", "Resolved after correction"}
    if payload.status not in allowed:
        raise HTTPException(status_code=422, detail="Unsupported application review status")
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    previous = app.status
    app.status = payload.status
    app.updated_at = datetime.utcnow()
    db.add(AuditLog(application_id=app.id, event_type="review_updated",
        description={"previous_status": previous, "status": payload.status, "reviewer": payload.reviewer}))
    if payload.note.strip():
        db.add(AuditLog(application_id=app.id, event_type="reviewer_note_added",
            description={"note": payload.note.strip(), "reviewer": payload.reviewer}))
    db.commit()
    return {"message": "Review updated", "status": app.status}