# Darwin — 数字生命体 Docker 镜像

FROM python:3.12-slim

# 防止 Python 缓冲区问题
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --no-cache-dir --upgrade pip

# 安装 hermes-agent（底层依赖）
RUN pip install --no-cache-dir hermes-agent>=0.14.0

# 复制 darwin 包
COPY . /app/

# 安装 darwin-agent
RUN pip install --no-cache-dir /app

# 创建配置目录
RUN mkdir -p /root/.darwin

# 复制 entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

# 清理 pip 缓存
RUN rm -rf /root/.cache/pip

# 暴露端口（未来飞书 webhook 用）
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD ["--help"]