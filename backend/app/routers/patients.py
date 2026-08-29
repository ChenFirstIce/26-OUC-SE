from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import admin_user, current_user, ensure_patient_scope
from ..models import Assessment, AssignmentPackage, ClinicalRecord, Patient, PatientProfile, User
from ..services.audit import audit
from ..services.permissions import require_permission

router = APIRouter(prefix="/patients", tags=["患者"])


class PatientInput(BaseModel):
    patient_code: str = Field(min_length=2, max_length=40)
    full_name: str = Field(min_length=2, max_length=80)
    sex: str | None = None
    birth_date: date | None = None
    education_level: str | None = None
    residence_type: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    marital_status: str | None = Field(default=None, max_length=30)
    occupation: str | None = Field(default=None, max_length=80)
    chief_concern: str | None = Field(default=None, max_length=2000)
    past_medical_history: str | None = Field(default=None, max_length=5000)
    family_history: str | None = Field(default=None, max_length=5000)
    current_medications: str | None = Field(default=None, max_length=5000)
    allergy_history: str | None = Field(default=None, max_length=5000)
    emergency_contact: str | None = Field(default=None, max_length=80)
    emergency_phone: str | None = Field(default=None, max_length=30)


class PatientUpdateInput(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=80)
    sex: str | None = Field(default=None, pattern=r"^(male|female|other)$")
    birth_date: date | None = None
    education_level: str | None = Field(default=None, max_length=50)
    residence_type: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    marital_status: str | None = Field(default=None, max_length=30)
    occupation: str | None = Field(default=None, max_length=80)
    chief_concern: str | None = Field(default=None, max_length=2000)
    past_medical_history: str | None = Field(default=None, max_length=5000)
    family_history: str | None = Field(default=None, max_length=5000)
    current_medications: str | None = Field(default=None, max_length=5000)
    allergy_history: str | None = Field(default=None, max_length=5000)
    emergency_contact: str | None = Field(default=None, max_length=80)
    emergency_phone: str | None = Field(default=None, max_length=30)


PROFILE_FIELDS = {
    "full_name", "phone", "marital_status", "occupation", "chief_concern",
    "past_medical_history", "family_history", "current_medications",
    "allergy_history", "emergency_contact", "emergency_phone",
}


class ClinicalRecordInput(BaseModel):
    record_type: str = Field(pattern=r"^(diagnosis|follow_up|treatment|note)$")
    title: str = Field(min_length=2, max_length=120)
    diagnosis_code: str | None = Field(default=None, max_length=40)
    content: str = Field(min_length=2, max_length=5000)
    event_at: datetime | None = None


class ClinicalRecordUpdate(ClinicalRecordInput):
    status: str = Field(default="active", pattern=r"^(active|archived)$")


def patient_view(patient: Patient) -> dict:
    profile = patient.profile
    age = None
    if patient.birth_date:
        today = date.today()
        age = today.year - patient.birth_date.year - ((today.month, today.day) < (patient.birth_date.month, patient.birth_date.day))
    return {
        "id": patient.id, "patient_code": patient.patient_code, "sex": patient.sex,
        "full_name": profile.full_name if profile else None, "age": age,
        "birth_date": patient.birth_date, "education_level": patient.education_level,
        "residence_type": patient.residence_type, "department_id": patient.department_id,
        "department_name": patient.department.name, "assigned_doctor_id": patient.assigned_doctor_id,
        "doctor_name": patient.assigned_doctor.display_name, "created_at": patient.created_at,
        **{field: getattr(profile, field) if profile else None for field in PROFILE_FIELDS if field != "full_name"},
    }


def assessment_view(row: Assessment) -> dict:
    return {"id": row.id, "questionnaire_code": row.questionnaire_code, "total_score": row.total_score,
            "dimension_scores": row.dimension_scores, "risk_level": row.risk_level,
            "review_status": row.review_status, "assessed_at": row.assessed_at}


