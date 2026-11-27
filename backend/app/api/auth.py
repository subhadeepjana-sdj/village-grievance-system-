from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.mongodb import mongodb_service
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserOut
from app.services.notification_service import record_failed_login, clear_failed_logins, notify_event
from app.models.notification import NotificationCategory, NotificationSeverity
from app.utils.security import verify_password, get_password_hash, create_access_token, decode_access_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _sync_user_from_mongo(email: str, db: Session) -> Optional[User]:
    """Hydrate a registered user from MongoDB into local SQLite when running across serverless containers."""
    if not email or not mongodb_service.connected:
        return None
    doc = mongodb_service.get_user_by_email(email)
    if not doc:
        return None
    role_val = str(doc.get("role") or "CITIZEN").upper()
    role_enum = UserRole[role_val] if role_val in UserRole.__members__ else UserRole.CITIZEN
    user = User(
        name=doc.get("name") or email.split("@")[0],
        phone=doc.get("phone"),
        email=doc["email"],
        password_hash=doc.get("password_hash") or "",
        role=role_enum,
        village_id=doc.get("village_id"),
        department_id=doc.get("department_id"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mirror_user_to_mongo(user: User) -> None:
    mongodb_service.upsert_user({
        "user_id": user.id,
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "password_hash": user.password_hash,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "village_id": user.village_id,
        "department_id": user.department_id,
    })


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("email")
    if email is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = _sync_user_from_mongo(email, db)
    if user is None:
        raise credentials_exception
    return user

def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    email: str = payload.get("email")
    if not email:
        return None
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = _sync_user_from_mongo(email, db)
    return user

@router.post("/register", response_model=UserOut)
def register(user_in: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if not existing:
        existing = _sync_user_from_mongo(user_in.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    user = User(
        name=user_in.name,
        phone=user_in.phone,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role or UserRole.CITIZEN,
        village_id=user_in.village_id,
        department_id=user_in.department_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _mirror_user_to_mongo(user)
    if user.role != UserRole.CITIZEN:
        notify_event(
            db,
            title="Privileged role account created",
            message=f"New account '{user.email}' registered with role {user.role.value}.",
            category=NotificationCategory.SECURITY.value,
            severity=NotificationSeverity.INFO.value,
            action_url="/admin/ai-monitoring",
            action_label="Review security event",
            requires_action=False,
            group_key=f"security:role_created:{user.email}",
        )
    return user

@router.post("/login", response_model=Token)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user:
        user = _sync_user_from_mongo(login_in.email, db)
    if not user or not verify_password(login_in.password, user.password_hash):
        record_failed_login(db, login_in.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    clear_failed_logins(login_in.email)
    _mirror_user_to_mongo(user)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value, "user_id": user.id}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    }
