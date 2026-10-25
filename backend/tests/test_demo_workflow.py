import os
import tempfile
import unittest

test_directory = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{test_directory.name}/satypath-test.db"
os.environ["UPLOAD_DIR"] = f"{test_directory.name}/uploads"

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import engine


class DemoWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        engine.dispose()
        test_directory.cleanup()

    def test_dashboard_validation_review_and_audit(self):
        overview = self.client.get("/dashboard/overview")
        self.assertEqual(overview.status_code, 200)
        self.assertEqual(len(overview.json()["applications"]), 10)

        mismatch = self.client.post("/applications/2/validate")
        self.assertEqual(mismatch.status_code, 200)
        self.assertEqual(mismatch.json()["status"], "Mismatch Detected")

        findings = self.client.get("/applications/evidence").json()
        faculty = next(item for item in findings if item["application_id"] == 2 and item["rule_id"] == "FAC-001")
        self.assertEqual(faculty["evidence"]["document_value"], 42)
        self.assertEqual(faculty["evidence"]["reference_value"], 35)

        review = self.client.post(f"/applications/evidence/{faculty['id']}/review",
                                  json={"status": "Confirmed discrepancy"})
        self.assertEqual(review.status_code, 200)
        self.assertTrue(any(item["event_type"] == "finding_reviewed"
                            for item in self.client.get("/audit/").json()))

    def test_clean_and_missing_expired_scenarios(self):
        clean = self.client.post("/applications/1/validate")
        self.assertEqual(clean.status_code, 200)
        self.assertEqual(clean.json()["status"], "No Issues Detected by Configured Checks")

        expired = self.client.post("/applications/3/validate")
        self.assertEqual(expired.status_code, 200)
        findings = self.client.get("/applications/evidence").json()
        scenario_findings = [item for item in findings if item["application_id"] == 3]
        self.assertTrue(any(item["rule_id"] == "DOC-001" for item in scenario_findings))
        self.assertTrue(any(item["rule_id"] == "CERT-001" for item in scenario_findings))


if __name__ == "__main__":
    unittest.main()