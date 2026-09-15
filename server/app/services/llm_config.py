from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import LlmProviderConfig, User


class LlmConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeepSeekCredentials:
    api_key: str
    base_url: str
    model: str


def _fernet() -> Fernet:
    if not settings.llm_secret_key:
        raise LlmConfigError("LLM_SECRET_KEY is not configured")
    digest = hashlib.sha256(settings.llm_secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_api_key(api_key: str) -> str:
    return _fernet().encrypt(api_key.encode("utf-8")).decode("ascii")


def decrypt_api_key(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise LlmConfigError("LLM provider key cannot be decrypted") from exc


def key_hint(api_key: str) -> str:
    clean = api_key.strip()
    if len(clean) <= 4:
        return "****"
    prefix = clean[:3] if clean.startswith("sk-") else ""
    return f"{prefix}****{clean[-4:]}"


def get_provider_config(db: Session, provider: str = "deepseek") -> LlmProviderConfig | None:
    return db.scalar(select(LlmProviderConfig).where(LlmProviderConfig.provider == provider))


def config_view(row: LlmProviderConfig | None) -> dict:
    if row is None:
        return {
            "provider": "deepseek", "enabled": False, "model": settings.deepseek_model,
            "base_url": settings.deepseek_base_url, "key_hint": "", "configured": False,
            "updated_at": None, "updated_by_id": None,
        }
    return {
        "provider": row.provider, "enabled": row.enabled, "model": row.model,
        "base_url": row.base_url, "key_hint": row.key_hint,
        "configured": bool(row.encrypted_api_key), "updated_at": row.updated_at,
        "updated_by_id": row.updated_by_id,
    }


def upsert_deepseek_config(db: Session, actor: User, *, api_key: str | None, enabled: bool,
                           model: str | None = None, base_url: str | None = None) -> LlmProviderConfig:
    row = get_provider_config(db)
    if row is None:
        row = LlmProviderConfig(provider="deepseek")
        db.add(row)
        db.flush()
    if api_key is not None:
        clean = api_key.strip()
        if not clean:
            raise LlmConfigError("DeepSeek API key cannot be empty")
        row.encrypted_api_key = encrypt_api_key(clean)
        row.key_hint = key_hint(clean)
    row.enabled = enabled
    row.model = (model or row.model or settings.deepseek_model).strip()
    row.base_url = (base_url or row.base_url or settings.deepseek_base_url).strip().rstrip("/")
    row.updated_by_id = actor.id
    return row


def deepseek_credentials(db: Session) -> DeepSeekCredentials | None:
    row = get_provider_config(db)
    if row is None or not row.enabled or not row.encrypted_api_key:
        return None
    return DeepSeekCredentials(
        api_key=decrypt_api_key(row.encrypted_api_key),
        base_url=(row.base_url or settings.deepseek_base_url).rstrip("/"),
        model=row.model or settings.deepseek_model,
    )
