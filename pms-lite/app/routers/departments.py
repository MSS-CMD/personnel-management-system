"""部门：主数据，仅管理员可写。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.schemas import DeptCreate, DeptOut

router = APIRouter(prefix="/departments", tags=["部门"])


@router.get("", response_model=list[DeptOut])
def list_deps(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Department).all()


@router.post("", response_model=DeptOut)
def create(d: DeptCreate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = models.Department(**d.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{did}")
def delete(did: int, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.Department, did)
    if not obj:
        raise HTTPException(status_code=404, detail="部门不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}
