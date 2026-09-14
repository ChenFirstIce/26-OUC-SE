from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import User, UserPermission


PERMISSION_FIELDS = (
    "can_create_patients",
    "can_assign_questionnaires",
    "can_review_results",
    "can_manage_templates",
)


def permission_for(db: Session, user: User) -> UserPermission:
    permission = db.get(UserPermission, user.id)
    if permission:
        return permission
    permission = UserPermission(
        user_id=user.id,
        can_create_patients=True,
        can_assign_questionnaires=True,
        can_review_results=True,
        can_manage_templates=user.role == "admin",
    )
    db.add(permission)
    db.flush()
    return permission


def permission_view(permission: UserPermission) -> dict[str, bool]:
    return {field: bool(getattr(permission, field)) for field in PERMISSION_FIELDS}


def require_permission(db: Session, user: User, field: str) -> None:
    if user.role == "admin":
        return
    if field not in PERMISSION_FIELDS or not getattr(permission_for(db, user), field):
        raise HTTPException(status_code=403, detail="管理员未授予当前操作权限")
