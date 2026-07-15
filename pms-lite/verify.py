"""本地验证：核对 PRD 的 A/B/C 例子与历史单价追溯（AC-13）。"""
from datetime import date
from decimal import Decimal

from app.database import init_db, SessionLocal
from app import models
from app.seed import seed_if_empty
from app.accounting import project_summary, employee_output


def main():
    init_db()
    seed_if_empty()
    db = SessionLocal()
    try:
        A = db.query(models.Employee).filter_by(username="employee_a").first()
        B = db.query(models.Employee).filter_by(username="employee_b").first()
        C = db.query(models.Employee).filter_by(username="employee_c").first()
        p1 = db.query(models.Project).filter_by(name="项目1").first()
        p2 = db.query(models.Project).filter_by(name="项目2").first()

        a_july = db.query(models.ServiceRecord).filter_by(emp_id=A.id, project_id=p1.id, start_date=date(2025, 7, 1)).first()
        a_march = db.query(models.ServiceRecord).filter_by(emp_id=A.id, project_id=p1.id, start_date=date(2025, 3, 10)).first()
        b_rec = db.query(models.ServiceRecord).filter_by(emp_id=B.id, project_id=p2.id, start_date=date(2025, 7, 5)).first()
        c_rec = db.query(models.ServiceRecord).filter_by(emp_id=C.id, project_id=p1.id, start_date=date(2025, 7, 8)).first()

        checks = [
            ("A 7月匹配单价=500", a_july.matched_price == Decimal("500")),
            ("A 7月产值=5000", a_july.output_amount == Decimal("5000")),
            ("A 3月历史匹配单价=400（历史追溯 AC-13）", a_march.matched_price == Decimal("400")),
            ("A 3月历史产值=2400", a_march.output_amount == Decimal("2400")),
            ("B 产值=2400", b_rec.output_amount == Decimal("2400")),
            ("C 产值=600", c_rec.output_amount == Decimal("600")),
            ("A 总产出=7400", employee_output(db, A.id)["total_output"] == 7400),
            ("项目1 人工=8000", abs(project_summary(db, p1.id)["labor"] - 8000) < 1e-6),
            ("项目1 其他成本=800", abs(project_summary(db, p1.id)["other_cost"] - 800) < 1e-6),
            ("项目2 人工=2400", abs(project_summary(db, p2.id)["labor"] - 2400) < 1e-6),
            ("项目2 其他成本=3000", abs(project_summary(db, p2.id)["other_cost"] - 3000) < 1e-6),
            ("项目2 超支=True（预算管控）", project_summary(db, p2.id)["over_budget"] is True),
            ("项目1 不超支", project_summary(db, p1.id)["over_budget"] is False),
        ]

        ok = True
        for name, passed in checks:
            print(("✅" if passed else "❌"), name)
            ok = ok and passed
        print("\n结果：", "全部通过 ✅" if ok else "存在失败 ❌")
        return 0 if ok else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
