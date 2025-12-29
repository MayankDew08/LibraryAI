from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth_scehamas import UserRegisterSchema
from app.schemas.admin_schemas import AdminLoginSchema, AdminRegisterSchema, StudentLoginWithOTPSchema
from app.services import auth
from app.services.otp import otp_service
from app.config.database import get_db
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/student/register", status_code=status.HTTP_201_CREATED)
def register_student(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    """
    Register a new student with OTP verification
    Steps:
    1. User requests OTP via POST /otp/generate
    2. User receives OTP (via email/SMS in production, in response for dev)
    3. User submits name, email, password, role='student', and OTP
    4. System verifies OTP and creates account
    """
    try:
        # Step 1: Verify OTP first
        otp_result = otp_service.verify_otp(user_data.email, user_data.otp)
        
        if not otp_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_result["message"]
            )
        
        # Step 2: Register the user
        result = auth.register_user(db, user_data)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/student/login")
def login_student(login_data: StudentLoginWithOTPSchema, db: Session = Depends(get_db)):
    """
    Authenticate student with email, password, and OTP
    Steps:
    1. User requests OTP via POST /otp/generate
    2. User receives OTP (via email/SMS in production, in response for dev)
    3. User submits email, password, and OTP
    4. System verifies all three
    """
    try:
        # Step 1: Verify OTP first
        otp_result = otp_service.verify_otp(login_data.email, login_data.otp)
        
        if not otp_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_result["message"]
            )
        
        # Step 2: Verify email and password
        result = auth.login_student_with_credentials(db, login_data.email, login_data.password)
        access_token= auth.create_access_token(data={"sub": login_data.email})
        return {
            "message": "Student login successful",
            "user": result,
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/admin/register", status_code=status.HTTP_201_CREATED)
def register_admin(admin_data: AdminRegisterSchema, db: Session = Depends(get_db)):
    """
    Register a new admin with OTP verification and admin password
    Steps:
    1. Admin requests OTP via POST /otp/generate
    2. Admin receives OTP (via email/SMS in production, in response for dev)
    3. Admin submits name, email, password='Admin@123', and OTP
    4. System verifies OTP and admin password, then creates account
    """
    try:
        # Step 1: Verify OTP first
        otp_result = otp_service.verify_otp(admin_data.email, admin_data.otp)
        
        if not otp_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_result["message"]
            )
        
        # Step 2: Register the admin (password already validated in schema)
        result = auth.register_admin(db, admin_data)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/login")
def admin_login(login_data: AdminLoginSchema, db: Session = Depends(get_db)):
    """
    Authenticate admin with email, password, and OTP
    Steps:
    1. Admin requests OTP via POST /otp/generate
    2. Admin receives OTP (via email/SMS in production, in response for dev)
    3. Admin submits email, password, and OTP
    4. System verifies all three
    """
    try:
        # Step 1: Verify OTP first
        otp_result = otp_service.verify_otp(login_data.email, login_data.otp)
        
        if not otp_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_result["message"]
            )
        
        # Step 2: Verify email and password
        result = auth.login_admin_with_credentials(db, login_data.email, login_data.password)
        
        return {
            "message": "Admin login successful",
            "admin": result
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

