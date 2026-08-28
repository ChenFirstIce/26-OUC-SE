from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models import User
from .database import get_db
from .security import decode_token


bearer = HTTPBearer(auto_error=False)


@dataclass
class PatientIdentity:
    assignment_id: int


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") not in {"admin", "doctor"}:
            raise ValueError
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效") from None
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号已停用")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def patient_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> PatientIdentity:
    if not credentials:
        raise HTTPException(status_code=401, detail="请先验证访问码")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("role") != "patient-link":
            raise ValueError
        return PatientIdentity(assignment_id=int(payload["assignment_id"]))
    except Exception:
        raise HTTPException(status_code=401, detail="患者填写会话无效或已过期") from None


def ensure_patient_scope(user: User, doctor_id: int) -> None:
    if user.role != "admin" and user.id != doctor_id:
        raise HTTPException(status_code=403, detail="无权访问该患者")

