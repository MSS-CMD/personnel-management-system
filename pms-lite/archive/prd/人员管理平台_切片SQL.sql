-- ============================================================
-- 人员管理平台 · 最小切片建表 + 种子数据 + 核算校验
-- 适用底座：RuoYi-Vue-Plus（或 -Single 单租户版），MySQL 8
-- 用法：先执行"建表"，再执行"种子"，最后执行"校验查询"核对 PRD 例子
-- 说明：员工档案复用若依 sys_user；本文件只建业务表 + 演示数据
-- ============================================================

-- ---------- 1) 建表 ----------
DROP TABLE IF EXISTS pms_emp_unit_price;
CREATE TABLE pms_emp_unit_price (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  emp_id        BIGINT       NOT NULL COMMENT '员工ID(关联 sys_user.user_id)',
  effective_date DATE         NOT NULL COMMENT '生效日期(从该日起新单价)',
  price         DECIMAL(10,2) NOT NULL COMMENT '日单价',
  remark        VARCHAR(255)  DEFAULT '' COMMENT '备注',
  del_flag      CHAR(1)       NOT NULL DEFAULT '0' COMMENT '删除标志(0正常1删除)',
  create_by     VARCHAR(64)   DEFAULT '' COMMENT '创建者',
  create_time   DATETIME      DEFAULT NULL COMMENT '创建时间',
  update_by     VARCHAR(64)   DEFAULT '' COMMENT '更新者',
  update_time   DATETIME      DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_emp_eff (emp_id, effective_date),
  KEY idx_emp (emp_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工日单价历史';

DROP TABLE IF EXISTS pms_project;
CREATE TABLE pms_project (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  name          VARCHAR(100) NOT NULL COMMENT '项目名称',
  dept_id       BIGINT       NOT NULL DEFAULT 0 COMMENT '归属部门(关联 sys_dept.dept_id)',
  leader_user_id BIGINT      NOT NULL DEFAULT 0 COMMENT '项目负责人(关联 sys_user.user_id)',
  budget        DECIMAL(15,2) NOT NULL DEFAULT 0 COMMENT '项目预算',
  status        CHAR(1)       NOT NULL DEFAULT '0' COMMENT '状态(0进行中 1已结项)',
  start_date    DATE          DEFAULT NULL COMMENT '项目开始',
  end_date      DATE          DEFAULT NULL COMMENT '项目结束',
  remark        VARCHAR(255)  DEFAULT '' COMMENT '备注',
  del_flag      CHAR(1)       NOT NULL DEFAULT '0' COMMENT '删除标志',
  create_by     VARCHAR(64)   DEFAULT '' COMMENT '创建者',
  create_time   DATETIME      DEFAULT NULL COMMENT '创建时间',
  update_by     VARCHAR(64)   DEFAULT '' COMMENT '更新者',
  update_time   DATETIME      DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_dept (dept_id),
  KEY idx_leader (leader_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目(归属部门/负责人/预算)';

DROP TABLE IF EXISTS pms_service_record;
CREATE TABLE pms_service_record (
  id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  emp_id        BIGINT       NOT NULL COMMENT '员工ID',
  project_id    BIGINT       NOT NULL COMMENT '项目ID',
  start_date    DATE         NOT NULL COMMENT '服务开始',
  end_date      DATE         NOT NULL COMMENT '服务结束',
  days          INT          NOT NULL DEFAULT 0 COMMENT '服务天数(=end-start+1, 自动算)',
  matched_price DECIMAL(10,2) DEFAULT NULL COMMENT '核算匹配到的生效单价(落库便于看板)',
  output_amount DECIMAL(15,2) DEFAULT NULL COMMENT '人工产值(=matched_price*days)',
  price_missing CHAR(1)       NOT NULL DEFAULT '0' COMMENT '单价缺失标记(0否1是)',
  remark        VARCHAR(255) DEFAULT '' COMMENT '备注',
  del_flag      CHAR(1)       NOT NULL DEFAULT '0' COMMENT '删除标志',
  create_by     VARCHAR(64)   DEFAULT '' COMMENT '创建者',
  create_time   DATETIME      DEFAULT NULL COMMENT '创建时间',
  update_by     VARCHAR(64)   DEFAULT '' COMMENT '更新者',
  update_time   DATETIME      DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_emp_proj (emp_id, project_id),
  KEY idx_proj (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='服务记录(员工+项目+起止)';

-- ---------- 2) 种子数据（PRD 的 A/B/C 例子；emp_id=1/2/3 为演示，实际替换为 sys_user 真实 user_id）----------
-- 员工日单价历史（A：3月400、7月500；B：7月400；C：7月200）
INSERT INTO pms_emp_unit_price (emp_id, effective_date, price, create_by, create_time) VALUES
 (1, '2025-03-01', 400.00, 'admin', NOW()),
 (1, '2025-07-01', 500.00, 'admin', NOW()),
 (2, '2025-07-01', 400.00, 'admin', NOW()),
 (3, '2025-07-01', 200.00, 'admin', NOW());

-- 项目（项目1 预算10000；项目2 预算5000）
INSERT INTO pms_project (name, dept_id, leader_user_id, budget, status, create_by, create_time) VALUES
 ('项目1', 100, 1, 10000.00, '0', 'admin', NOW()),
 ('项目2', 100, 2, 5000.00,  '0', 'admin', NOW());

-- 服务记录（days 由后端算；此处预填便于直接校验）
-- A 7/1-7/10 项目1 (10天) → 匹配500 → 5000
-- B 7/5-7/10 项目2 (6天)  → 匹配400 → 2400
-- C 7/8-7/10 项目1 (3天)  → 匹配200 → 600
-- A历史 3/10-3/15 项目1 (6天) → 匹配400(3月生效) → 2400  【用于验证 AC-13 历史追溯】
INSERT INTO pms_service_record (emp_id, project_id, start_date, end_date, days, create_by, create_time) VALUES
 (1, 1, '2025-07-01', '2025-07-10', 10, 'admin', NOW()),
 (2, 2, '2025-07-05', '2025-07-10', 6,  'admin', NOW()),
 (3, 1, '2025-07-08', '2025-07-10', 3,  'admin', NOW()),
 (1, 1, '2025-03-10', '2025-03-15', 6,  'admin', NOW());

-- ---------- 3) 校验查询（复制执行，核对 PRD AC-4 / AC-5 / AC-7 / AC-13）----------
-- 3.1 每条服务记录按"服务开始日期"匹配当时生效单价，算人工产值
SELECT
  sr.id,
  sr.emp_id,
  sr.project_id,
  sr.start_date,
  sr.end_date,
  sr.days,
  up.price                                                    AS matched_price,
  (sr.days * up.price)                                        AS output_amount,
  CASE WHEN up.price IS NULL THEN '单价缺失' ELSE 'OK' END      AS calc_status
FROM pms_service_record sr
LEFT JOIN pms_emp_unit_price up
  ON up.emp_id = sr.emp_id
 AND up.effective_date = (
       SELECT MAX(effective_date)
       FROM pms_emp_unit_price u2
       WHERE u2.emp_id = sr.emp_id AND u2.effective_date <= sr.start_date
     )
ORDER BY sr.id;

-- 3.2 项目人工汇总（本切片不含成本明细，总支出=人工）
SELECT
  sr.project_id,
  SUM(sr.days * up.price) AS project_labor
FROM pms_service_record sr
LEFT JOIN pms_emp_unit_price up
  ON up.emp_id = sr.emp_id
 AND up.effective_date = (
       SELECT MAX(effective_date)
       FROM pms_emp_unit_price u2
       WHERE u2.emp_id = sr.emp_id AND u2.effective_date <= sr.start_date
     )
WHERE up.price IS NOT NULL
GROUP BY sr.project_id;

-- 期望结果：
-- 3.1: id1→5000(id A 7月), id2→2400(B), id3→600(C), id4→2400(A 历史3月按400)  ← 印证 AC-13 历史追溯
-- 3.2: 项目1=5000+600+2400(历史)=8000；项目2=2400
--      （PRD 例子项目1=6400 是"含差旅成本800"的口径；本切片未建成本明细，故人工=5600(7月部分)+历史2400，
--        等 Epic3 建成本明细后总支出=人工+其他成本，即可得 PRD 的 6400）
