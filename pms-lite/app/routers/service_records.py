"""服务记录：管理员或项目负责人(仅限自己负责的项目)可写。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app import models
from app.schemas import ServiceRecordCreate, ServiceRecordOut, ServiceRecordUpdate
from app.accounting import recompute_record


def _check_owner(db: Session, user: models.Employee, project_id: int):
    if user.role == models.ROLE_PROJECT_LEADER:
        proj = db.get(models.Project, project_id)
        if not proj or proj.leader_emp_id != user.id:
            raise HTTPException(status_code=403, detail="只能管理自己负责的项目")


router = APIRouter(prefix="/service-records", tags=["服务记录"])


@router.get("", response_model=list[ServiceRecordOut])
def list_records(db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER, models.ROLE_DEPT_LEADER, models.ROLE_EMPLOYEE))):
    return db.query(models.ServiceRecord).all()


@router.post("", response_model=ServiceRecordOut)
def create(r: ServiceRecordCreate, db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    _check_owner(db, user, r.project_id)
    obj = models.ServiceRecord(**r.model_dump())
    db.add(obj)
    db.flush()
    recompute_record(db, obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{rid}", response_model=ServiceRecordOut)
def update(rid: int, r: ServiceRecordUpdate, db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    obj = db.get(models.ServiceRecord, rid)
    if not obj:
        raise HTTPException(status_code=404, detail="服务记录不存在")
    _check_owner(db, user, r.project_id if r.project_id is not None else obj.project_id)
    for k, v in r.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    recompute_record(db, obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{rid}")
def delete(rid: int, db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    obj = db.get(models.ServiceRecord, rid)
    if not obj:
        raise HTTPException(status_code=404, detail="服务记录不存在")
    _check_owner(db, user, obj.project_id)
    db.delete(obj)
    db.commit()
    return {"ok": True}
