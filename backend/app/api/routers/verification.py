from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...models.application import Application
from ...models.audit_log import AuditLog
from ...models.finding import Finding
from ...models.rule import Rule

router = APIRouter()
REQUIRED_DOCUMENTS = {"Application Form", "Affidavit", "Accreditation Certificate", "Previous Approval Letter"}


def add_finding(db, app, rule, description, evidence, severity=None):
    existing = db.query(Finding).filter(Finding.application_id == app.id, Finding.rule_id == rule.id,
        Finding.description == description, Finding.status == "pending").first()
    if existing:
        return existing
    finding = Finding(application_id=app.id, rule_id=rule.id, severity=severity or rule.severity,
        description=description, evidence=evidence, confidence=None)
    db.add(finding)
    db.flush()
    db.add(AuditLog(application_id=app.id, event_type="finding_generated",
        description={"finding_id": finding.id, "rule_id": rule.rule_id, "severity": finding.severity}))
    return finding


@router.post("/{app_id}/validate")
async def validate_application(app_id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    rules = {r.rule_id: r for r in db.query(Rule).filter(Rule.enabled.is_(True)).all()}
    docs = app.documents
    present = {doc.category for doc in docs}
    created = []
    missing = sorted(REQUIRED_DOCUMENTS - present)
    if missing and "DOC-001" in rules:
        result = add_finding(db, app, rules["DOC-001"], "Missing required documents: " + ", ".join(missing),
            {"check": "Required document presence", "expected": sorted(REQUIRED_DOCUMENTS),
             "observed": sorted(present), "missing": missing, "source": "Configured demo checklist",
             "next_action": "Request the listed documents from the applicant"}, "high")
        created.append(result.id)
    institution = app.institution
    seen_hashes = {}
    for doc in docs:
        data = doc.extracted_data or {}
        expiry = data.get("expiry_date")
        if expiry and "CERT-001" in rules:
            try:
                expired = date.fromisoformat(expiry) < date.today()
            except (TypeError, ValueError):
                expired = False
            if expired:
                result = add_finding(db, app, rules["CERT-001"], f"{doc.category} expiry date {expiry} has passed.",
                    {"check": "Certificate expiry date", "document": doc.filename,
                     "observed_expiry": expiry, "checked_on": date.today().isoformat(),
                     "source": "Synthetic demo extraction", "next_action": "Request a current certificate"}, "high")
                created.append(result.id)
        submitted_id = data.get("institution_id")
        if submitted_id and submitted_id != institution.institution_id and "ID-001" in rules:
            result = add_finding(db, app, rules["ID-001"], "Institution identifier differs from the synthetic reference record.",
                {"check": "Institution identifier consistency", "document": doc.filename,
                 "document_value": submitted_id, "reference_value": institution.institution_id,
                 "reference_source": "Synthetic demo institution record", "next_action": "Verify the identifier with the applicant"}, "high")
            created.append(result.id)
        faculty = data.get("faculty_count")
        if faculty is not None and faculty != institution.faculty_count and "FAC-001" in rules:
            result = add_finding(db, app, rules["FAC-001"],
                f"Faculty count mismatch: document reports {faculty}; synthetic reference record lists {institution.faculty_count}.",
                {"check": "Cross-document faculty count consistency", "document": doc.filename,
                 "document_value": faculty, "reference_value": institution.faculty_count,
                 "reference_source": "Synthetic demo institution record", "next_action": "Compare the submitted roster with the reference record"}, "medium")
            created.append(result.id)
        if doc.file_hash in seen_hashes and "DOC-001" in rules:
            result = add_finding(db, app, rules["DOC-001"], "Duplicate file content detected by SHA-256 hash.",
                {"check": "Exact duplicate file hash", "document_a": seen_hashes[doc.file_hash],
                 "document_b": doc.filename, "sha256": doc.file_hash,
                 "next_action": "Confirm whether the duplicate upload is intentional"}, "medium")
            created.append(result.id)
        else:
            seen_hashes[doc.file_hash] = doc.filename
    active = db.query(Finding).filter(Finding.application_id == app.id, Finding.status == "pending").all()
    app.status = "Manual Review Required" if any(f.severity == "high" for f in active) else (
        "Mismatch Detected" if active else "No Issues Detected by Configured Checks")
    app.updated_at = datetime.utcnow()
    db.add(AuditLog(application_id=app.id, event_type="validation_executed",
        description={"finding_ids": created, "active_finding_count": len(active),
                     "source": "Configured demo checks; human review required"}))
    db.commit()
    return {"message": "Validation completed using configured demo checks", "status": app.status,
        "new_finding_ids": sorted(set(created)), "active_finding_count": len(active),
        "disclaimer": "A clean preliminary result is not an official approval."}