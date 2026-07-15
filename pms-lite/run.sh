#!/usr/bin/env bash
# 启动人员管理平台（轻量版）
set -e
echo "==> 安装依赖"
pip install -r requirements.txt
echo "==> 启动服务（默认 http://localhost:8000）"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
