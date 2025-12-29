import pytest
from datetime import datetime, timedelta, timezone
from app.services.otp import OTPService

class DummyEmailService:
    def __init__(self):
        self.sent = []
    def send_otp_email(self, identifier, otp):
        self.sent.append((identifier, otp))

@pytest.fixture(autouse=True)
def patch_email_service(monkeypatch):
    dummy = DummyEmailService()
    monkeypatch.setattr("app.services.otp.email_service", dummy)
    return dummy

@pytest.fixture
def otp():
    return OTPService()

def test_generate_otp(otp, patch_email_service):
    identifier = "user123@example.com"
    generated_otp = otp.generate_otp(identifier)
    assert len(generated_otp) == 6
    assert generated_otp.isdigit()
    # Check email sent
    assert patch_email_service.sent[-1][0] == identifier
    assert patch_email_service.sent[-1][1] == generated_otp

def test_verify_otp_success(otp):
    identifier = "user456@example.com"
    generated_otp = otp.generate_otp(identifier)
    result = otp.verify_otp(identifier, generated_otp)
    assert result["valid"] is True
    assert "successfully" in result["message"].lower()

def test_verify_otp_invalid(otp):
    identifier = "user789@example.com"
    otp.generate_otp(identifier)
    result = otp.verify_otp(identifier, "000000")
    assert result["valid"] is False
    assert "invalid" in result["message"].lower()

def test_verify_otp_expired(otp):
    identifier = "user_expired@example.com"
    otp.generate_otp(identifier)
    # Manually expire
    otp._otp_store[identifier]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    result = otp.verify_otp(identifier, otp._otp_store[identifier]["otp"])
    assert result["valid"] is False
    assert "expired" in result["message"].lower()

def test_verify_otp_max_attempts(otp):
    identifier = "user_attempts@example.com"
    otp.generate_otp(identifier)
    for _ in range(otp.MAX_ATTEMPTS):
        otp.verify_otp(identifier, "wrongotp")
    # Next attempt should be blocked
    result = otp.verify_otp(identifier, "wrongotp")
    assert result["valid"] is False
    assert "maximum verification attempts" in result["message"].lower()

def test_resend_otp_generates_new(otp, patch_email_service):
    identifier = "user_resend@example.com"
    first_otp = otp.generate_otp(identifier)
    second_otp = otp.resend_otp(identifier)
    assert first_otp != second_otp
    assert patch_email_service.sent[-1][1] == second_otp

def test_get_otp_info(otp):
    identifier = "user_info@example.com"
    otp.generate_otp(identifier)
    info = otp.get_otp_info(identifier)
    assert info["exists"] is True
    assert info["remaining_attempts"] == otp.MAX_ATTEMPTS

def test_cleanup_expired(otp):
    identifier = "user_cleanup@example.com"
    otp.generate_otp(identifier)
    # Expire OTP
    otp._otp_store[identifier]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    cleaned = otp.cleanup_expired()
    assert cleaned == 1
    assert otp.get_otp_info(identifier) is None
    