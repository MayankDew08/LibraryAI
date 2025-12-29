from pydantic import BaseModel, EmailStr, field_validator


class AdminRegisterSchema(BaseModel):
    """Schema for admin registration"""
    name: str
    email: EmailStr
    password: str
    otp: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if v != 'Admin@123':
            raise ValueError('Invalid admin password')
        return v
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be exactly 6 digits')
        return v


class AdminLoginSchema(BaseModel):
    """Schema for admin login with OTP"""
    email: EmailStr
    password: str
    otp: str
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be exactly 6 digits')
        return v


class StudentLoginWithOTPSchema(BaseModel):
    """Schema for student login with OTP"""
    email: EmailStr
    password: str
    otp: str
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be exactly 6 digits')
        return v
