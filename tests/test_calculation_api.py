"""API and HMAC regression tests."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail


def test_clinical_api_and_static_site():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/calculate", json={
        "hco3": 12, "pco2": 26, "sodium": 140,
        "chloride": 100, "albumin": 2
    })
    assert response.status_code == 200
    assert response.json()["expected_pco2"] == 26
    assert response.json()["corrected_anion_gap"] == 33
    assert response.json()["delta_ratio"] == 1.75
    assert client.post("/api/calculate", json={"hco3": 12, "sodium": 140}).status_code == 422
    assert client.get("/").status_code == 200
    assert "Winter's formula" in client.get("/").text
    assert "function calculateMetrics" in client.get("/calculator.js").text


def test_audit_detects_field_tampering():
    ledger = AuditTrail(secret_key="test-key-only")
    ledger.log("actor", "supervisor", "test", {"status": "OK"})
    ledger.log("actor", "supervisor", "test", {"status": "OK"})
    assert ledger.verify_integrity()
    ledger.logs[0]["event_type"] = "FORGED"
    assert not ledger.verify_integrity()


def test_audit_does_not_expose_mutable_log_records():
    ledger = AuditTrail(secret_key="test-key-only")
    ledger.log("actor", "supervisor", "test", {"status": "OK"})
    public_log = ledger.get_trail()
    public_log[0]["event_type"] = "changed"
    assert ledger.verify_integrity()
