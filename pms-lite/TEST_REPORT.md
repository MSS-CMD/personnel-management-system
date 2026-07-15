# pms-lite 验收测试报告

> 测试环境：Ubuntu 22.04 / Python 3.11 / FastAPI + SQLite（单文件 `data/pms.db`）
> 测试方式：本地启动 `run.py`，通过 HTTP 接口与 `verify.py` 断言双重验证
> 测试日期：2025-07-15（沙箱环境）

## 一、启动与可达性

| 项 | 路径 | 预期 | 实际 | 结果 |
|---|---|---|---|---|
| 健康检查 | `GET /health` | 200 | 200 `{"status":"ok"}` | ✅ |
| 极简前端首页 | `GET /` | 200 (HTML) | 200 | ✅ |

> 注意：本项目接口**没有** `/api` 前缀，完整前缀见 `openapi.json`（如 `/auth/login`、`/projects`、`/accounting/projects`）。前端 `index.html` 已对齐。

## 二、核算核心（对照 PRD v0.5 用例 A/B/C）

由 `verify.py`（13 项断言）执行，全部通过：

| 用例 | 说明 | 预期值 | 结果 |
|---|---|---|---|
| A·7月 | 匹配单价 | 500 | ✅ |
| A·7月 | 产值 = 500 × 10天 | 5000 | ✅ |
| A·3月 | 历史追溯匹配单价（AC-13） | 400 | ✅ |
| A·3月 | 历史产值 = 400 × 6天 | 2400 | ✅ |
| B | 产值 | 2400 | ✅ |
| C | 产值 | 600 | ✅ |
| A 合计 | 总产出 | 7400 | ✅ |
| 项目1 | 人工合计 | 8000 | ✅ |
| 项目1 | 其他成本（差旅） | 800 | ✅ |
| 项目2 | 人工合计 | 2400 | ✅ |
| 项目2 | 其他成本（设备租赁） | 3000 | ✅ |
| 项目2 | 超支（预算 5000 < 5400） | True | ✅ |
| 项目1 | 不超支（8800 ≤ 10000） | False | ✅ |

## 三、权限与鉴权（AC-15 仅管理员可改单价）

| 场景 | 请求 | 预期 | 实际 | 结果 |
|---|---|---|---|---|
| 未登录 | `GET /projects` | 401 | 401 | ✅ |
| 管理员登录 | `POST /auth/login` | 返回 `access_token` | 200 + token | ✅ |
| 管理员改单价 | `POST /unit-prices` | 200 | 200 | ✅ |
| 普通员工改单价 | `POST /unit-prices`（employee_a） | 403 | 403 | ✅ |

## 四、看板汇总接口

`GET /accounting/projects`（管理员令牌）：

```json
[
  {"project_id":1,"name":"项目1","budget":10000,"labor":8000,"other_cost":800,"total_cost":8800,"over_budget":false,"service_count":3,"missing_price_count":0},
  {"project_id":2,"name":"项目2","budget":5000,"labor":2400,"other_cost":3000,"total_cost":5400,"over_budget":true,"service_count":1,"missing_price_count":0}
]
```

个人历史追溯 `GET /accounting/employees/2`（employee_a）：

```json
{"emp_id":2,"total_output":7400,"service_count":2,"missing_price_count":0}
```

## 五、结论

核心功能（日单价历史匹配、个人/项目产值核算、预算超支判定、RBAC 权限）**全部达到 PRD 验收标准**，可进入下一阶段开发或本地试用。

## 六、安全提醒（重要）

项目早期曾在对话中提供过 GitHub Personal Access Token，并曾写入本地 git remote URL。
**建议立即到 GitHub → Settings → Developer settings → Personal access tokens 撤销（revoke）该 token**，并确认 `personnel-repo/.git/config` 的 remote 已不含明文 token（改用 SSH 或重新 clone）。
