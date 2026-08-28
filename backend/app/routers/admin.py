from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user
from ..models import AuditLog, Department, User


router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/departments")
def departments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": d.id, "code": d.code, "name": d.name, "active": d.active}
            for d in db.scalars(select(Department).order_by(Department.name)).all()]


@router.get("/users")
def users(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [{
        "id": u.id, "username": u.username, "display_name": u.display_name,
        "role": u.role, "department_id": u.department_id,
        "department_name": u.department.name if u.department else None, "active": u.active,
    } for u in db.scalars(select(User).order_by(User.role, User.display_name)).all()]


@router.get("/audit")
def audit_logs(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    _: User = Depends(admin_user), db: Session = Depends(get_db),
):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return [{
        "id": row.id, "actor_type": row.actor_type, "actor_id": row.actor_id,
        "action": row.action, "target_type": row.target_type,
        "target_id": row.target_id, "result": row.result, "created_at": row.created_at,
    } for row in rows]

