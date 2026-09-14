from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user
from ..core.security import hash_password
from ..models import AuditLog, Department, User
from ..services.audit import audit
from ..services.permissions import PERMISSION_FIELDS, permission_for, permission_view

router = APIRouter(prefix="/admin", tags=["管理"])


class DepartmentInput(BaseModel):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=80)
    active: bool = True


class UserCreateInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    display_name: str = Field(min_length=2, max_length=80)
    role: str = Field(pattern=r"^(doctor|admin)$")
    department_id: int | None = None
    active: bool = True
    permissions: dict[str, bool] = {}


class UserUpdateInput(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    role: str | None = Field(default=None, pattern=r"^(doctor|admin)$")
    department_id: int | None = None
    active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=100)
    permissions: dict[str, bool] | None = None


def department_view(department: Department) -> dict:
    return {"id": department.id, "code": department.code, "name": department.name, "active": department.active}


def user_view(db: Session, user: User) -> dict:
    return {
        "id": user.id, "username": user.username, "display_name": user.display_name,
        "role": user.role, "department_id": user.department_id,
        "department_name": user.department.name if user.department else None, "active": user.active,
        "permissions": permission_view(permission_for(db, user)),
    }


@router.get("/departments")
def departments(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [department_view(d) for d in db.scalars(select(Department).order_by(Department.name)).all()]


@router.post("/departments", status_code=201)
def create_department(payload: DepartmentInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    if db.scalar(select(Department).where(Department.code == payload.code.upper())):
        raise HTTPException(status_code=409, detail="科室编码已存在")
    department = Department(code=payload.code.upper(), name=payload.name, active=payload.active)
    db.add(department); db.flush()
    audit(db, "user", user.id, "department.create", "department", department.id)
    db.commit(); db.refresh(department)
    return department_view(department)


@router.patch("/departments/{department_id}")
def update_department(department_id: int, payload: DepartmentInput, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="科室不存在")
    duplicate = db.scalar(select(Department).where(Department.code == payload.code.upper(), Department.id != department_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="科室编码已存在")
    department.code, department.name, department.active = payload.code.upper(), payload.name, payload.active
    audit(db, "user", user.id, "department.update", "department", department.id)
    db.commit()
    return department_view(department)


@router.get("/users")
def users(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [user_view(db, row) for row in db.scalars(select(User).order_by(User.role, User.display_name)).all()]


@router.post("/users", status_code=201)
def create_user(payload: UserCreateInput, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="登录账号已存在")
    if payload.department_id and not db.get(Department, payload.department_id):
        raise HTTPException(status_code=422, detail="科室不存在")
    user = User(username=payload.username, password_hash=hash_password(payload.password), display_name=payload.display_name,
                role=payload.role, department_id=payload.department_id, active=payload.active)
    db.add(user); db.flush()
    permission = permission_for(db, user)
    for field, value in payload.permissions.items():
        if field in PERMISSION_FIELDS:
            setattr(permission, field, value)
    audit(db, "user", actor.id, "user.create", "user", user.id)
    db.commit(); db.refresh(user)
    return user_view(db, user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdateInput, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.id == actor.id and payload.active is False:
        raise HTTPException(status_code=409, detail="不能停用当前登录账号")
    fields = payload.model_fields_set
    if "department_id" in fields and payload.department_id and not db.get(Department, payload.department_id):
        raise HTTPException(status_code=422, detail="科室不存在")
    for field in ("display_name", "role", "department_id", "active"):
        if field in fields:
            setattr(user, field, getattr(payload, field))
    if payload.new_password:
        user.password_hash = hash_password(payload.new_password)
    if payload.permissions is not None:
        permission = permission_for(db, user)
        for field, value in payload.permissions.items():
            if field in PERMISSION_FIELDS:
                setattr(permission, field, value)
    audit(db, "user", actor.id, "user.update", "user", user.id)
    db.commit()
    return user_view(db, user)


@router.get("/audit")
def audit_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
               _: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return [{"id": row.id, "actor_type": row.actor_type, "actor_id": row.actor_id, "action": row.action,
             "target_type": row.target_type, "target_id": row.target_id, "result": row.result,
             "created_at": row.created_at} for row in rows]
