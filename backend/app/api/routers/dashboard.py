from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...models.application import Application
from ...models.finding import Finding

router = APIRouter()


def application_summary(item: Application) -> dict:
    findings = item.findings
    return {"id": item.id, "reference_number": item.reference_number,
            "institution_name": item.institution.name if item.institution else item.institution_name,
            "institution_code": item.institution.institution_id if item.institution else "",
            "state": item.institution.state if item.institution else "", "category": item.category,
            "academic_year": item.academic_year, "status": item.status,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "document_count": len(item.documents), "finding_count": len(findings),
            "open_findings": sum(f.status == "pending" for f in findings)}


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    applications = db.query(Application).all()
    findings = db.query(Finding).all()
    return {"total_applications": len(applications),
            "pending": sum(a.status in {"Pending Verification", "Manual Review Required"} for a in applications),
            "mismatches": sum(f.status == "pending" for f in findings),
            "missing_or_expired": sum(f.status == "pending" and f.rule and f.rule.rule_id in {"DOC-001", "CERT-001"} for f in findings),
            "manual_review": sum(a.status == "Manual Review Required" for a in applications)}


@router.get("/overview")
async def overview(db: Session = Depends(get_db)):
    applications = db.query(Application).order_by(Application.updated_at.desc()).all()
    distribution = {}
    for item in applications:
        distribution[item.status] = distribution.get(item.status, 0) + 1
    findings = db.query(Finding).order_by(Finding.created_at.desc()).limit(6).all()
    return {"stats": await get_stats(db),
            "applications": [application_summary(item) for item in applications],
            "status_distribution": distribution,
            "recent_findings": [{"id": f.id, "application_id": f.application_id,
                "institution_name": f.application.institution.name, "description": f.description,
                "severity": f.severity, "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None} for f in findings]}