# 人员管理平台 — 起步方案 + 最小可跑通切片

> 计划类型：阶段四 · 研发跟进（Epic0 脚手架 + 核心核算闭环）
> 依据：PRD v0.5、研发拆解工作项（17 项）、用户确认"技术底座 = RuoYi-Vue-Plus（开源同栈）"、产出 = 起步方案 + 最小可跑通切片
> 适用：单人开发（你一人完成所有代码），本地验证部署

---

## 0. 本次确认的关键决策

| 项 | 结论 |
|----|------|
| 原假设 `oa-flow-pms` | **弃用**：GitHub 仓库仅 docs，源码需付费，不可 clone 二开 |
| 实际底座 | **RuoYi-Vue-Plus**（dromara，Apache-2.0，完全开源可商用，Java+Vue 同栈） |
| 单公司适配 | 优先用 **RuoYi-Vue-Plus-Single**（已删多租户与工作流，最贴合"单公司 + 无流程"）；若其版本滞后则用主仓库并忽略租户功能 |
| 产出范围 | Epic0 脚手架 + 最小可跑通切片（部门 / 员工+日单价 / 项目+预算 / 服务记录 / 核算引擎） |
| 角色 | 你一人开发，wb-issues 17 项即你的个人任务清单，按 5 批次自己认领 |

> 技术栈已核实：SpringBoot **3.5.x**（需 **JDK 17+**）、Vue3 + TS + ElementPlus（plus-ui）、MyBatis-Plus、Sa-Token（鉴权/角色）、Redis ≥6、MySQL 8（也支持 PG/SQLServer）、FastExcel（导入导出）、**内置代码生成器（设计表→一键生成 CRUD+页面，省约 80% 样板）**。

---

## 1. 本地环境（前置，一次性）

- **JDK 17+**（SpringBoot 3.5 硬性要求；注意区别于若依原版 JDK8/11）
- **Maven 3.8+**、**Node 18/20+**、**MySQL 8**、**Redis 6+**
- 代码编辑器（IDEA / VS Code）

---

## 2. 获取与启动（Epic0：T0.1 拉框架 + T0.2 库/权限/组织）

1. **克隆**（二选一）
   - 单租户精简版（推荐）：`git clone https://gitee.com/ColorDreams/RuoYi-Vue-Plus-Single.git`
   - 主仓库（维护最活跃，SpringBoot 3.5.15）：`git clone https://github.com/dromara/RuoYi-Vue-Plus.git` + 前端 `git clone https://github.com/JavaLionLi/plus-ui.git`
2. **建库**：执行仓库 `script/` 下 SQL（若依基础表：`sys_dept` 部门树、`sys_user` 用户、`sys_role` 角色、`sys_menu` 菜单、`sys_dict` 字典等）。
3. **改配置**：`ruoyi-admin` 的 `application.yml` / `application-dev.yml` 填 MySQL、Redis 连接；`ruoyi-generator` 配代码生成器数据源。
4. **起后端**：运行 `RuoYiApplication`（Undertow，默认 8080）。
5. **起前端**：`plus-ui` → `npm install` → `npm run dev`（默认 80）。
6. **验证**：浏览器登录（admin / 默认密码），看到若依主页、部门树、用户管理即成功。
7. **交付标志**：本地可跑的空壳 + 若依基础能力（部门/用户/角色/权限/Sa-Token 数据权限）。

---

## 3. 最小切片数据模型（DDL 草图，落库后用代码生成器）

| 实体 | 表 | 说明 | 对应任务 |
|------|----|------|----------|
| 部门 | `sys_dept`（自带） | 树形，单公司多部门；**零代码复用** | T1.1 |
| 员工 | `sys_user`（自带）+ `pms_emp_unit_price` | 员工档案复用用户表；日单价历史独立表 | T1.2 |
| 项目 | `pms_project` | name, dept_id, leader_user_id, budget, status | T1.3 |
| 服务记录 | `pms_service_record` | emp_id, project_id, start_date, end_date, days(计算) | T2.1 |
| 成本明细 | （本切片**不建**，留 Epic3） | — | — |
| 核算结果 | 不落表，由服务记录+单价历史实时算（或缓存 `pms_emp_output`） | 自定义逻辑 | T2.2/T2.3 |

