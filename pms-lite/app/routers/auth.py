"""登录 / 登出 / 当前用户。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import LoginReq, TokenOut, EmployeeOut, ChangePasswordReq
from app.security import verify_password, gen_token, hash_password
from app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenOut)
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(models.Employee.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = gen_token()
    db.add(models.Token(token=token, emp_id=user.id, expire_at=datetime.now() + timedelta(days=30)))
    db.commit()
    return TokenOut(access_token=token, user=EmployeeOut.model_validate(user))


@router.post("/logout")
def logout(authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        db.query(models.Token).filter(models.Token.token == authorization[7:].strip()).delete()
        db.commit()
    return {"ok": True}


@router.get("/me", response_model=EmployeeOut)
def me(user: models.Employee = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    req: ChangePasswordReq,
    db: Session = Depends(get_db),
    user: models.Employee = Depends(get_current_user),
):
    """登录用户修改自己的密码（需校验原密码）。"""
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"ok": True}
