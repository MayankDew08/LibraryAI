from sqlalchemy.orm import Session
from app.config.database import get_db
from fastapi import Depends
from app.models.users import User, UserRole
from app.models.admin import Admin
from app.schemas.auth_scehamas import UserRegisterSchema
from app.schemas.admin_schemas import AdminRegisterSchema
from app.utils.security import hash_password, verify_password
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timezone, timedelta
from authlib.jose import JoseError, jwt
from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
        
def create_access_token(data: dict):
    header={"alg": ALGORITHM}
    expire=datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = data.copy()
    payload.update({"exp": expire})
    return jwt.encode(header, payload, SECRET_KEY).decode('utf-8')

def verify_token(token : str):
    try:
        claims= jwt.decode(token, SECRET_KEY)
        claims.validate()
        username= claims.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return username
    except JoseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def register_user(db: Session, user_data: UserRegisterSchema):
    """Register a new user in the system"""
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise ValueError("Email already registered")
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    # Create new user with role automatically set to 'student'
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=UserRole.student
    )
    
    db.add(new_user)
    db.commit()
    
    # Generate JWT access token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id, "role": new_user.role.value}
    )
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role.value,
        "access_token": access_token,
        "token_type": "bearer"
    }


def login_student_with_credentials(db: Session, email: str, password: str):
    """Authenticate student with email and password (OTP already verified)"""
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise ValueError("User account is deactivated")
    
    # Generate JWT access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value}
    )
    
    return {
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "access_token": access_token,
        "token_type": "bearer"
    }


def register_admin(db: Session, admin_data: AdminRegisterSchema):
    """Register a new admin in the system"""
    # Check if email already exists
    if db.query(Admin).filter(Admin.email == admin_data.email).first():
        raise ValueError("Email already registered")
    
    # Hash the password
    hashed_password = hash_password(admin_data.password)
    
    # Create new admin
    new_admin = Admin(
        name=admin_data.name,
        email=admin_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_admin)
    db.commit()
    
    # Generate JWT access token
    access_token = create_access_token(
        data={"sub": new_admin.email, "admin_id": new_admin.id, "role": "admin"}
    )
    
    return {
        "message": "Admin registered successfully",
        "admin_id": new_admin.id,
        "name": new_admin.name,
        "email": new_admin.email,
        "role": "admin",
        "access_token": access_token,
        "token_type": "bearer"
    }
    

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency to get current authenticated user from JWT token"""
    email = verify_token(token)  # Returns email from token
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.role not in [UserRole.student, "student"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Student access required."
        )
    
    return user


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency to get current authenticated admin from JWT token"""
    email = verify_token(token)  # Returns email from token
    
    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )
    
    return admin


def login_admin_with_credentials(db: Session, email: str, password: str):
    """Authenticate admin with email and password (OTP already verified)"""
    # Find admin by email
    admin = db.query(Admin).filter(Admin.email == email).first()
    
    if not admin:
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not verify_password(password, admin.hashed_password):
        raise ValueError("Invalid email or password")
    
    # Check if admin is active
    if not admin.is_active:
        raise ValueError("Admin account is deactivated")
    
    # Generate JWT access token
    access_token = create_access_token(
        data={"sub": admin.email, "admin_id": admin.id, "role": "admin"}
    )
    
    return {
        "admin_id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "role": "admin",
        "access_token": access_token,
        "token_type": "bearer"
    }