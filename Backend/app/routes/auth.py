from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth_scehamas import UserRegisterSchema, UserLoginSchema
from app.services import auth
from app.config.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class AdminLoginSchema(BaseModel):
    """Schema for admin login (simple password check)"""
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        result = auth.register_user(db, user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(login_data: UserLoginSchema, db: Session = Depends(get_db)):
    """Authenticate user and return user details"""
    try:
        result = auth.login_user(db, login_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/admin-login")
def admin_login(login_data: AdminLoginSchema):
    """Admin login endpoint with hardcoded password"""
    if login_data.password == "Admin@123":
        return {
            "message": "Admin login successful",
            "role": "admin",
            "access_granted": True
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid admin password"
        )

