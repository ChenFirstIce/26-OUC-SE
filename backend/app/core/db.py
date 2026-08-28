from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    # Importing registers every table with SQLAlchemy metadata.
    from app.modules.assessments import models as _assessment_models  # noqa: F401
    from app.modules.assignments import models as _assignment_models  # noqa: F401
    from app.modules.audit import models as _audit_models  # noqa: F401
    from app.modules.departments import models as _department_models  # noqa: F401
    from app.modules.patients import models as _patient_models  # noqa: F401
    from app.modules.questionnaires import models as _questionnaire_models  # noqa: F401
    from app.modules.users import models as _user_models  # noqa: F401

    Base.metadata.create_all(bind=engine)

