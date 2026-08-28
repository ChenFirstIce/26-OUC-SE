from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AssignmentItem, AssignmentPackage


def is_expired(assignment: AssignmentPackage) -> bool:
    if not assignment.deadline:
        return False
    deadline = assignment.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)


def refresh_assignment_status(db: Session, assignment: AssignmentPackage) -> None:
    if assignment.status == "revoked":
        return
    if is_expired(assignment) and assignment.status not in {"submitted", "reviewed"}:
        assignment.status = "expired"
        return
    statuses = list(db.scalars(select(AssignmentItem.status).where(AssignmentItem.assignment_id == assignment.id)))
    if statuses and all(status in {"submitted", "reviewed"} for status in statuses):
        assignment.status = "submitted" if any(status == "submitted" for status in statuses) else "reviewed"
    elif any(status == "draft" for status in statuses):
        assignment.status = "in_progress"
    else:
        assignment.status = "pending"

