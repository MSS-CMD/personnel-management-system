# 人员管理平台（轻量版）v0.5

单人可维护的轻量实现：FastAPI + SQLite + 极简前端。覆盖 PRD v0.5 的核心：
历史日单价追溯、产值核算、项目预算管控、四角色权限（仅管理员可改单价）、导入工具。

## 快速开始（你只需装 Python 3.10+）

```bash
cd pms-lite
pip install -r requirements.txt
python run.py          # 或：uvicorn app.main:app --port 8000
```

打开浏览器 http://localhost:8000 即可使用。首次启动自动建表并写入演示数据（A/B/C 例子）。

演示账号（密码均为 `admin123`）：

| 账号 | 角色 |
|---|---|
| admin | 系统管理员（可改单价/预算、导入） |
| employee_a / employee_b | 项目负责人（管自己项目的服务记录与成本） |
| employee_c | 普通员工 |
| depthead | 部门负责人 |

> 团队在工地访问：本机跑起来后，同一局域网，或加内网穿透/VPN，他们用浏览器打开即可，无需装任何软件。

## 验证核算逻辑

```bash
python verify.py
```

应全部通过：A=5000 / A历史=2400 / B=2400 / C=600；项目1 人工=8000；项目2 因设备租赁 3000 超支。

## 目录结构

```
app/
  main.py          入口（建表+seed+挂载路由+托管前端）
  database.py      SQLite 引擎/会话
  models.py        ORM 模型
  schemas.py       Pydantic 模型
  security.py      密码哈希 + 令牌
  deps.py          认证/权限依赖（require_role）
  accounting.py    核算核心（历史单价匹配/产值/汇总）
  seed.py          演示数据
  routers/         auth/departments/employees/projects/unit_prices/
                   service_records/cost_details/accounting/import_
  static/index.html  极简前端（原生 JS，移动端友好）
verify.py          本地验证脚本
requirements.txt   仅 fastapi/uvicorn/sqlalchemy/pydantic/python-multipart/openpyxl
```

## 权限口径（PRD v0.5 更正）

- **仅系统管理员可修改员工日单价与项目预算**。
- 项目负责人可录入/修改自己负责项目的服务记录与成本明细，不可改单价/预算。
- 普通员工、部门负责人可查看，不可写主数据。
- 验证：用非 admin 账号调用 `POST /unit-prices` 返回 403（AC-15）。

## 导入

支持 CSV（标准库）与 XLSX（openpyxl）。表头字段见页面"导入"页说明。