def clinical_record_view(row: ClinicalRecord) -> dict:
    return {"id": row.id, "patient_id": row.patient_id, "doctor_id": row.doctor_id,
            "doctor_name": row.doctor.display_name, "record_type": row.record_type, "title": row.title,
            "diagnosis_code": row.diagnosis_code, "content": row.content, "event_at": row.event_at,
            "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at}


def scoped_patient(db: Session, patient_id: int, user: User) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    ensure_patient_scope(user, patient.assigned_doctor_id)
    return patient


@router.get("")
def list_patients(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), keyword: str = "",
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Patient).outerjoin(PatientProfile).where(Patient.active.is_(True))
    count_query = select(func.count()).select_from(Patient).outerjoin(PatientProfile).where(Patient.active.is_(True))
    if user.role != "admin":
        query = query.where(Patient.assigned_doctor_id == user.id)
        count_query = count_query.where(Patient.assigned_doctor_id == user.id)
    if keyword:
        keyword_filter = or_(Patient.patient_code.contains(keyword), PatientProfile.full_name.contains(keyword))
        query = query.where(keyword_filter); count_query = count_query.where(keyword_filter)
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(Patient.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [patient_view(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201)
def create_patient(payload: PatientInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "can_create_patients")
    if not user.department_id:
        raise HTTPException(status_code=422, detail="账号未绑定科室，不能直接创建患者")
    if db.scalar(select(Patient).where(Patient.patient_code == payload.patient_code)):
        raise HTTPException(status_code=409, detail="患者编码已存在")
    values = payload.model_dump()
    profile_values = {field: values.pop(field) for field in PROFILE_FIELDS}
    patient = Patient(**values, department_id=user.department_id, assigned_doctor_id=user.id)
    db.add(patient); db.flush(); audit(db, "user", user.id, "patient.create", "patient", patient.id)
    db.add(PatientProfile(patient_id=patient.id, **profile_values))
    db.commit(); db.refresh(patient)
    return patient_view(patient)


@router.patch("/{patient_id}")
def update_patient(patient_id: int, payload: PatientUpdateInput,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, user, "can_create_patients")
    patient = scoped_patient(db, patient_id, user)
    profile = patient.profile or PatientProfile(patient_id=patient.id)
    if not patient.profile:
        db.add(profile)
    for field in payload.model_fields_set:
        if field in PROFILE_FIELDS:
            setattr(profile, field, getattr(payload, field))
        else:
            setattr(patient, field, getattr(payload, field))
    audit(db, "user", user.id, "patient.update", "patient", patient.id)
    db.commit(); db.refresh(patient)
    return patient_view(patient)


@router.delete("/{patient_id}")
def archive_patient(patient_id: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    patient.active = False
    assignments = db.scalars(select(AssignmentPackage).where(AssignmentPackage.patient_id == patient_id)).all()
    for assignment in assignments:
        if assignment.status in {"pending", "in_progress"}:
            assignment.status = "revoked"
    audit(db, "user", user.id, "patient.archive", "patient", patient.id)
    db.commit()
    return {"status": "archived", "patient_id": patient.id}


@router.get("/{patient_id}")
def get_patient(patient_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    patient = scoped_patient(db, patient_id, user)
    data = patient_view(patient)
    assessments = db.scalars(select(Assessment).where(Assessment.patient_id == patient_id).order_by(Assessment.assessed_at.desc())).all()
    data["assessments"] = [assessment_view(row) for row in assessments]
    return data


@router.get("/{patient_id}/analysis")
def patient_analysis(patient_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    patient = scoped_patient(db, patient_id, user)
    assessments = db.scalars(select(Assessment).where(Assessment.patient_id == patient_id).order_by(Assessment.assessed_at)).all()
    assignments = db.scalars(select(AssignmentPackage).where(AssignmentPackage.patient_id == patient_id).order_by(AssignmentPackage.created_at.desc())).all()
    records = db.scalars(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient_id, ClinicalRecord.status == "active").order_by(ClinicalRecord.event_at.desc())).all()
    latest_by_scale: dict[str, Assessment] = {}
    for row in assessments:
        latest_by_scale[row.questionnaire_code] = row
    risk_counts = {level: sum(1 for row in assessments if row.risk_level == level) for level in ("low", "medium", "high", "unknown")}
    completed = sum(1 for row in assignments if row.status in {"submitted", "reviewed"})
    age = None
    if patient.birth_date:
        today = date.today(); age = today.year - patient.birth_date.year - ((today.month, today.day) < (patient.birth_date.month, patient.birth_date.day))
    return {
        "patient": patient_view(patient), "age": age, "assessment_count": len(assessments),
        "assignment_count": len(assignments), "completion_rate": round(completed * 100 / len(assignments), 1) if assignments else 0,
        "latest_risk": assessments[-1].risk_level if assessments else "unknown", "risk_counts": risk_counts,
        "trend": [assessment_view(row) for row in assessments],
        "latest_by_scale": [assessment_view(row) for row in latest_by_scale.values()],
        "assignments": [{"id": row.id, "title": row.title, "status": row.status, "doctor_name": row.doctor.display_name,
                         "deadline": row.deadline, "created_at": row.created_at} for row in assignments],
        "recent_records": [clinical_record_view(row) for row in records[:5]],
    }


@router.get("/{patient_id}/clinical-records")
def list_clinical_records(patient_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    scoped_patient(db, patient_id, user); require_permission(db, user, "can_review_results")
    rows = db.scalars(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient_id).order_by(ClinicalRecord.event_at.desc())).all()
    return [clinical_record_view(row) for row in rows]


@router.post("/{patient_id}/clinical-records", status_code=201)
def create_clinical_record(patient_id: int, payload: ClinicalRecordInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    scoped_patient(db, patient_id, user); require_permission(db, user, "can_review_results")
    row = ClinicalRecord(patient_id=patient_id, doctor_id=user.id, event_at=payload.event_at or datetime.now(timezone.utc),
                         **payload.model_dump(exclude={"event_at"}))
    db.add(row); db.flush(); audit(db, "user", user.id, "clinical_record.create", "clinical_record", row.id)
    db.commit(); db.refresh(row)
    return clinical_record_view(row)


@router.patch("/{patient_id}/clinical-records/{record_id}")
def update_clinical_record(patient_id: int, record_id: int, payload: ClinicalRecordUpdate,
                           user: User = Depends(current_user), db: Session = Depends(get_db)):
    scoped_patient(db, patient_id, user); require_permission(db, user, "can_review_results")
    row = db.get(ClinicalRecord, record_id)
    if not row or row.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="临床记录不存在")
    if user.role != "admin" and row.doctor_id != user.id:
        raise HTTPException(status_code=403, detail="只能修改本人创建的记录")
    for field, value in payload.model_dump().items():
        setattr(row, field, value or (datetime.now(timezone.utc) if field == "event_at" else value))
    audit(db, "user", user.id, "clinical_record.update", "clinical_record", row.id)
    db.commit()
    return clinical_record_view(row)
