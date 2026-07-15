"""FastAPI 应用入口：初始化数据库、挂载路由、托管极简前端。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.seed import seed_if_empty
from app.routers import (
    accounting,
    auth,
    cost_details,
    departments,
    employees,
    import_,
    projects,
    service_records,
    unit_prices,
)

app = FastAPI(title="人员管理平台（轻量版）", version="0.5.0")

init_db()
seed_if_empty()  # 首次运行写入 PRD 的 A/B/C 演示数据

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(projects.router)
app.include_router(unit_prices.router)
app.include_router(service_records.router)
app.include_router(cost_details.router)
app.include_router(accounting.router)
app.include_router(import_.router)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
