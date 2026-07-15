"""核算看板：项目汇总、员工产值、全量重算。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.accounting import project_summary, employee_output, recompute_all
from app.schemas import AccountingSummary

router = APIRouter(prefix="/accounting", tags=["核算"])


@router.get("/projects", response_model=list[AccountingSummary])
def projects_summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    result = []
    for p in db.query(models.Project).all():
        result.append(AccountingSummary(**project_summary(db, p.id)))
    return result


@router.get("/projects/{pid}", response_model=AccountingSummary)
def one_project(pid: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.get(models.Project, pid):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="项目不存在")
    return AccountingSummary(**project_summary(db, pid))


@router.get("/employees/{eid}")
def one_employee(eid: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return employee_output(db, eid)


@router.post("/recompute")
def recompute(db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    n = recompute_all(db)
    return {"recomputed": n}
