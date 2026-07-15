"""项目其他成本明细：管理员或项目负责人(自己项目)可写。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app import models
from app.schemas import CostDetailCreate, CostDetailOut

router = APIRouter(prefix="/cost-details", tags=["成本明细"])


def _check_owner(db: Session, user: models.Employee, project_id: int):
    if user.role == models.ROLE_PROJECT_LEADER:
        proj = db.get(models.Project, project_id)
        if not proj or proj.leader_emp_id != user.id:
            raise HTTPException(status_code=403, detail="只能管理自己负责的项目")


@router.get("", response_model=list[CostDetailOut])
def list_costs(project_id: int | None = None, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER, models.ROLE_DEPT_LEADER, models.ROLE_EMPLOYEE))):
    q = db.query(models.CostDetail)
    if project_id is not None:
        q = q.filter(models.CostDetail.project_id == project_id)
    return q.all()


@router.post("", response_model=CostDetailOut)
def create(c: CostDetailCreate, db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    _check_owner(db, user, c.project_id)
    obj = models.CostDetail(**c.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{cid}")
def delete(cid: int, db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    obj = db.get(models.CostDetail, cid)
    if not obj:
        raise HTTPException(status_code=404, detail="成本明细不存在")
    _check_owner(db, user, obj.project_id)
    db.delete(obj)
    db.commit()
    return {"ok": True}
