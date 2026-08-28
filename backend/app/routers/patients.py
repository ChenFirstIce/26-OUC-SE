from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import current_user, ensure_patient_scope
from ..models import Assessment, Patient, User
from ..services.audit import audit


router = APIRouter(prefix="/patients", tags=["患者"])


class PatientInput(BaseModel):
    patient_code: str = Field(min_length=2, max_length=40)
    sex: str | None = None
    birth_date: date | None = None
    education_level: str | None = None
    residence_type: str | None = None


def patient_view(patient: Patient) -> dict:
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "sex": patient.sex,
        "birth_date": patient.birth_date,
        "education_level": patient.education_level,
        "residence_type": patient.residence_type,
        "department_id": patient.department_id,
        "department_name": patient.department.name,
        "assigned_doctor_id": patient.assigned_doctor_id,
        "doctor_name": patient.assigned_doctor.display_name,
        "created_at": patient.created_at,
    }


@router.get("")
def list_patients(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    keyword: str = "", user: User = Depends(current_user), db: Session = Depends(get_db),
):
    query = select(Patient).where(Patient.active.is_(True))
    count_query = select(func.count()).select_from(Patient).where(Patient.active.is_(True))
    if user.role != "admin":
        query = query.where(Patient.assigned_doctor_id == user.id)
        count_query = count_query.where(Patient.assigned_doctor_id == user.id)
    if keyword:
        query = query.where(Patient.patient_code.contains(keyword))
        count_query = count_query.where(Patient.patient_code.contains(keyword))
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(Patient.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [patient_view(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201)
def create_patient(payload: PatientInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == "admin" and not user.department_id:
        raise HTTPException(status_code=422, detail="管理员账号未绑定科室，不能直接创建患者")
    if db.scalar(select(Patient).where(Patient.patient_code == payload.patient_code)):
        raise HTTPException(status_code=409, detail="患者编码已存在")
    patient = Patient(**payload.model_dump(), department_id=user.department_id, assigned_doctor_id=user.id)
    db.add(patient)
    db.flush()
    audit(db, "user", user.id, "patient.create", "patient", patient.id)
    db.commit()
    db.refresh(patient)
    return patient_view(patient)


@router.get("/{patient_id}")
def get_patient(patient_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    ensure_patient_scope(user, patient.assigned_doctor_id)
    data = patient_view(patient)
    assessments = db.scalars(select(Assessment).where(Assessment.patient_id == patient_id).order_by(Assessment.assessed_at.desc())).all()
    data["assessments"] = [{
        "id": a.id, "questionnaire_code": a.questionnaire_code, "total_score": a.total_score,
        "dimension_scores": a.dimension_scores, "risk_level": a.risk_level,
        "review_status": a.review_status, "assessed_at": a.assessed_at,
    } for a in assessments]
    return data

