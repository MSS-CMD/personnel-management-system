"""生成 5 个导入模板（xlsx），供用户在「导入」页下载后填写真实数据。"""
import os

from openpyxl import Workbook

OUT = os.path.join(os.path.dirname(__file__), "import_templates")
os.makedirs(OUT, exist_ok=True)

TEMPLATES = {
    "员工导入模板.xlsx": {
        "headers": ["username", "name", "password", "role", "status", "dept_id"],
        "example": ["zhang3", "张三", "admin123", "employee", "在岗", 1],
        "note": "username 登录账号(唯一); role: admin/project_leader/dept_leader/employee; status: 在岗/休假/出差/待岗; dept_id 部门ID",
    },
    "项目导入模板.xlsx": {
        "headers": ["name", "dept_id", "leader_emp_id", "budget", "status", "start_date", "end_date"],
        "example": ["某项目", 1, 2, 50000, 0, "2025-01-01", "2025-12-31"],
        "note": "budget 预算(数字); status: 0进行中/1已结项; 日期格式 YYYY-MM-DD",
    },
    "日单价导入模板.xlsx": {
        "headers": ["emp_id", "effective_date", "price", "remark"],
        "example": [2, "2025-03-01", 400, "3月起执行价"],
        "note": "emp_id 员工ID; effective_date 生效日期 YYYY-MM-DD; price 日单价(数字)",
    },
    "服务记录导入模板.xlsx": {
        "headers": ["emp_id", "project_id", "start_date", "end_date", "remark"],
        "example": [2, 1, "2025-07-01", "2025-07-10", "现场施工"],
        "note": "起止日期 YYYY-MM-DD; 天数自动=截止-起始+1; 产值=匹配日单价×天数",
    },
    "成本明细导入模板.xlsx": {
        "headers": ["project_id", "category", "amount", "occur_date", "remark"],
        "example": [1, "差旅", 800, "2025-07-10", "出差补助"],
        "note": "category 类别(差旅/设备租赁/外包等); amount 金额(数字); occur_date 发生日期 YYYY-MM-DD",
    },
}

for fname, cfg in TEMPLATES.items():
    wb = Workbook()
    ws = wb.active
    ws.title = "数据"
    ws.append(cfg["headers"])
    ws.append(cfg["example"])
    # 说明页
    ws2 = wb.create_sheet("填写说明")
    ws2.append(["字段说明"])
    ws2.append([cfg["note"]])
    ws2.append([])
    ws2.append(["注意：第一行是表头请勿删除；第二行是示例，可删改；生效日期/起止日期用 YYYY-MM-DD 格式。"])
    path = os.path.join(OUT, fname)
    wb.save(path)
    print("生成:", path)

print("完成，共", len(TEMPLATES), "个模板")
