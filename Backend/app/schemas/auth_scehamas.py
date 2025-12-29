from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
    
class UserRegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)
    otp: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 20:
            raise ValueError('Password must be at most 20 characters long')
        return v
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be exactly 6 digits')
        return v
        return v
    
class LoginResponseSchema(BaseModel):
    access_token: str
    token_type: str ='bearer'
    
    class Config:
        from_attributes = True 