`pms_emp_unit_price` 关键字段：`emp_id, effective_date(生效日期), price(日单价), create_by`。同一员工同生效日唯一（PRD AC-2）。
`pms_project`：`dept_id(归属部门), leader_user_id(负责人), budget(默认0), status(进行中/已结项)`。
`pms_service_record`：保存时算 `days = datediff(end,start)+1`，校验 start≤end、同员工同项目区间不重叠（FR-SVC）。

---

## 4. 切片实现步骤（你一个人照做）

1. **代码生成器出样板**：为 `pms_project`、`pms_service_record`、`pms_emp_unit_price` 在生成器里配置字段→一键生成后端 Controller/Service/Mapper + Vue 列表/增删改/导出页。
2. **员工+日单价（T1.2）**：在用户页加"日单价历史"子页/弹窗，录入生效日期+单价写 `pms_emp_unit_price`；**单价修改入口仅 admin**——后端 `@SaCheckRole("admin")`，前端按角色隐藏。
3. **项目（T1.3）**：生成器产出后，补"负责人/预算/状态"字段与"结项冻结录入"逻辑（FR-PRJ）。
4. **服务记录（T2.1）**：保存时后端算天数、校验倒序/重叠。
5. **核算引擎（T2.2/T2.3，手写核心，生成器帮不了）**：`AccountingService.compute()`
   - 对每条服务记录，按**服务日期**匹配生效单价：取 `effective_date ≤ 服务日期` 的最新一条；
   - 个人人工产值 = 匹配单价 × days；项目人工 = Σ；项目总支出 = 人工（+ 成本明细，本切片暂为 0）；执行率 = 总支出 ÷ 预算；
   - 无匹配标"单价缺失"置顶，不计入直至补全（FR-CAL / AC-13）。
6. **看板雏形（T4 部分）**：员工卡（部门/在服务项目/产值）、项目卡（预算/人工/总支出/执行率）——先用简单接口+页面验证，完整看板留 Epic4。
7. **本地验证（关键）**：种入 PRD 的 A/B/C 例子
   - A: 单价500（3月400、7月500），7/1–7/10 项目1（10天）→ 5000
   - B: 单价400，7/5–7/10 项目2（6天）→ 2400
   - C: 单价200，7/8–7/10 项目1（3天）→ 600
   - 核对 AC-4（天数10/6/3）、AC-5（5000/2400/600）、AC-7（项目1=5600、项目2=2400）、AC-13（历史3月服务按400、7月按500 分别核算）。

---

## 5. 与 PRD / 工作项映射

- **本切片覆盖**：T0.1、T0.2、T1.1、T1.2、T1.3、T2.1、T2.2、T2.3。
- **留后续批次**：T3 成本明细、T4 完整看板、T5 预算预警、T6 权限细化、T7 导入导出、T8 测试试点。
- 切片完成即拥有"录入→核算"主心骨，可先给自己和小范围同事用起来验证口径。

---

## 6. 风险与注意

- **R1 环境**：SpringBoot 3.5 必须 JDK 17+；本机若只有 JDK8/11 需先装 17。
- **R2 单公司**：用 -Single 版或主仓库忽略租户；勿被多租户 `tenant_id` 拦截干扰。
- **R3 权限**：Sa-Token 注解做角色校验（admin 改单价），前端按角色隐藏入口（双重保险，对应 PRD 单价仅管理员）。
- **R4 核算是自定义核心**：代码生成器覆盖不了，建议顺手为 `AccountingService` 写单测（即提前做 T8.1 用例，保障 A/B/C 与历史追溯不出错）。
- **R5 资料库上传**：此前因后端临时凭证偶发 `InvalidAccessKeyId` 未成功，三份 v0.5 文件在 `/workspace`，可手动传或稍后重试。

---

## 7. 本切片完成标志（Exit 条件）

- [ ] 本地前后端起服务成功，若依基础（部门树/用户/角色）可用
- [ ] 能录员工+日单价历史、建项目+预算、录服务记录（天数自动算、校验生效）
- [ ] 核算接口/页面按历史追溯算出 A/B/C 与项目汇总，与 PRD 例子完全一致
- [ ] admin 以外角色看不到"改单价"入口（后端拦截生效）

---

## 8. 下一步（切片通过后）

按原 5 批次继续：第3批看板完整（T4.1/T4.2）→ 第4批预算预警（T5）→ 第5批权限细化+导入导出（T6/T7）→ 第6批测试试点（T8）。每批完成可随时本地验证。
