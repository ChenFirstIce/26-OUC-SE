import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import current_user
from ..models import Assessment, AssignmentItem, AssignmentPackage, Patient, QuestionnaireTemplate, QuestionnaireVersion, User
from ..services.audit import audit


router = APIRouter(tags=["统计"])


def patient_scope(query, user: User, doctor_column):
    return query if user.role == "admin" else query.where(doctor_column == user.id)


@router.get("/statistics/overview")
def overview(user: User = Depends(current_user), db: Session = Depends(get_db)):
    patient_query = patient_scope(select(func.count(Patient.id)), user, Patient.assigned_doctor_id)
    assignment_query = patient_scope(select(func.count(AssignmentPackage.id)), user, AssignmentPackage.doctor_id)
    assessment_query = patient_scope(select(func.count(Assessment.id)), user, Assessment.doctor_id)
    high_query = patient_scope(select(func.count(distinct(Assessment.patient_id))).where(Assessment.risk_level == "high"), user, Assessment.doctor_id)
    assessed_patient_query = patient_scope(select(func.count(distinct(Assessment.patient_id))), user, Assessment.doctor_id)
    patient_count = db.scalar(patient_query) or 0
    assignment_count = db.scalar(assignment_query) or 0
    assessment_count = db.scalar(assessment_query) or 0
    high_risk = db.scalar(high_query) or 0
    assessed_patients = db.scalar(assessed_patient_query) or 0
    return {
        "patient_count": patient_count, "assignment_count": assignment_count,
        "assessment_count": assessment_count, "high_risk_patients": high_risk,
        "high_risk_rate": round(high_risk / assessed_patients * 100, 1) if assessed_patients else 0,
        "pending_review": db.scalar(patient_scope(select(func.count(Assessment.id)).where(Assessment.review_status == "pending"), user, Assessment.doctor_id)) or 0,
    }


@router.get("/statistics/funnel")
def funnel(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(AssignmentPackage.status, func.count(AssignmentPackage.id)).group_by(AssignmentPackage.status)
    query = patient_scope(query, user, AssignmentPackage.doctor_id)
    counts = dict(db.execute(query).all())
    total = sum(counts.values())
    submitted = counts.get("submitted", 0) + counts.get("reviewed", 0)
    return {"counts": counts, "total": total, "completion_rate": round(submitted / total * 100, 1) if total else 0}


@router.get("/statistics/questionnaires")
def questionnaire_stats(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = (
        select(QuestionnaireTemplate.name, func.count(AssignmentItem.id),
               func.sum(case((AssignmentItem.status.in_(["submitted", "reviewed"]), 1), else_=0)))
        .join(QuestionnaireVersion, QuestionnaireVersion.template_id == QuestionnaireTemplate.id)
        .join(AssignmentItem, AssignmentItem.questionnaire_version_id == QuestionnaireVersion.id)
        .join(AssignmentPackage, AssignmentPackage.id == AssignmentItem.assignment_id)
        .group_by(QuestionnaireTemplate.name)
    )
    query = patient_scope(query, user, AssignmentPackage.doctor_id)
    return [{"name": name, "assigned": assigned, "submitted": submitted or 0,
             "completion_rate": round((submitted or 0) / assigned * 100, 1) if assigned else 0}
            for name, assigned, submitted in db.execute(query).all()]


@router.get("/statistics/risks")
def risks(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Assessment.risk_level, func.count(Assessment.id)).group_by(Assessment.risk_level)
    query = patient_scope(query, user, Assessment.doctor_id)
    return [{"level": level, "count": count} for level, count in db.execute(query).all()]


@router.get("/statistics/score-summary")
def score_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = (
        select(
            Assessment.questionnaire_code,
            QuestionnaireTemplate.name,
            func.count(Assessment.id),
            func.avg(Assessment.total_score),
            func.min(Assessment.total_score),
            func.max(Assessment.total_score),
            func.sum(case((Assessment.risk_level == "high", 1), else_=0)),
            func.sum(case((Assessment.risk_level == "medium", 1), else_=0)),
        )
        .join(QuestionnaireTemplate, QuestionnaireTemplate.code == Assessment.questionnaire_code)
        .group_by(Assessment.questionnaire_code, QuestionnaireTemplate.name)
        .order_by(func.count(Assessment.id).desc())
    )
    query = patient_scope(query, user, Assessment.doctor_id)
    return [{
        "questionnaire_code": code, "questionnaire_name": name, "assessment_count": count,
        "average_score": round(float(average), 2) if average is not None else None,
        "minimum_score": minimum, "maximum_score": maximum,
        "high_risk_count": high_count or 0, "medium_risk_count": medium_count or 0,
    } for code, name, count, average, minimum, maximum, high_count, medium_count in db.execute(query).all()]


@router.get("/exports/assessments.csv")
def export_assessments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Assessment, Patient.patient_code).join(Patient, Patient.id == Assessment.patient_id).order_by(Assessment.assessed_at.desc())
    query = patient_scope(query, user, Assessment.doctor_id)
    rows = db.execute(query).all()
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(["patient_code", "questionnaire_code", "total_score", "risk_level", "review_status", "assessed_at"])
    for assessment, patient_code in rows:
        writer.writerow([patient_code, assessment.questionnaire_code, assessment.total_score, assessment.risk_level, assessment.review_status, assessment.assessed_at.isoformat()])
    audit(db, "user", user.id, "assessment.export", "assessment", "filtered")
    db.commit()
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=assessments.csv"})
