import os
import sys
import hashlib
import datetime
from typing import Optional

user_site = os.path.expanduser(r"~\AppData\Roaming\Python\Python314\site-packages")
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

from jose import jwt, JWTError
from app.config import settings

def get_password_hash(password: str) -> str:
    try:
        import bcrypt
        if isinstance(password, str):
            pw_bytes = password.encode('utf-8')[:72]
        else:
            pw_bytes = password[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')
    except Exception:
        # Fallback SHA-256 salted hash
        salt = "village_secret_salt_2026"
        return "sha256$" + hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        import bcrypt
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            pw_bytes = plain_password.encode('utf-8')[:72]
            return bcrypt.checkpw(pw_bytes, hashed_password.encode('utf-8'))
    except Exception:
        pass

    if hashed_password.startswith("sha256$"):
        salt = "village_secret_salt_2026"
        calc = "sha256$" + hashlib.sha256((salt + plain_password).encode('utf-8')).hexdigest()
        return calc == hashed_password

    # Simple fallback check
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
