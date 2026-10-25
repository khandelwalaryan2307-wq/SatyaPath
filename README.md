# SatyaPath

**Evidence-Driven Verification. Transparent Decisions.**

Smart India Hackathon 2026 prototype for AICTE application intake, document checks, evidence review and audit history. This prototype uses synthetic institutional records and simulated source checks. It does not connect to AICTE databases or issuer APIs, and its results are not regulatory decisions.

## Run locally on Windows

The extracted project includes a frontend `node_modules` folder and a backend virtual environment. Open two PowerShell terminals from the project directory.

Backend:

```powershell
Set-Location .\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
Set-Location .\frontend
npm run dev -- --host 127.0.0.1
```

Open <http://localhost:5173/>. API documentation is available at <http://localhost:8000/docs>. Frontend API requests use the `/api` proxy prefix so client-side page routes remain available on direct navigation.

For a fresh checkout, install backend packages with `python -m pip install -r backend/requirements.txt`, and frontend packages with `npm install` from `frontend`.

## Repeatable demo

1. Select **Load demo data** in the left navigation. The seed is deterministic and will not duplicate existing demo records.
2. Open application `SP-2026-002` (North Valley Engineering College) and run validation. The submitted synthetic faculty count is 42; the synthetic reference count is 35.
3. Open the finding in Evidence Explorer and classify it. The reviewer action is saved in the audit trail.
4. Open `SP-2026-003` and run validation to see its missing required document and expired accreditation certificate.
5. Open `SP-2026-001` to run the clean scenario.

## Verification behavior

- Required document presence, certificate expiry, institution identifier and faculty count comparisons use configured demo rules.
- Exact duplicate uploads are detected with SHA-256 hashes. Uploads are limited to PDF, PNG and JPG, with a 15 MB limit, and are stored under the configured local upload directory using server-generated names.
- Uploaded file extraction is explicitly marked for manual review. The app does not claim OCR values it did not extract. Pre-seeded scenario fields are labelled synthetic demo data.
- Findings contain the rule, evidence values and sources, and a recommended reviewer action. A mismatch or metadata signal is not a fraud conclusion.
- Rule changes, reviewer classifications, application status updates and notes are recorded in an append-only audit log.

## Configuration

Copy `backend/.env.example` to `backend/.env` to customize settings. SQLite is used by default and the database is created at startup. `DATABASE_URL` may be set to a PostgreSQL SQLAlchemy URL when a PostgreSQL service is available. Never commit credentials or real applicant documents.

## Tests

```powershell
Set-Location .\backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend production build:

```powershell
Set-Location .\frontend
npm run build
```

## Prototype limitations

- No authenticated identity provider or real role enforcement is configured; the reviewer/admin roles shown are demo roles.
- No live AICTE reference source or issuer service is contacted.
- OCR, document authenticity conclusions, PDF structural analysis and real regulatory approval decisions are outside this prototype. Uploaded documents require human extraction/review.
- Sample checklist rules are configurable examples and must be checked against the applicable official AICTE handbook before operational use.