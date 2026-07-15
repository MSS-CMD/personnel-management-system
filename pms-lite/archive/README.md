# 人员管理平台 — 老方案归档

> 本目录为**旧方案文档副本**，原文件保留在 `workspace/` 根目录不变。
> 新方案（轻量自研单服务）在 `pms-lite/` 目录。

## 目录说明

```
archive/
├── prd/                     # PRD 与研发拆解文档
│   ├── 人员管理平台_PRD.md           # 需求文档 v0.5（含 EARS 需求与验收标准）
│   ├── 人员管理平台_PRD_评审稿.docx   # 评审稿 Word 版
│   ├── 人员管理平台_切片SQL.sql        # MySQL 建表+种子+核算校验（RuoYi 版）
│   ├── 人员管理平台_研发拆解工作项.md    # 17 项研发任务拆解
│   ├── 人员管理平台_需求规划与计划清单.md # 早期需求规划
│   ├── 起步清单_RuoYi版.md            # RuoYi-Vue-Plus 全栈起步步骤
│   └── gen_prd_docx.js              # PRD 转 Word 生成脚本
│
└── plans/                    # 计划文件
    ├── quantum-aurora-darwin.md     # RuoYi-Vue-Plus 起步方案（含最小切片）
    ├── swift-cascade-einstein.md    # 原始研发拆解计划
    └── toasty-aurora-newton.md      # 最终选定方案：轻量自研单服务
```

## 方案路线回顾

| 阶段 | 方案 | 状态 |
|---|---|---|
| 最初 | oa-flow-pms 二开 → 商业授权不可用 | 已放弃 |
| 中间 | RuoYi-Vue-Plus 全栈（quantum-aurora-darwin） | 保留备用 |
| **最终** | **轻量自研单服务（toasty-aurora-newton → pms-lite/）** | **当前执行** |

轻量方案已完整实现在 `pms-lite/` 目录，可直接运行。
