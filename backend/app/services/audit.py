from sqlalchemy.orm import Session

from ..models import AuditLog


def audit(db: Session, actor_type: str, actor_id: str | int, action: str, target_type: str, target_id: str | int) -> None:
    db.add(AuditLog(
        actor_type=actor_type,
        actor_id=str(actor_id),
        action=action,
        target_type=target_type,
        target_id=str(target_id),
    ))

