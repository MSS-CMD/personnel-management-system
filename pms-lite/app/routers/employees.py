"""员工（兼用户）：主数据，仅管理员可写。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.security import hash_password

router = APIRouter(prefix="/employees", tags=["员工"])


@router.get("", response_model=list[EmployeeOut])
def list_emps(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Employee).all()


@router.post("", response_model=EmployeeOut)
def create(e: EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    if db.query(models.Employee).filter(models.Employee.username == e.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if e.role not in models.ROLES:
        raise HTTPException(status_code=400, detail=f"角色必须是 {models.ROLES}")
    obj = models.Employee(
        username=e.username, name=e.name,
        password_hash=hash_password(e.password), role=e.role, dept_id=e.dept_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{eid}", response_model=EmployeeOut)
def update(eid: int, e: EmployeeUpdate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.Employee, eid)
    if not obj:
        raise HTTPException(status_code=404, detail="员工不存在")
    data = e.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["password_hash"] = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{eid}")
def delete(eid: int, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.Employee, eid)
    if not obj:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}
