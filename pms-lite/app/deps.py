"""认证与权限依赖。"""
from fastapi import Depends, Header, HTTPException

from app.database import get_db
from app import models
from sqlalchemy.orm import Session


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> models.Employee:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或缺少令牌")
    token = authorization[7:].strip()
    tok = db.query(models.Token).filter(models.Token.token == token).first()
    if not tok:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user = db.get(models.Employee, tok.emp_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_role(*roles: str):
    """返回依赖：当前用户角色不在允许列表则 403（用于写操作守卫）。"""

    def checker(user: models.Employee = Depends(get_current_user)) -> models.Employee:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"无权限：需要角色 {', '.join(roles)}",
            )
        return user

    return checker
