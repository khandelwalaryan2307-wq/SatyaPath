from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class InstitutionBase(BaseModel):
    institution_id: str = Field(..., description="Unique institution identifier")
    name: str
    state: Optional[str] = None
    district: Optional[str] = None
    approved_programmes: Optional[List[str]] = None
    approved_intake: Optional[int] = None
    faculty_count: Optional[int] = None
    accreditation_status: Optional[str] = None

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionRead(InstitutionBase):
    id: int
    class Config:
        orm_mode = True

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    approved_programmes: Optional[List[str]] = None
    approved_intake: Optional[int] = None
    faculty_count: Optional[int] = None
    accreditation_status: Optional[str] = None
    class Config:
        orm_mode = True
