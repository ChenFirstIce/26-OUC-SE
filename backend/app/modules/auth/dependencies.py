from typing import Annotated

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.api import AppError
from app.core.db import get_db
from app.core.security import decode_token
from app.modules.users.models import User


bearer = HTTPBearer(auto_error=False)
DbDep = Annotated[Session, Depends(get_db)]


def current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if not credentials:
        raise AppError(401, "UNAUTHENTICATED", "请先登录")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") not in {"admin", "doctor"}:
            raise ValueError
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise AppError(401, "INVALID_TOKEN", "登录状态无效或已过期") from None
    if not user or not user.is_active:
        raise AppError(401, "USER_DISABLED", "账号不存在或已停用")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise AppError(403, "FORBIDDEN", "需要管理员权限")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def patient_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    x_assignment_token: Annotated[str | None, Header()] = None,
) -> dict:
    raw = credentials.credentials if credentials else x_assignment_token
    if not raw:
        raise AppError(401, "PATIENT_SESSION_REQUIRED", "请先验证访问码")
    try:
        payload = decode_token(raw)
        if payload.get("role") != "patient-link":
            raise ValueError
        return payload
    except (jwt.PyJWTError, ValueError):
        raise AppError(401, "INVALID_PATIENT_SESSION", "填写会话无效或已过期") from None


PatientClaims = Annotated[dict, Depends(patient_claims)]

