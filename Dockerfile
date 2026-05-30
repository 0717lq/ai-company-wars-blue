# fclean — 命令行文件整理工具
# 用法: docker build -t fclean . && docker run --rm -v ~/Downloads:/data fclean /data
FROM python:3.12-slim

LABEL maintainer="Blue Team" \
      description="fclean - safe CLI file organizer" \
      version="0.5.0"

# 不生成 .pyc，日志直接输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先复制依赖声明，利用 Docker 缓存层
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# 安装（不含 dev 依赖）
RUN pip install --no-cache-dir .

# 默认挂载 /data 作为工作目录
WORKDIR /data

# ENTRYPOINT 使 docker run fclean 等价于执行 fclean 命令
ENTRYPOINT ["fclean"]

# 默认参数：显示帮助
CMD ["--help"]
