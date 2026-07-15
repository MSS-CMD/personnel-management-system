"""首次运行自动写入演示数据（PRD 的 A/B/C 例子）。已存在则跳过。"""
from datetime import date
from decimal import Decimal

from app.database import SessionLocal
from app import models
from app.security import hash_password
from app.accounting import recompute_record


def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(models.Employee).first():
            return
        # 部门：电气工程部 -> 电气一部
        dept_root = models.Department(name="电气工程部")
        dept1 = models.Department(name="电气一部")
        db.add_all([dept_root, dept1])
        db.flush()
        dept1.parent_id = dept_root.id

        def emp(username, name, role, dept_id):
            return models.Employee(
                username=username,
                name=name,
                password_hash=hash_password("admin123"),
                role=role,
                dept_id=dept_id,
            )

        admin = emp("admin", "系统管理员", models.ROLE_ADMIN, dept_root.id)
        A = emp("employee_a", "员工A(张三)", models.ROLE_PROJECT_LEADER, dept1.id)
        B = emp("employee_b", "员工B(李四)", models.ROLE_PROJECT_LEADER, dept1.id)
        C = emp("employee_c", "员工C(王五)", models.ROLE_EMPLOYEE, dept1.id)
        dept_head = emp("depthead", "部门负责人(赵六)", models.ROLE_DEPT_LEADER, dept_root.id)
        db.add_all([admin, A, B, C, dept_head])
        db.flush()

        # 项目：项目1 预算10000(负责人A)；项目2 预算5000(负责人B)
        p1 = models.Project(name="项目1", dept_id=dept1.id, leader_emp_id=A.id, budget=Decimal("10000"))
        p2 = models.Project(name="项目2", dept_id=dept1.id, leader_emp_id=B.id, budget=Decimal("5000"))
        db.add_all([p1, p2])
        db.flush()

        # 日单价历史：A(3月400/7月500)、B(7月400)、C(7月200)
        db.add_all([
            models.UnitPrice(emp_id=A.id, effective_date=date(2025, 3, 1), price=Decimal("400")),
            models.UnitPrice(emp_id=A.id, effective_date=date(2025, 7, 1), price=Decimal("500")),
            models.UnitPrice(emp_id=B.id, effective_date=date(2025, 7, 1), price=Decimal("400")),
            models.UnitPrice(emp_id=C.id, effective_date=date(2025, 7, 1), price=Decimal("200")),
        ])

        # 服务记录
        srs = [
            models.ServiceRecord(emp_id=A.id, project_id=p1.id, start_date=date(2025, 7, 1), end_date=date(2025, 7, 10)),
            models.ServiceRecord(emp_id=B.id, project_id=p2.id, start_date=date(2025, 7, 5), end_date=date(2025, 7, 10)),
            models.ServiceRecord(emp_id=C.id, project_id=p1.id, start_date=date(2025, 7, 8), end_date=date(2025, 7, 10)),
            models.ServiceRecord(emp_id=A.id, project_id=p1.id, start_date=date(2025, 3, 10), end_date=date(2025, 3, 15)),
        ]
        db.add_all(srs)
        db.flush()
        for r in srs:
            recompute_record(db, r)

        # 成本明细（演示：项目2 因设备租赁超预算）
        db.add(models.CostDetail(project_id=p1.id, category="差旅", amount=Decimal("800"), occur_date=date(2025, 7, 10)))
        db.add(models.CostDetail(project_id=p2.id, category="设备租赁", amount=Decimal("3000"), occur_date=date(2025, 7, 10)))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    from app.database import init_db

    init_db()
    seed_if_empty()
    print("演示数据已写入（如已存在则跳过）。")
