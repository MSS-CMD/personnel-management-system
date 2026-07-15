"""Pydantic 请求/响应模型。"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DeptCreate(BaseModel):
    name: str
    parent_id: int | None = None


class DeptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    parent_id: int | None
    create_time: datetime


class EmployeeCreate(BaseModel):
    username: str
    name: str
    password: str
    role: str = "employee"
    dept_id: int | None = None


class EmployeeUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    dept_id: int | None = None
    password: str | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    name: str
    role: str
    dept_id: int | None
    create_time: datetime


class UnitPriceCreate(BaseModel):
    emp_id: int
    effective_date: date
    price: Decimal
    remark: str = ""


class UnitPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    emp_id: int
    effective_date: date
    price: Decimal
    remark: str
    create_time: datetime


class ProjectCreate(BaseModel):
    name: str
    dept_id: int | None = None
    leader_emp_id: int | None = None
    budget: Decimal = 0
    status: int = 0
    start_date: date | None = None
    end_date: date | None = None
    remark: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = None
    dept_id: int | None = None
    leader_emp_id: int | None = None
    budget: Decimal | None = None
    status: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    remark: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    dept_id: int | None
    leader_emp_id: int | None
    budget: Decimal
    status: int
    start_date: date | None
    end_date: date | None
    remark: str


class ServiceRecordCreate(BaseModel):
    emp_id: int
    project_id: int
    start_date: date
    end_date: date
    remark: str = ""


class ServiceRecordUpdate(BaseModel):
    emp_id: int | None = None
    project_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    remark: str | None = None


class ServiceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    emp_id: int
    project_id: int
    start_date: date
    end_date: date
    days: int
    matched_price: Decimal | None
    output_amount: Decimal | None
    price_missing: bool
    remark: str


class CostDetailCreate(BaseModel):
    project_id: int
    category: str = "其他"
    amount: Decimal = 0
    occur_date: date | None = None
    remark: str = ""


class CostDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    category: str
    amount: Decimal
    occur_date: date | None
    remark: str


class LoginReq(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: EmployeeOut


class AccountingSummary(BaseModel):
    project_id: int
    name: str | None
    budget: float
    labor: float
    other_cost: float
    total_cost: float
    over_budget: bool
    service_count: int
    missing_price_count: int
