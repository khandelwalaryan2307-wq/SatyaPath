from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models.application import Application
from ..models.audit_log import AuditLog
from ..models.document import Document
from ..models.institution import Institution
from ..models.rule import Rule


RULES = [
    ("DOC-001", "Required documents present", "Required supporting documents should be provided.", "high"),
    ("CERT-001", "Certificate validity", "Submitted certificates should not be expired.", "high"),
    ("ID-001", "Institution identifier consistency", "The identifier should match the synthetic reference record.", "high"),
    ("FAC-001", "Faculty count consistency", "Faculty count should agree with the synthetic reference record.", "medium"),
    ("INT-001", "Approved intake consistency", "Programme intake should agree with the synthetic reference record.", "medium"),
]

INSTITUTIONS = [
    ("DEMO-1001", "ABC Institute of Technology", "Karnataka", "Bengaluru", 420, 42, ["Computer Science", "Electronics", "Mechanical"], "valid"),
    ("DEMO-1002", "North Valley Engineering College", "Uttar Pradesh", "Lucknow", 360, 35, ["Computer Science", "Civil"], "valid"),
    ("DEMO-1003", "Coastal School of Engineering", "Kerala", "Kochi", 300, 31, ["Computer Science", "Electrical"], "expired"),
    ("DEMO-1004", "Central Institute of Applied Sciences", "Madhya Pradesh", "Bhopal", 480, 48, ["Computer Science", "Electronics", "Civil"], "valid"),
    ("DEMO-1005", "Eastern Technical University", "West Bengal", "Kolkata", 360, 36, ["Computer Science", "Mechanical"], "valid"),
    ("DEMO-1006", "Deccan College of Engineering", "Maharashtra", "Pune", 420, 40, ["Computer Science", "Electrical"], "valid"),
    ("DEMO-1007", "Riverbend Institute of Technology", "Assam", "Guwahati", 240, 24, ["Civil", "Computer Science"], "pending"),
    ("DEMO-1008", "Western Hills Polytechnic", "Rajasthan", "Jaipur", 300, 29, ["Mechanical", "Electrical"], "valid"),
    ("DEMO-1009", "Southern Institute of Engineering", "Tamil Nadu", "Chennai", 540, 53, ["Computer Science", "Electronics", "Civil"], "valid"),
    ("DEMO-1010", "Lakeside College of Technology", "Telangana", "Hyderabad", 360, 34, ["Computer Science", "Mechanical"], "valid"),
]


def seed_demo_data(db: Session) -> None:
    if db.query(Institution).count() == 0:
        for code, name, state, district, intake, faculty, programmes, accreditation in INSTITUTIONS:
            db.add(Institution(institution_id=code, name=name, state=state, district=district,
                               approved_intake=intake, faculty_count=faculty,
                               approved_programmes=programmes, accreditation_status=accreditation))
        db.flush()

    if db.query(Rule).count() == 0:
        for code, name, description, severity in RULES:
            db.add(Rule(rule_id=code, name=name, description=description,
                        category="Extension of Approval", severity=severity, enabled=True))
        db.flush()

    if db.query(Application).count() == 0:
        institutions = {item.institution_id: item for item in db.query(Institution).all()}
        scenarios = [
            ("SP-2026-001", "DEMO-1001", "No Issues Detected by Configured Checks", 42, "valid", True),
            ("SP-2026-002", "DEMO-1002", "Mismatch Detected", 42, "valid", True),
            ("SP-2026-003", "DEMO-1003", "Manual Review Required", 31, "expired", False),
            ("SP-2026-004", "DEMO-1004", "Pending Verification", 48, "valid", True),
            ("SP-2026-005", "DEMO-1005", "No Issues Detected by Configured Checks", 36, "valid", True),
            ("SP-2026-006", "DEMO-1006", "Mismatch Detected", 37, "valid", True),
            ("SP-2026-007", "DEMO-1007", "Manual Review Required", 24, "valid", False),
            ("SP-2026-008", "DEMO-1008", "Pending Verification", 29, "valid", True),
            ("SP-2026-009", "DEMO-1009", "No Issues Detected by Configured Checks", 53, "valid", True),
            ("SP-2026-010", "DEMO-1010", "Pending Verification", 34, "valid", True),
        ]
        required = ["Application Form", "Affidavit", "Accreditation Certificate", "Previous Approval Letter"]
        now = datetime.utcnow()
        for index, (reference, code, status, faculty, certificate, complete) in enumerate(scenarios):
            institution = institutions[code]
            application = Application(
                reference_number=reference, institution_name=institution.name,
                institution_id=institution.id, category="Extension of Approval",
                academic_year="2026-27", status=status,
                created_at=now - timedelta(days=index * 2 + 1),
            )
            db.add(application)
            db.flush()
            categories = required if complete else required[:3] if certificate == "expired" else required[:2]
            for category in categories:
                extracted = {"institution_id": code, "faculty_count": faculty,
                             "approved_intake": institution.approved_intake,
                             "expiry_date": "2024-03-31" if certificate == "expired" and category == "Accreditation Certificate" else "2028-03-31"}
                db.add(Document(
                    application_id=application.id, category=category,
                    filename=f"{reference.lower()}-{category.lower().replace(' ', '-')}.pdf",
                    filepath="", file_hash=f"demo-{reference}-{category}",
                    mime_type="application/pdf", size_bytes=184320 + index * 1024,
                    extraction_status="synthetic_demo", extracted_data=extracted,
                    uploaded_at=application.created_at,
                ))
            db.add(AuditLog(application_id=application.id, event_type="application_created",
                            description={"reference_number": reference, "source": "Synthetic demo data"},
                            timestamp=application.created_at))
        db.flush()
    db.commit()