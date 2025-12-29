from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import random
import string
from app.services.email_service import email_service


class OTPService:
    """
    OTP Service for generating and verifying One-Time Passwords
    Stores OTPs in memory with expiration time (5 minutes)
    """
    
    def __init__(self):
        # Store OTPs: {identifier: {"otp": "123456", "expires_at": datetime, "attempts": 0}}
        self._otp_store: Dict[str, Dict] = {}
        self.OTP_LENGTH = 6
        self.OTP_EXPIRY_MINUTES = 5
        self.MAX_ATTEMPTS = 3
    
    def generate_otp(self, identifier: str) -> str:
        """
        Generate a random 6-digit OTP for the given identifier (email/phone)
        Sends OTP via email
        
        Args:
            identifier: Email or phone number
            
        Returns:
            6-digit OTP as string
        """
        # Generate random 6-digit number
        otp = ''.join(random.choices(string.digits, k=self.OTP_LENGTH))
        
        # Calculate expiry time (5 minutes from now)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        
        # Store OTP with metadata
        self._otp_store[identifier] = {
            "otp": otp,
            "expires_at": expires_at,
            "attempts": 0,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Send OTP via email
        email_service.send_otp_email(identifier, otp)
        
        return otp
    
    def verify_otp(self, identifier: str, otp: str) -> Dict[str, any]:
        """
        Verify if the provided OTP is valid for the identifier
        
        Args:
            identifier: Email or phone number
            otp: OTP to verify
            
        Returns:
            Dict with verification result: {"valid": bool, "message": str}
        """
        # Check if OTP exists for this identifier
        if identifier not in self._otp_store:
            return {
                "valid": False,
                "message": "No OTP found for this identifier. Please request a new OTP."
            }
        
        stored_data = self._otp_store[identifier]
        
        # Check if OTP has expired
        if datetime.now(timezone.utc) > stored_data["expires_at"]:
            # Clean up expired OTP
            del self._otp_store[identifier]
            return {
                "valid": False,
                "message": "OTP has expired. Please request a new OTP."
            }
        
        # Check if max attempts exceeded
        if stored_data["attempts"] >= self.MAX_ATTEMPTS:
            # Clean up after max attempts
            del self._otp_store[identifier]
            return {
                "valid": False,
                "message": "Maximum verification attempts exceeded. Please request a new OTP."
            }
        
        # Increment attempt counter
        stored_data["attempts"] += 1
        
        # Verify OTP
        if stored_data["otp"] == otp:
            # OTP is valid - clean up
            del self._otp_store[identifier]
            return {
                "valid": True,
                "message": "OTP verified successfully."
            }
        else:
            remaining_attempts = self.MAX_ATTEMPTS - stored_data["attempts"]
            return {
                "valid": False,
                "message": f"Invalid OTP. {remaining_attempts} attempts remaining."
            }
    
    def get_otp_info(self, identifier: str) -> Optional[Dict]:
        """
        Get OTP information for debugging (without revealing the actual OTP)
        
        Args:
            identifier: Email or phone number
            
        Returns:
            Dict with OTP metadata or None
        """
        if identifier not in self._otp_store:
            return None
        
        stored_data = self._otp_store[identifier]
        now = datetime.now(timezone.utc)
        
        return {
            "exists": True,
            "expires_at": stored_data["expires_at"],
            "created_at": stored_data["created_at"],
            "is_expired": now > stored_data["expires_at"],
            "attempts": stored_data["attempts"],
            "remaining_attempts": self.MAX_ATTEMPTS - stored_data["attempts"],
            "time_remaining_seconds": int((stored_data["expires_at"] - now).total_seconds())
        }
    
    def resend_otp(self, identifier: str) -> str:
        """
        Resend OTP (generates a new one and invalidates the old one)
        
        Args:
            identifier: Email or phone number
            
        Returns:
            New 6-digit OTP as string
        """
        # Delete old OTP if exists
        if identifier in self._otp_store:
            del self._otp_store[identifier]
        
        # Generate and return new OTP
        return self.generate_otp(identifier)
    
    def cleanup_expired(self):
        """
        Clean up expired OTPs from memory
        Should be called periodically
        """
        now = datetime.now(timezone.utc)
        expired_identifiers = [
            identifier for identifier, data in self._otp_store.items()
            if now > data["expires_at"]
        ]
        
        for identifier in expired_identifiers:
            del self._otp_store[identifier]
        
        return len(expired_identifiers)


# Singleton instance
otp_service = OTPService()
