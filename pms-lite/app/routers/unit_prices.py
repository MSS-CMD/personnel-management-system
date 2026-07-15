"""日单价历史：仅管理员可写（PRD v0.5 关键权限）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app import models
from app.schemas import UnitPriceCreate, UnitPriceOut

router = APIRouter(prefix="/unit-prices", tags=["日单价"])


@router.get("", response_model=list[UnitPriceOut])
def list_prices(
    emp_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.UnitPrice)
    if emp_id is not None:
        q = q.filter(models.UnitPrice.emp_id == emp_id)
    return q.order_by(models.UnitPrice.emp_id, models.UnitPrice.effective_date).all()


@router.post("", response_model=UnitPriceOut)
def create(u: UnitPriceCreate, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    # 同员工同日唯一
    exists = db.query(models.UnitPrice).filter(
        models.UnitPrice.emp_id == u.emp_id,
        models.UnitPrice.effective_date == u.effective_date,
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="该员工此生效日已存在单价，请改用修改或删除后重填")
    obj = models.UnitPrice(**u.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{uid}")
def delete(uid: int, db: Session = Depends(get_db), _=Depends(require_role(models.ROLE_ADMIN))):
    obj = db.get(models.UnitPrice, uid)
    if not obj:
        raise HTTPException(status_code=404, detail="单价记录不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}
