from datetime import date, datetime, timedelta, timezone
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.security import hash_password, token_digest
from .models import (
    AssignmentItem, AssignmentPackage, ClinicalRecord, Department, Patient, QuestionnaireTemplate,
    QuestionnaireVersion, User, UserPermission,
)


DEMO_ACCESS_CODE = "123456"
DEMO_TOKEN = "demo-patient-token"


SCD_SCHEMA = {
    "title": "认知与生活状态演示问卷（非临床）",
    "notice": "本问卷仅用于课程系统演示，不可用于医学诊断。",
    "sections": [{
        "key": "recent_changes", "title": "近期感受",
        "questions": [
            {"key": "memory_change", "type": "yes_no", "label": "最近是否感觉记忆状态发生变化？", "required": True, "dimension": "主观感受",
             "options": [{"value": "no", "label": "否", "score": 0}, {"value": "yes", "label": "是", "score": 1}]},
            {"key": "daily_impact", "type": "scale", "label": "这种变化对日常生活的影响程度？", "required": True, "dimension": "日常影响",
             "options": [{"value": 0, "label": "没有影响", "score": 0}, {"value": 1, "label": "轻微", "score": 1}, {"value": 2, "label": "较明显", "score": 2}, {"value": 3, "label": "严重", "score": 3}]},
            {"key": "example", "type": "long_text", "label": "可以补充一个具体例子", "required": False,
             "show_if": {"question_key": "memory_change", "equals": "yes"}},
        ],
    }],
}


WELLBEING_SCHEMA = {
    "title": "生活与情绪演示问卷（非临床）",
    "notice": "题目为系统功能演示内容，不是正式医学量表。",
    "sections": [{
        "key": "wellbeing", "title": "最近一周",
        "questions": [
            {"key": "sleep_hours", "type": "number", "label": "平均每晚睡眠时长（小时）", "required": True, "min": 0, "max": 24, "dimension": "生活状态", "score_numeric": False},
            {"key": "mood", "type": "scale", "label": "整体情绪状态", "required": True, "dimension": "情绪",
             "options": [{"value": "good", "label": "良好", "score": 0}, {"value": "normal", "label": "一般", "score": 1}, {"value": "low", "label": "较低落", "score": 2}]},
            {"key": "activities", "type": "multi_choice", "label": "经常参加的活动", "required": False,
             "options": [{"value": "walk", "label": "散步", "score": 0}, {"value": "read", "label": "阅读", "score": 0}, {"value": "social", "label": "社交", "score": 0}]},
        ],
    }],
}


