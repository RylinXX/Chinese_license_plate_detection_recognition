#!/bin/sh
# 启动脚本：因 web-server.py 文件名含连字符，不能直接作为 Python 模块名
# 改用 uvicorn CLI 的 --app-dir 方式加载
exec uvicorn web-server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --access-log \
    --log-level info
