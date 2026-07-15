"""导入工具：支持 CSV（标准库）与 XLSX（openpyxl）。管理员可导入主数据。"""
import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app import models
from app.security import hash_password
from app.accounting import recompute_record

router = APIRouter(prefix="/import", tags=["导入"])


def _rows(file: UploadFile):
    raw = file.file.read()
    name = (file.filename or "").lower()
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(raw), read_only=True)
        ws = wb.active
        vals = list(ws.values)
        wb.close()
        if not vals:
            return []
        header = [str(h).strip() for h in vals[0]]
        return [dict(zip(header, r)) for r in vals[1:] if any(c is not None for c in r)]
    text = raw.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _date(v):
    v = (v if v is not None else "").strip()
    return date.fromisoformat(v) if v and v != "None" else None


def _dec(v):
    v = (v if v is not None else "").strip()
    try:
        return Decimal(str(v)) if v not in ("", "None") else Decimal(0)
    except Exception:
        raise HTTPException(status_code=400, detail=f"数值解析失败: {v!r}")


def _int(v):
    v = (v if v is not None else "").strip()
    return int(v) if v not in ("", "None") else None


def _str(v):
    return (v if v is not None else "").strip()


@router.post("/employees")
def import_employees(file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    n = 0
    for r in _rows(file):
        uname = _str(r.get("username"))
        if not uname:
            continue
        if db.query(models.Employee).filter(models.Employee.username == uname).first():
            continue
        db.add(models.Employee(
            username=uname, name=_str(r.get("name")) or uname,
            password_hash=hash_password(_str(r.get("password")) or "admin123"),
            role=_str(r.get("role")) or "employee",
            dept_id=_int(r.get("dept_id")),
        ))
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/projects")
def import_projects(file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    n = 0
    for r in _rows(file):
        name = _str(r.get("name"))
        if not name:
            continue
        db.add(models.Project(
            name=name, dept_id=_int(r.get("dept_id")),
            leader_emp_id=_int(r.get("leader_emp_id")),
            budget=_dec(r.get("budget")), status=int(_str(r.get("status")) or 0),
            start_date=_date(r.get("start_date")), end_date=_date(r.get("end_date")),
            remark=_str(r.get("remark")),
        ))
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/unit-prices")
def import_unit_prices(file: UploadFile = File(...), db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    n = 0
    for r in _rows(file):
        emp_id = _int(r.get("emp_id"))
        d = _date(r.get("effective_date"))
        if not emp_id or not d:
            continue
        exists = db.query(models.UnitPrice).filter(
            models.UnitPrice.emp_id == emp_id, models.UnitPrice.effective_date == d).first()
        if exists:
            exists.price = _dec(r.get("price"))
            exists.remark = _str(r.get("remark"))
        else:
            db.add(models.UnitPrice(emp_id=emp_id, effective_date=d,
                     price=_dec(r.get("price")), remark=_str(r.get("remark"))))
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/service-records")
def import_service_records(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    n = 0
    for r in _rows(file):
        emp_id = _int(r.get("emp_id"))
        pid = _int(r.get("project_id"))
        sd = _date(r.get("start_date"))
        ed = _date(r.get("end_date"))
        if not (emp_id and pid and sd and ed):
            continue
        if user.role == models.ROLE_PROJECT_LEADER:
            proj = db.get(models.Project, pid)
            if not proj or proj.leader_emp_id != user.id:
                raise HTTPException(status_code=403, detail=f"只能导入自己负责的项目: {pid}")
        obj = models.ServiceRecord(emp_id=emp_id, project_id=pid, start_date=sd, end_date=ed,
                                   remark=_str(r.get("remark")))
        db.add(obj)
        db.flush()
        recompute_record(db, obj)
        n += 1
    db.commit()
    return {"imported": n}


@router.post("/cost-details")
def import_cost_details(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_role(models.ROLE_ADMIN, models.ROLE_PROJECT_LEADER))):
    n = 0
    for r in _rows(file):
        pid = _int(r.get("project_id"))
        if not pid:
            continue
        if user.role == models.ROLE_PROJECT_LEADER:
            proj = db.get(models.Project, pid)
            if not proj or proj.leader_emp_id != user.id:
                raise HTTPException(status_code=403, detail=f"只能导入自己负责的项目: {pid}")
        db.add(models.CostDetail(
            project_id=pid, category=_str(r.get("category")) or "其他",
            amount=_dec(r.get("amount")), occur_date=_date(r.get("occur_date")),
            remark=_str(r.get("remark"))))
        n += 1
    db.commit()
    return {"imported": n}
