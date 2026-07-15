"""ORM 模型：部门 / 员工(兼登录用户) / 日单价历史 / 项目 / 服务记录 / 成本明细 / 令牌。"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 角色常量：系统管理员 / 项目负责人 / 部门负责人 / 普通员工
ROLE_ADMIN = "admin"
ROLE_PROJECT_LEADER = "project_leader"
ROLE_DEPT_LEADER = "dept_leader"
ROLE_EMPLOYEE = "employee"
ROLES = [ROLE_ADMIN, ROLE_PROJECT_LEADER, ROLE_DEPT_LEADER, ROLE_EMPLOYEE]


class Department(Base):
    __tablename__ = "department"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Employee(Base):
    """员工档案，同时作为登录用户（轻量方案合并，避免若依式 sys_user 映射）。"""
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=ROLE_EMPLOYEE)
    dept_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="在岗")  # 在岗/休假/出差/待岗
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UnitPrice(Base):
    """员工日单价历史：同一员工同一生效日唯一，用于历史追溯。"""
    __tablename__ = "unit_price"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"), index=True)
    effective_date: Mapped[date] = mapped_column(Date)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    remark: Mapped[str] = mapped_column(String(255), default="")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint("emp_id", "effective_date", name="uk_emp_eff"),)


class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    dept_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leader_emp_id: Mapped[int | None] = mapped_column(ForeignKey("employee.id"), nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    status: Mapped[int] = mapped_column(Integer, default=0)  # 0 进行中 / 1 已结项
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str] = mapped_column(String(255), default="")


class ServiceRecord(Base):
    """服务记录：员工在某项目的服务起止，派生出天数/匹配单价/产值。"""
    __tablename__ = "service_record"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    days: Mapped[int] = mapped_column(Integer, default=0)
    matched_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    output_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    price_missing: Mapped[bool] = mapped_column(Boolean, default=False)
    remark: Mapped[str] = mapped_column(String(255), default="")


class CostDetail(Base):
    """项目其他成本明细（差旅/设备/外包等），与人工合计为项目总支出。"""
    __tablename__ = "cost_detail"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(100), default="其他")
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    occur_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str] = mapped_column(String(255), default="")


class Token(Base):
    """登录令牌，存库以支持重启后持续有效。"""
    __tablename__ = "token"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employee.id"))
    expire_at: Mapped[datetime] = mapped_column(DateTime)
