#!/bin/bash
echo "启动后端服务..."
cd "$(dirname "$0")"
python -m uvicorn backend.app.main:app --reload --port 8000

