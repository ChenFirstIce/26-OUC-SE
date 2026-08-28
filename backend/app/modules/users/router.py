from pydantic import BaseModel, Field
from fastapi import APIRouter
from sqlalchemy import select

from app.core.api import AppError
from app.core.security import hash_password
from app.modules.auth.dependencies import AdminUser, DbDep
from app.modules.departments.models import Department
from app.modules.users.models import User


router = APIRouter(prefix="/users", tags=["用户管理"])


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=8, max_length=100)
    display_name: str = Field(min_length=2, max_length=100)
    role: str = "doctor"
    department_id: int | None = None


@router.get("")
def list_users(_: AdminUser, db: DbDep):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [serialize(item) for item in users]


@router.post("", status_code=201)
def create_user(payload: UserCreate, _: AdminUser, db: DbDep):
    if payload.role not in {"admin", "doctor"}:
        raise AppError(422, "INVALID_ROLE", "角色只能是 admin 或 doctor")
    if db.scalar(select(User).where(User.username == payload.username)):
        raise AppError(409, "USERNAME_EXISTS", "用户名已存在")
    if payload.department_id and not db.get(Department, payload.department_id):
        raise AppError(422, "DEPARTMENT_NOT_FOUND", "科室不存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
        department_id=payload.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize(user)


@router.patch("/{user_id}/status")
def update_status(user_id: int, is_active: bool, admin: AdminUser, db: DbDep):
    if user_id == admin.id and not is_active:
        raise AppError(422, "CANNOT_DISABLE_SELF", "不能停用当前管理员账号")
    user = db.get(User, user_id)
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "用户不存在")
    user.is_active = is_active
    db.commit()
    return serialize(user)


def serialize(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
        "is_active": user.is_active,
    }

