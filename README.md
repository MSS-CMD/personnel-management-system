# 人员管理平台

轻量自研单服务（FastAPI + SQLite + 极简前端），覆盖项目人员产值核算全流程。

## 仓库结构

| 目录 | 说明 |
|---|---|
| `pms-lite/` | **当前执行方案** — 可运行项目（FastAPI + SQLite） |
| `archive/` | 旧方案文档归档（RuoYi 全栈方案、PRD、研发拆解等） |
| `起步清单_轻量版.md` | 单人 D0–D7 起步步骤 |

## pms-lite 快速开始

只需 Python 3.10+：

```bash
cd pms-lite
pip install -r requirements.txt
python run.py          # 浏览器开 http://localhost:8000
python verify.py       # 核对 A/B/C 验证（应全部通过）
```

演示账号：`admin` / `employee_a` / `employee_b` / `employee_c` / `depthead`（密码均为 `admin123`）

## 核心功能

- 员工日单价历史追溯（账号：仅管理员可改单价）
- 项目产值核算（天数自动算 + 历史单价匹配）
- 项目预算管控（超支自动标红）
- 四角色权限（系统管理员/项目负责人/部门负责人/普通员工）
- CSV / XLSX 导入工具
- 极简前端（单文件 HTML + 原生 JS，移动端友好）
