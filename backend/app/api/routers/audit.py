from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...models.audit_log import AuditLog

router = APIRouter()


@router.get("/")
async def list_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(250).all()
    return [{"id": log.id, "application_id": log.application_id,
             "reference_number": log.application.reference_number if log.application else None,
             "event_type": log.event_type, "description": log.description or {},
             "timestamp": log.timestamp.isoformat() if log.timestamp else None}
            for log in logs]