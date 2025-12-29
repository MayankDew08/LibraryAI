from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.services.otp import otp_service

router = APIRouter(prefix="/otp", tags=["otp"])


class OTPGenerateRequest(BaseModel):
    """Schema for OTP generation request"""
    identifier: str  # Can be email or phone number
    

class OTPVerifyRequest(BaseModel):
    """Schema for OTP verification request"""
    identifier: str
    otp: str


@router.post("/generate")
def generate_otp(request: OTPGenerateRequest):
    """
    Generate a 6-digit OTP for the given identifier (email/phone)
    OTP expires after 5 minutes and is sent via email
    """
    try:
        otp = otp_service.generate_otp(request.identifier)
        
        # For development, still return OTP in response
        # In production, remove the "otp" field from response
        
        return {
            "message": "OTP sent to your email successfully",
            "identifier": request.identifier,
            "otp": otp,  # For development - remove in production
            "expires_in_minutes": 5,
            "note": "Check your email for the OTP code"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating OTP: {str(e)}"
        )


@router.post("/verify")
def verify_otp(request: OTPVerifyRequest):
    """
    Verify the OTP provided by user
    Maximum 3 attempts allowed
    """
    try:
        result = otp_service.verify_otp(request.identifier, request.otp)
        
        if result["valid"]:
            return {
                "verified": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying OTP: {str(e)}"
        )


@router.post("/resend")
def resend_otp(request: OTPGenerateRequest):
    """
    Resend OTP (generates a new one and invalidates the old one)
    """
    try:
        otp = otp_service.resend_otp(request.identifier)
        
        return {
            "message": "New OTP generated successfully",
            "identifier": request.identifier,
            "otp": otp,  # REMOVE THIS IN PRODUCTION!
            "expires_in_minutes": 5,
            "note": "Previous OTP has been invalidated"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resending OTP: {str(e)}"
        )


@router.get("/status/{identifier}")
def get_otp_status(identifier: str):
    """
    Get OTP status for an identifier (for debugging)
    Returns metadata without revealing the actual OTP
    """
    info = otp_service.get_otp_info(identifier)
    
    if info is None:
        return {
            "exists": False,
            "message": "No active OTP for this identifier"
        }
    
    return info


@router.post("/cleanup")
def cleanup_expired_otps():
    """
    Manually trigger cleanup of expired OTPs
    In production, this should run automatically via scheduled task
    """
    count = otp_service.cleanup_expired()
    return {
        "message": "Cleanup completed",
        "expired_otps_removed": count
    }
