from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select

from app.core.api import AppError
from app.core.security import create_token, verify_password
from app.modules.auth.dependencies import CurrentUser, DbDep
from app.modules.audit.models import AuditLog
from app.modules.users.models import User


router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, db: DbDep):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "用户名或密码错误")
    token = create_token(str(user.id), user.role)
    db.add(AuditLog(user_id=user.id, action="login", target_type="user", target_id=str(user.id)))
    db.commit()
    return {"access_token": token, "token_type": "bearer", "user": serialize_user(user)}


@router.get("/me")
def me(user: CurrentUser):
    return serialize_user(user)


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
    }

