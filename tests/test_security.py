"""
Security and reliability tests for winter-formula-acid-base.
"""
import sys
from pathlib import Path
import warnings
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from winter_acid_base import calculate_metrics, process_batch
from agents.base import AuditTrail, PHIGuard, SecurityException, assert_no_phi


class TestCalculateMetricsEdgeCases:
    """Test edge cases in the core algorithm."""

    def test_empty_kwargs(self):
        """calculate_metrics with no args should return default score."""
        res = calculate_metrics()
        assert res["score"] == 1.0
        assert res["classification"] == "Low / Standard"

    def test_single_value(self):
        res = calculate_metrics(v1=15.0)
        assert res["score"] == 15.0
        assert res["classification"] == "Moderate / Intermediate"

    def test_multiple_values(self):
        res = calculate_metrics(v1=10.0, v2=4.0, v3=2.0)
        # score = 10.0 + 4.0/2 + 2.0/3 = 10 + 2 + 0.67 = 12.67
        assert res["score"] == pytest.approx(12.67, abs=0.01)

    def test_string_values_ignored(self):
        """Non-numeric strings should not affect score."""
        res = calculate_metrics(v1=10.0, name="test")
        assert res["score"] == 10.0

    def test_none_values_ignored(self):
        res = calculate_metrics(v1=10.0, v2=None)
        assert res["score"] == 10.0

    def test_high_score_classification(self):
        res = calculate_metrics(v1=30.0)
        assert res["classification"] == "High / Severe"
        assert "urgent" in res["clinical_recommendation"].lower()

    def test_inputs_evaluated_count(self):
        res = calculate_metrics(v1=5.0, v2=3.0)
        assert res["inputs_evaluated"] == 2


class TestProcessBatchValidation:
    """Test input validation in process_batch."""

    def test_missing_file_raises_error(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv_raises_error(self, tmp_path):
        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty or has no headers"):
            process_batch(str(empty), str(tmp_path / "out.csv"))

    def test_csv_with_only_headers(self, tmp_path):
        csv_in = tmp_path / "headers_only.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient_ID,v1,v2\n", encoding="utf-8")
        process_batch(str(csv_in), str(csv_out))
        content = csv_out.read_text(encoding="utf-8")
        assert "Patient_ID" in content

    def test_batch_output_fields(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("ID,v1,v2\nA,1.0,2.0\n", encoding="utf-8")
        process_batch(str(csv_in), str(csv_out))
        content = csv_out.read_text(encoding="utf-8")
        assert "score" in content
        assert "classification" in content
        assert "clinical_recommendation" in content


class TestPHIGuard:
    """Test PHI detection patterns."""

    def test_mrn_detected(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Patient MRN-12345678")

    def test_ssn_detected(self):
        with pytest.raises(SecurityException):
            assert_no_phi("SSN: 123-45-6789")

    def test_phone_detected(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Call 555-123-4567")

    def test_email_detected(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Email: patient@hospital.com")

    def test_clean_text_passes(self):
        assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_empty_string_passes(self):
        assert_no_phi("")

    def test_none_handled(self):
        assert_no_phi(None)

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("Contact patient@hospital.com")
        assert "[REDACTED_IDENTIFIER]" in redacted
        assert "patient@hospital.com" not in redacted


class TestAuditTrailSecurity:
    """Test audit trail security features."""

    def test_no_hardcoded_default_key(self):
        """AuditTrail should warn when no key is provided."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail()
            assert len(w) == 1
            assert "AUDIT_SECRET_KEY not set" in str(w[0].message)

    def test_custom_key_no_warning(self):
        """Providing a key directly should not warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail(secret_key="test-key-for-unit-tests")
            assert len(w) == 0

    def test_audit_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key")
        trail.log("test", "tier", "event", {"data": "value1"})
        trail.log("test", "tier", "event", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_blocks_phi(self):
        trail = AuditTrail(secret_key="test-key")
        with pytest.raises(SecurityException):
            trail.log("test", "tier", "event", {"data": "MRN-12345678"})
