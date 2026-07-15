"""项目：预算等主数据，仅管理员可写（含预算）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["项目"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Project).all()


@router.post("", response_model=ProjectOut)
def create(p: ProjectCreate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = models.Project(**p.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{pid}", response_model=ProjectOut)
def update(pid: int, p: ProjectUpdate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.Project, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="项目不存在")
    for k, v in p.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{pid}")
def delete(pid: int, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.Project, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}
