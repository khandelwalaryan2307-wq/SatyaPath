import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import dashboard, applications, verification, compliance, institutions, audit
from app.core.database import SessionLocal, engine
from app.db.seed import seed_demo_data
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.finding import Finding
from app.models.institution import Institution
from app.models.rule import Rule
from app.models.base import Base

app = FastAPI(title="SatyaPath Backend", version="0.1.0")

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(verification.router, prefix="/applications", tags=["verification"])
app.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
app.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])


@app.on_event("startup")
def initialize_demo_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
