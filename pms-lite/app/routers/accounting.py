"""核算看板：项目汇总、员工产值、报表、全量重算。"""
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.accounting import project_summary, employee_output, recompute_all, monthly_output, dept_report
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
        raise HTTPException(status_code=404, detail="项目不存在")
    return AccountingSummary(**project_summary(db, pid))


@router.get("/employees/{eid}")
def one_employee(eid: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return employee_output(db, eid)


@router.get("/report/monthly")
def report_monthly(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """按 员工 × 月份 汇总产值与天数。"""
    return monthly_output(db)


@router.get("/report/dept")
def report_dept(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """按部门汇总人数、人工产值、超支项目数。"""
    return dept_report(db)


@router.get("/report/export")
def report_export(group_by: str = "monthly", db: Session = Depends(get_db), _=Depends(get_current_user)):
    """导出报表为 Excel（group_by=monthly|dept）。"""
    from openpyxl import Workbook

    if group_by == "dept":
        data = dept_report(db)
        headers = ["部门ID", "部门", "人数", "人工产值", "超支项目数"]
        rows = [[d["dept_id"], d["name"], d["emp_count"], round(d["labor"], 2), d["over_budget_count"]] for d in data]
        fname = "部门报表.xlsx"
    else:
        data = monthly_output(db)
        headers = ["员工ID", "姓名", "月份", "产值", "天数"]
        rows = [[d["emp_id"], d["name"], d["month"], round(float(d["output"]), 2), d["days"]] for d in data]
        fname = "月度产值报表.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb.save(path)
    return FileResponse(path, filename=fname, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/recompute")
def recompute(db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    n = recompute_all(db)
    return {"recomputed": n}
