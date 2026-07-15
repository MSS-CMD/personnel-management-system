"""核算核心：历史单价匹配、天数、产值、项目总支出。"""
from datetime import date
from decimal import Decimal

from sqlalchemy import func

from app import models


def match_unit_price(session, emp_id: int, service_start: date) -> Decimal | None:
    """取 effective_date <= 服务起始日 中最新的一条日单价；无则返回 None。"""
    row = (
        session.query(models.UnitPrice)
        .filter(
            models.UnitPrice.emp_id == emp_id,
            models.UnitPrice.effective_date <= service_start,
        )
        .order_by(models.UnitPrice.effective_date.desc())
        .first()
    )
    return row.price if row else None


def recompute_record(session, rec: models.ServiceRecord) -> models.ServiceRecord:
    """重算单条服务记录：天数、匹配单价、产值、单价缺失标记。"""
    rec.days = (rec.end_date - rec.start_date).days + 1
    price = match_unit_price(session, rec.emp_id, rec.start_date)
    if price is not None:
        rec.matched_price = price
        rec.output_amount = price * rec.days
        rec.price_missing = False
    else:
        rec.matched_price = None
        rec.output_amount = Decimal(0)
        rec.price_missing = True
    return rec


def recompute_all(session) -> int:
    recs = session.query(models.ServiceRecord).all()
    for r in recs:
        recompute_record(session, r)
    session.commit()
    return len(recs)


def project_summary(session, project_id: int) -> dict:
    proj = session.get(models.Project, project_id)
    recs = session.query(models.ServiceRecord).filter_by(project_id=project_id).all()
    labor = sum((r.output_amount or Decimal(0)) for r in recs)
    other = session.query(
        func.coalesce(func.sum(models.CostDetail.amount), 0)
    ).filter_by(project_id=project_id).scalar() or Decimal(0)
    total = labor + other
    budget = proj.budget if proj else Decimal(0)
    return {
        "project_id": project_id,
        "name": proj.name if proj else None,
        "budget": float(budget),
        "labor": float(labor),
        "other_cost": float(other),
        "total_cost": float(total),
        "over_budget": bool(total > budget),
        "service_count": len(recs),
        "missing_price_count": sum(1 for r in recs if r.price_missing),
    }


def employee_output(session, emp_id: int) -> dict:
    recs = session.query(models.ServiceRecord).filter_by(emp_id=emp_id).all()
    total = sum((r.output_amount or Decimal(0)) for r in recs)
    return {
        "emp_id": emp_id,
        "total_output": float(total),
        "service_count": len(recs),
        "missing_price_count": sum(1 for r in recs if r.price_missing),
    }


def monthly_output(session) -> list:
    """按 员工 × 月份 汇总产值与天数。"""
    agg = {}
    for r in session.query(models.ServiceRecord).all():
        if not r.output_amount:
            continue
        emp = session.get(models.Employee, r.emp_id)
        month = r.start_date.strftime("%Y-%m")
        key = (r.emp_id, month)
        a = agg.setdefault(key, {
            "emp_id": r.emp_id,
            "name": emp.name if emp else "",
            "month": month,
            "output": Decimal(0),
            "days": 0,
        })
        a["output"] += r.output_amount
        a["days"] += r.days
    return [dict(v) for v in agg.values()]


def dept_report(session) -> list:
    """按部门汇总：人数、人工产值、超支项目数。"""
    result = []
    for d in session.query(models.Department).all():
        emps = session.query(models.Employee).filter(models.Employee.dept_id == d.id).all()
        emp_ids = [e.id for e in emps]
        labor = Decimal(0)
        if emp_ids:
            recs = session.query(models.ServiceRecord).filter(models.ServiceRecord.emp_id.in_(emp_ids)).all()
            labor = sum((r.output_amount or Decimal(0)) for r in recs)
        projs = session.query(models.Project).filter(models.Project.dept_id == d.id).all()
        over = sum(1 for p in projs if project_summary(session, p.id)["over_budget"])
        result.append({
            "dept_id": d.id,
            "name": d.name,
            "emp_count": len(emps),
            "labor": float(labor),
            "over_budget_count": over,
        })
    return result

