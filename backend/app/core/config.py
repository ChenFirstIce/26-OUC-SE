from dataclasses import dataclass
from pathlib import Path
import os
import tempfile


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "阿尔茨海默症筛查问卷与数据统计系统"
    api_prefix: str = "/api/v1"
    # 当前 Windows Python 运行时无法让 SQLite 打开中文工作目录，因此默认数据文件放在
    # 当前用户临时数据目录；可通过 DATABASE_URL 切换到 PostgreSQL 或其他 ASCII 路径。
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(Path(tempfile.gettempdir()) / 'ad_questionnaire_data' / 'ad_questionnaire.db').as_posix()}",
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-change-before-deployment")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
    patient_session_minutes: int = int(os.getenv("PATIENT_SESSION_MINUTES", "120"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")


settings = Settings()
