# ============================================================
# 工地车辆台账系统 - Dockerfile
# 技术栈: FastAPI + Uvicorn + SQLite
# Python 3.11 slim (轻量化镜像，约 200MB)
# ============================================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    LANG=C.UTF-8

# 安装系统依赖（opencv-headless 需要 libgl）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 先单独复制 requirements.txt，利用 Docker 层缓存
# 只有 requirements 变化时才重新 pip install，加速 rebuild
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制项目核心文件
COPY web-server.py .
COPY recognizer.py .
COPY templates/ ./templates/
COPY static/ ./static/

# 数据目录（持久化 volume 挂载点）
RUN mkdir -p /app/data /app/uploaded_imgs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/summary_analytics')" || exit 1

COPY start.sh .
RUN chmod +x start.sh

# 启动命令（通过 shell 脚本绕过 Python 模块名含连字符的限制）
CMD ["./start.sh"]
