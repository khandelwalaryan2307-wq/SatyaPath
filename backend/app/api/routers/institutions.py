from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...models.institution import Institution

router = APIRouter()


@router.get("/")
async def list_institutions(search: str = "", db: Session = Depends(get_db)):
    query = db.query(Institution)
    if search:
        query = query.filter((Institution.name.ilike(f"%{search}%")) |
                             (Institution.institution_id.ilike(f"%{search}%")) |
                             (Institution.state.ilike(f"%{search}%")))
    return [{"id": i.id, "institution_id": i.institution_id, "name": i.name,
             "state": i.state, "district": i.district, "approved_programmes": i.approved_programmes or [],
             "approved_intake": i.approved_intake, "faculty_count": i.faculty_count,
             "accreditation_status": i.accreditation_status,
             "last_updated": i.last_updated.isoformat() if i.last_updated else None,
             "source": "Synthetic demo record; not an official AICTE data source"}
            for i in query.order_by(Institution.name).all()]