def seed_database(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        for user in db.scalars(select(User)).all():
            if not db.get(UserPermission, user.id):
                db.add(UserPermission(user_id=user.id, can_manage_templates=user.role == "admin"))
        demo_patient = db.scalar(select(Patient).where(Patient.patient_code == "P0001"))
        if demo_patient and not db.scalar(select(ClinicalRecord.id).where(ClinicalRecord.patient_id == demo_patient.id).limit(1)):
            now = datetime.now(timezone.utc)
            db.add_all([
                ClinicalRecord(patient_id=demo_patient.id, doctor_id=demo_patient.assigned_doctor_id,
                               record_type="diagnosis", title="首次门诊认知情况记录（演示）",
                               diagnosis_code="DEMO-R41.3", content="患者主诉近期记忆下降。建议结合正式认知量表、实验室检查和影像资料进一步评估；本条为系统演示记录。",
                               event_at=now - timedelta(days=45)),
                ClinicalRecord(patient_id=demo_patient.id, doctor_id=demo_patient.assigned_doctor_id,
                               record_type="follow_up", title="阶段性随访（演示）",
                               content="家属反馈生活自理能力总体稳定，已完成居家安全与规律作息宣教，计划四周后复评。",
                               event_at=now - timedelta(days=14)),
            ])
        db.commit()
        return
    departments = [
        Department(code="NEU", name="神经内科"),
        Department(code="GER", name="老年医学科"),
        Department(code="MEM", name="记忆门诊"),
    ]
    db.add_all(departments)
    db.flush()
    admin = User(username="admin", password_hash=hash_password("Admin123!"), display_name="系统管理员", role="admin", department_id=departments[0].id)
    doctors = [
        User(username=f"doctor{i}", password_hash=hash_password("Doctor123!"), display_name=f"演示医生{i}", role="doctor", department_id=departments[(i - 1) % 3].id)
        for i in range(1, 7)
    ]
    db.add_all([admin, *doctors])
    db.flush()
    db.add(UserPermission(user_id=admin.id, can_manage_templates=True))
    db.add_all([UserPermission(user_id=doctor.id) for doctor in doctors])
    templates = []
    for code, name, description, schema, scoring in [
        ("DEMO_SCD", "认知状态演示问卷", "模拟主观认知变化收集，仅用于系统演示。", SCD_SCHEMA,
         {"strategy": "metadata_sum", "risk_thresholds": [{"min": 0, "level": "low"}, {"min": 2, "level": "medium"}, {"min": 4, "level": "high"}]}),
        ("DEMO_WELLBEING", "生活与情绪演示问卷", "模拟生活和情绪信息收集，仅用于系统演示。", WELLBEING_SCHEMA,
         {"strategy": "metadata_sum", "risk_thresholds": [{"min": 0, "level": "low"}, {"min": 1, "level": "medium"}, {"min": 2, "level": "high"}]}),
    ]:
        template = QuestionnaireTemplate(code=code, name=name, description=description, status="published", created_by_id=admin.id)
        db.add(template)
        db.flush()
        version = QuestionnaireVersion(template_id=template.id, version=1, schema_json=schema, scoring_json=scoring, published_at=datetime.now(timezone.utc))
        db.add(version)
        templates.append((template, version))
    db.flush()
    random.seed(20260827)
    patients = []
    for index in range(1, 101):
        doctor = doctors[(index - 1) % len(doctors)]
        patient = Patient(
            patient_code=f"P{index:04d}", sex="female" if index % 2 else "male",
            birth_date=date(1940 + index % 40, index % 12 + 1, index % 25 + 1),
            education_level=random.choice(["小学及以下", "初中", "高中", "大专及以上"]),
            residence_type=random.choice(["与家人同住", "独居", "养老机构"]),
            department_id=doctor.department_id, assigned_doctor_id=doctor.id,
        )
        db.add(patient)
        patients.append(patient)
    db.flush()
    demo_assignment = AssignmentPackage(
        patient_id=patients[0].id, doctor_id=doctors[0].id, title="首次筛查演示任务",
        note="请根据真实感受填写。本任务内容仅用于课程演示。",
        deadline=datetime.now(timezone.utc) + timedelta(days=30),
        token_hash=token_digest(DEMO_TOKEN), access_code_hash=hash_password(DEMO_ACCESS_CODE),
    )
    db.add(demo_assignment)
    db.flush()
    for _, version in templates:
        db.add(AssignmentItem(assignment_id=demo_assignment.id, questionnaire_version_id=version.id))
    db.add_all([
        ClinicalRecord(patient_id=patients[0].id, doctor_id=doctors[0].id, record_type="diagnosis",
                       title="首次门诊认知情况记录（演示）", diagnosis_code="DEMO-R41.3",
                       content="患者主诉近期记忆下降。建议结合正式认知量表、实验室检查和影像资料进一步评估；本条为系统演示记录。",
                       event_at=datetime.now(timezone.utc) - timedelta(days=45)),
        ClinicalRecord(patient_id=patients[0].id, doctor_id=doctors[0].id, record_type="follow_up",
                       title="阶段性随访（演示）", content="家属反馈生活自理能力总体稳定，已完成居家安全与规律作息宣教，计划四周后复评。",
                       event_at=datetime.now(timezone.utc) - timedelta(days=14)),
    ])
    db.commit()
