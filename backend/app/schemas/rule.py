from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RuleBase(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    severity: str = Field(default="medium", description="low, medium, high")
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None

class RuleCreate(RuleBase):
    pass

class RuleRead(RuleBase):
    id: int
    class Config:
        orm_mode = True

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    class Config:
        orm_mode = True
