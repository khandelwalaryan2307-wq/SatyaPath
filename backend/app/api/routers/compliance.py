from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...models.audit_log import AuditLog
from ...models.rule import Rule

router = APIRouter()


class RuleUpdate(BaseModel):
    enabled: bool


@router.get("/")
async def list_rules(db: Session = Depends(get_db)):
    return [{"id": r.id, "rule_id": r.rule_id, "name": r.name, "description": r.description,
             "category": r.category, "severity": r.severity, "enabled": r.enabled,
             "last_updated": r.last_updated.isoformat() if r.last_updated else None,
             "source": "Configurable sample rule; verify against the current official handbook"}
            for r in db.query(Rule).order_by(Rule.rule_id).all()]


@router.patch("/{rule_id}")
async def update_rule(rule_id: str, payload: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.enabled = payload.enabled
    rule.last_updated = datetime.utcnow()
    db.add(AuditLog(event_type="compliance_rule_updated",
        description={"rule_id": rule.rule_id, "enabled": rule.enabled, "actor": "Demo administrator"}))
    db.commit()
    return {"rule_id": rule.rule_id, "enabled": rule.enabled}