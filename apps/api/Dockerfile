FROM python:3.11

WORKDIR /workspace

# 复制依赖文件
COPY apps/api/requirements.txt /tmp/apps-api-requirements.txt
COPY services/ai-agents/requirements.txt /tmp/ai-agents-requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r /tmp/apps-api-requirements.txt \
    && pip install --no-cache-dir -r /tmp/ai-agents-requirements.txt

# 复制应用代码，保留仓库目录结构，避免相对路径导入失效
COPY apps/api /workspace/apps/api
COPY services/ai-agents /workspace/services/ai-agents
COPY services/blockchain /workspace/services/blockchain

# 暴露端口
EXPOSE 8000

WORKDIR /workspace/apps/api

ENV PYTHONPATH=/workspace/services:/workspace/services/ai-agents:/workspace/apps/api

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
