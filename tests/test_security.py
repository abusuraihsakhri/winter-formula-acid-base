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
    def test_required_hco3(self):
        with pytest.raises(ValueError, match="hco3 is required"):
            calculate_metrics()

    def test_non_numeric_rejected(self):
        with pytest.raises(ValueError, match="hco3 must be a number"):
            calculate_metrics(hco3="not a number")

    def test_expected_range(self):
        assert calculate_metrics(hco3=10)["expected_pco2"] == 23.0


class TestProcessBatchValidation:
    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv(self, tmp_path):
        source = tmp_path / "empty.csv"
        source.write_text("")
        with pytest.raises(ValueError, match="empty or has no headers"):
            process_batch(str(source), str(tmp_path / "out.csv"))

    def test_header_only_batch(self, tmp_path):
        source = tmp_path / "input.csv"
        source.write_text("Case_ID,hco3,pco2\\n".replace("\\n", "\n"))
        target = tmp_path / "output.csv"
        process_batch(str(source), str(target))
        assert "expected_pco2" in target.read_text()

    def test_missing_required_column(self, tmp_path):
        source = tmp_path / "input.csv"
        source.write_text("Case_ID,pco2\\nA,28\\n".replace("\\n", "\n"))
        with pytest.raises(ValueError, match="must include hco3"):
            process_batch(str(source), str(tmp_path / "output.csv"))


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
