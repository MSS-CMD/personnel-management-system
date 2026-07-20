# 人员管理平台（轻量版）pms-lite

> **项目状态：已暂停 / 归档（2025-07-20）**
> 代码已推送到 GitHub（`MSS-CMD/personnel-management-system`，`main` 分支）。
> 如需恢复开发，请直接阅读本文档末尾的「[后续如何继续](#%E5%90%8E%E7%BB%AD%E5%A6%82%E4%BD%95%E7%BB%A7%E7%BB%AD%E6%81%A2%E5%A4%8D%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97)」一节，按步骤操作即可。

---

## 1. 项目简介

面向电气工程团队（经理常出差、成员分散）的**轻量人员产值核算平台**。核心目标：

- 记录每位员工的**日单价**（支持按生效日的历史调价）
- 记录员工的**服务/出差行程**（关联项目、起止日期）
- 管理**项目预算**与**其他成本明细**（设备租赁、差旅等）
- **自动核算**每人产值（日单价 × 服务天数）与项目总支出，识别超支

**设计原则**：单开发者可维护、零运维。后端 FastAPI + SQLite 单文件数据库，前端原生 HTML/JS 无构建步骤，团队成员用浏览器即可访问，无需安装任何软件。

---

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2.x |
| 数据校验 | Pydantic v2 |
| 数据库 | SQLite（单文件 `data/pms.db`，首次运行自动建表） |
| 前端 | 原生 HTML + JS（单文件 `app/static/index.html`，无打包工具） |
| 认证 | 自写 RBAC：Bearer Token + PBKDF2-HMAC-SHA256 密码哈希 |
| 运行 | uvicorn |
| 导入/导出 | openpyxl（XLSX）、标准库 csv（CSV） |

依赖极少，`requirements.txt` 仅 6 个包。

---

## 3. 目录结构

```
pms-lite/
  run.py              便捷启动入口（uvicorn app.main:app :8000）
  run.sh              启动脚本
  requirements.txt    依赖（fastapi/uvicorn/sqlalchemy/pydantic/python-multipart/openpyxl）
  verify.py           核算逻辑本地验证脚本
  generate_templates.py  生成导入模板
  import_templates/   各实体导入 Excel 模板
  app/
    main.py           入口：建表 + seed + 挂载路由 + 托管前端静态页
    database.py       SQLite 引擎 / 会话
    models.py         ORM 模型（Employee/Department/Project/UnitPrice/ServiceRecord/CostDetail/Token）
    schemas.py        Pydantic 请求/响应模型
    security.py       密码哈希 + 令牌签发/校验
    deps.py           认证与权限依赖（get_current_user / require_role）
    accounting.py     ★ 核算核心（历史单价匹配 / 产值 / 汇总 / 重算）
    seed.py           演示数据初始化
    static/
      index.html      极简前端（原生 JS，移动端友好，含全部 CRUD/看板/导入 UI）
    routers/
      auth.py             登录 / 修改密码
      departments.py      部门
      employees.py        员工（含状态/角色修改）
      projects.py         项目（预算、负责人）
      unit_prices.py      日单价历史（仅管理员可写，变更自动重算）
      service_records.py  服务记录（天数/产值自动核算）
      cost_details.py     成本明细
      accounting.py       核算看板（项目汇总/员工产值/部门报表/月度报表/Excel 导出）
      import_.py          数据导入（CSV/XLSX）
```

---

## 4. 功能清单（已完成）

- **主数据管理**：员工、部门、项目、日单价、服务记录、成本明细 的增删改查
- **RBAC 四角色**：系统管理员 / 项目负责人 / 部门负责人 / 普通员工，按权限控制读写
- **历史日单价**：按 `effective_date` 记录调价；核算时取「生效日 ≤ 服务起始日」的最新单价
- **产值自动核算**：`天数 = 结束日 − 起始日 + 1`，`产值 = 匹配单价 × 天数`
- **缺单价兜底**：若员工所有单价生效日均晚于服务起始日（典型事后补录场景），取最早一条单价匹配，避免误报「缺单价」
- **日单价变更自动重算**：新增/删除单价后自动重算该员工全部服务记录，无需手动点「全量重算」
- **核算看板**：项目预算使用率与超支预警、员工产值、部门报表、月度产值报表、Excel 导出
- **数据导入**：员工/项目/日单价/服务记录/成本明细 支持 CSV 与 XLSX 模板导入
- **中文化 UI**：表头、角色、状态、下拉关联、金额千分位、搜索、筛选、加载/空状态
- **员工状态可编辑**：在岗 / 休假 / 出差 / 待岗 随时修改（原创建后固定，已修复）

---

## 5. 权限口径

- **仅系统管理员**可修改员工日单价与项目预算、导入数据。
- **项目负责人**可录入/修改自己负责项目的服务记录与成本明细，不可改单价/预算。
- **普通员工、部门负责人**可查看，不可写主数据（部门负责人可看本部门汇总）。
- 校验：非 admin 调用 `POST /unit-prices` 返回 403。

---

## 6. 核心业务逻辑

核算核心在 `app/accounting.py`：

- `match_unit_price(session, emp_id, service_start)`
  优先取 `effective_date <= service_start` 中最新的一条单价；若该员工所有单价生效日均晚于服务起始日，兜底取最早一条。
- `recompute_record(rec)`：重算单条记录的天数、匹配单价、产值、缺单价标记。
- `recompute_employee(emp_id)`：日单价变更后调用，重算该员工全部服务记录。
- `recompute_all()`：看板「全量重算」按钮调用。
- `project_summary / employee_output / monthly_output / dept_report`：各类汇总。

> **关键修复记录**：commit `068ef63` 修复「日单价已录入但服务记录仍显示缺单价」——根因为匹配规则过严（要求生效日 ≤ 起始日）且单价变更未触发重算。修复后为兜底匹配 + 自动重算。

---

## 7. 如何本地运行

只需 Python 3.10+：

```bash
cd pms-lite
pip install -r requirements.txt
python run.py          # 或：uvicorn app.main:app --port 8000
```

首次启动自动建表并写入演示数据。浏览器打开 **http://localhost:8000** 即可使用。

**演示账号**（密码均为 `admin123`）：

| 账号 | 角色 |
|---|---|
| admin | 系统管理员（可改单价/预算、导入） |
| employee_a / employee_b | 项目负责人（管自己项目的服务记录与成本） |
| employee_c | 普通员工 |
| depthead | 部门负责人 |

> 团队在工地访问：本机跑起来后，同一局域网内用浏览器打开即可；跨网络可加内网穿透 / VPN。

**重置演示数据**（清空后重建）：

```bash
rm -f data/pms.db
python -c "from app.database import init_db, SessionLocal; init_db(); \
from app.seed import seed_if_empty; seed_if_empty()"
```

**验证核算逻辑**：

```bash
python verify.py     # 应全部通过：A=5000 / A历史=2400 / B=2400 / C=600；项目1 人工=8000
```

---

## 8. 已知问题与后续优化点

> 以下为暂停前的待办，恢复开发时可优先处理。

1. **GitHub remote 含明文 Token**：仓库 `.git/config` 的 remote URL 嵌入了 `ghp_***` 个人 Token（仅本地配置，不会进入 GitHub）。**建议恢复开发前在 GitHub 撤销该 Token 并改用 SSH 或个人访问令牌重新鉴权。**
2. **无单条服务记录 GET 接口**：`GET /service-records/{id}` 不存在，前端列表靠全量拉取。如需单条查询/编辑详情可补充。
3. **无自动化测试套件**：仅有 `verify.py` 手工验证脚本。建议引入 pytest + 接口测试，覆盖核算与权限。
4. **无 CI/CD**：目前手动 `git push`，未接 GitHub Actions。可加 lint + 测试 + 构建检查。
5. **密码为演示默认**：`admin123` 仅适合演示；正式使用前应强制改密并考虑加盐策略升级。
6. **SQLite 并发**：单文件数据库适合小团队；若多人高频并发写入，建议评估迁移 Postgres。
7. **前端无构建/无国际化框架**：当前原生 JS 单文件足够轻量，但功能增多后建议评估引入框架或拆分模块。

---

## 9. ★ 后续如何继续（恢复开发指南）

项目已暂停，代码完整保留在 GitHub。恢复时按以下步骤即可无缝接手：

### 步骤 1：准备环境
- 安装 **Python 3.10+**（推荐 3.11）。
- 安装 **Git**。

### 步骤 2：获取代码
两种方式任选其一：
```bash
# 方式 A：从 GitHub 克隆
git clone https://github.com/MSS-CMD/personnel-management-system.git
cd personnel-management-system

# 方式 B：若本地仍保留仓库（/workspace/personnel-repo），直接复用
cd /workspace/personnel-repo
git pull origin main     # 拉取最新
```
> 代码根目录下的 `pms-lite/` 即为可运行项目。

### 步骤 3：安装依赖
```bash
cd pms-lite
pip install -r requirements.txt
```

### 步骤 4：初始化数据库
```bash
python -c "from app.database import init_db, SessionLocal; init_db(); \
from app.seed import seed_if_empty; seed_if_empty()"
```
首次会自动生成 `data/pms.db` 并写入演示数据；已有库则跳过。

### 步骤 5：启动运行
```bash
python run.py
# 浏览器访问 http://localhost:8000，用 admin / admin123 登录
```

### 步骤 6：日常开发工作流
本仓库采用「**工作副本改代码 → 同步到 Git 仓库目录 → commit → push**」的双目录结构：

1. 在 `pms-lite/`（或你 clone 出的目录）修改代码。
2. 本地验证：启动服务 + `python verify.py` + 浏览器自测。
3. 提交并推送：
   ```bash
   git add -A
   git commit -m "feat/fix: 简述改动"
   git push origin main
   ```

### 步骤 7：测试与验收
- 核算：`python verify.py`
- 接口：可用 `requests` 脚本或 Apifox/Postman 调 `http://localhost:8000/docs`（FastAPI 自动文档）。
- 权限：用非 admin 账号验证 403。

### 步骤 8：恢复前的安全必做
- **撤销并轮换 remote 中的 GitHub Token**（见第 8 节第 1 条），改用 SSH 或个人访问令牌。
- 正式使用前强制修改默认密码 `admin123`。

---

## 10. 提交历史要点

| Commit | 说明 |
|---|---|
| `068ef63` | 修复「日单价已录入但服务记录仍显示缺单价」（兜底匹配 + 单价变更自动重算） |
| `2217807` | 修复新增报 `[object Object]`（解析 FastAPI 422 + 空值/必填校验） |
| `54629ca` | 6 项综合修复（中文化 / 员工带单价 / 筛选 / 日期缺省+时长 / 画面重复 / 密码提示） |
| `ac9edc1` | 员工状态/角色可编辑模态弹窗 |
| `f6e6897` | 全面 UI 审核优化（中文化、关联下拉、千分位、看板、搜索） |
| `c77ad69` | 修复侧边栏 fixed 导致内容重叠的排版 bug |
| `9b6e267` | 专业前端视觉升级 |
| `91f4001` | 5 项增强（超支预警、改密、导入模板、报表导出、员工状态） |
| `8e75f01` | 初次提交：完整交付 |

---

> 本文档与代码一同归档于 GitHub。架构没有银弹，合适的才是最好的——恢复开发时请结合团队实际情况调整优先级。
