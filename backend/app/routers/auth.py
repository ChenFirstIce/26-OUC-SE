from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import current_user
from ..core.security import create_token, verify_password
from ..models import User
from ..services.audit import audit
from ..services.permissions import permission_for, permission_view


router = APIRouter(prefix="/auth", tags=["认证"])


class LoginInput(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    audit(db, "user", user.id, "login", "user", user.id)
    db.commit()
    return {"access_token": create_token(str(user.id), user.role), "token_type": "bearer", "user": user_view(user, db)}


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_view(user, db)


def user_view(user: User, db: Session) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else None,
        "permissions": permission_view(permission_for(db, user)),
    }
