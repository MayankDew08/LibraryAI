import bcrypt

def hash_password(password: str) -> str:
    # Convert to uppercase and truncate to 72 bytes for bcrypt
    password_upper = password.upper()
    password_bytes = password_upper.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    # Convert to uppercase and truncate to 72 bytes for bcrypt
    password_upper = plain.upper()
    password_bytes = password_upper.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

