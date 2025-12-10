from sqlalchemy.orm import Session
from app.models.users import User, UserRole
from app.schemas.auth_scehamas import UserRegisterSchema, UserLoginSchema
from app.utils.security import hash_password, verify_password


def register_user(db: Session, user_data: UserRegisterSchema):
    """Register a new user in the system"""
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise ValueError("Email already registered")
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=UserRole[user_data.role.lower()]
    )
    
    db.add(new_user)
    db.commit()
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role.value
    }


def login_user(db: Session, login_data: UserLoginSchema):
    """Authenticate user and return user details"""
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise ValueError("Invalid email or password")
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise ValueError("Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise ValueError("User account is deactivated")
    
    return {
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value
    }