from pydantic import BaseModel, Field
from fastapi import APIRouter
from sqlalchemy import select

from app.core.api import AppError
from app.modules.auth.dependencies import AdminUser, CurrentUser, DbDep
from app.modules.departments.models import Department


router = APIRouter(prefix="/departments", tags=["科室"])


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=100)


@router.get("")
def list_departments(_: CurrentUser, db: DbDep):
    rows = db.scalars(select(Department).where(Department.is_active.is_(True)).order_by(Department.name)).all()
    return [{"id": row.id, "code": row.code, "name": row.name} for row in rows]


@router.post("", status_code=201)
def create_department(payload: DepartmentCreate, _: AdminUser, db: DbDep):
    if db.scalar(select(Department).where(Department.code == payload.code)):
        raise AppError(409, "DEPARTMENT_EXISTS", "科室编码已存在")
    row = Department(code=payload.code, name=payload.name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name}

