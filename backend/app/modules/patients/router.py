from datetime import date

from pydantic import BaseModel, Field
from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.core.api import AppError
from app.modules.assessments.models import Assessment
from app.modules.auth.dependencies import CurrentUser, DbDep
from app.modules.patients.models import Patient
from app.modules.users.models import User


router = APIRouter(prefix="/patients", tags=["患者"])


class PatientPayload(BaseModel):
    patient_code: str = Field(min_length=2, max_length=60)
    display_name: str | None = Field(default=None, max_length=80)
    sex: str | None = None
    birth_date: date | None = None
    education_level: str | None = None
    residence_type: str | None = None
    department_id: int | None = None
    assigned_doctor_id: int | None = None


def scoped_query(user: User):
    query = select(Patient)
    if user.role == "doctor":
        query = query.where(Patient.assigned_doctor_id == user.id)
    return query


@router.get("")
def list_patients(
    user: CurrentUser,
    db: DbDep,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = scoped_query(user).where(Patient.is_active.is_(True))
    if keyword:
        query = query.where(or_(Patient.patient_code.contains(keyword), Patient.display_name.contains(keyword)))
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0
    rows = db.scalars(query.order_by(Patient.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201)
def create_patient(payload: PatientPayload, user: CurrentUser, db: DbDep):
    if db.scalar(select(Patient).where(Patient.patient_code == payload.patient_code)):
        raise AppError(409, "PATIENT_CODE_EXISTS", "患者编码已存在")
    doctor_id = payload.assigned_doctor_id if user.role == "admin" else user.id
    department_id = payload.department_id if user.role == "admin" else user.department_id
    doctor = db.get(User, doctor_id) if doctor_id else None
    if not doctor or doctor.role != "doctor" or not department_id:
        raise AppError(422, "INVALID_OWNER", "必须指定有效的负责医生和科室")
    if user.role == "doctor" and doctor.id != user.id:
        raise AppError(403, "FORBIDDEN", "不能为其他医生创建患者")
    row = Patient(
        patient_code=payload.patient_code,
        display_name=payload.display_name,
        sex=payload.sex,
        birth_date=payload.birth_date,
        education_level=payload.education_level,
        residence_type=payload.residence_type,
        department_id=department_id,
        assigned_doctor_id=doctor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/{patient_id}")
def get_patient(patient_id: int, user: CurrentUser, db: DbDep):
    patient = db.scalar(scoped_query(user).where(Patient.id == patient_id))
    if not patient:
        raise AppError(404, "PATIENT_NOT_FOUND", "患者不存在或无权查看")
    assessments = db.scalars(
        select(Assessment).where(Assessment.patient_id == patient.id).order_by(Assessment.assessed_at.desc())
    ).all()
    result = serialize(patient)
    result["assessments"] = [
        {
            "id": item.id,
            "assessment_code": item.assessment_code,
            "total_score": item.total_score,
            "risk_level": item.risk_level,
            "review_status": item.review_status,
            "assessed_at": item.assessed_at,
            "dimension_scores": item.dimension_scores,
        }
        for item in assessments
    ]
    return result


@router.patch("/{patient_id}")
def update_patient(patient_id: int, payload: PatientPayload, user: CurrentUser, db: DbDep):
    patient = db.scalar(scoped_query(user).where(Patient.id == patient_id))
    if not patient:
        raise AppError(404, "PATIENT_NOT_FOUND", "患者不存在或无权修改")
    for field in ("display_name", "sex", "birth_date", "education_level", "residence_type"):
        setattr(patient, field, getattr(payload, field))
    if user.role == "admin":
        if payload.department_id:
            patient.department_id = payload.department_id
        if payload.assigned_doctor_id:
            patient.assigned_doctor_id = payload.assigned_doctor_id
    db.commit()
    return serialize(patient)


def serialize(patient: Patient) -> dict:
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "display_name": patient.display_name,
        "sex": patient.sex,
        "birth_date": patient.birth_date,
        "education_level": patient.education_level,
        "residence_type": patient.residence_type,
        "department_id": patient.department_id,
        "assigned_doctor_id": patient.assigned_doctor_id,
        "created_at": patient.created_at,
    }

