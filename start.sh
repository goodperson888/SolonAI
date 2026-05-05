#!/bin/bash

# =============================================
# Solon AI - 一键启动脚本
# 同时启动：前端 + 后端API + AI服务
# =============================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "============================================"
echo "  Solon AI - 一键启动"
echo "============================================"
echo -e "${NC}"

# 项目根目录
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_MODE="${SOLON_DB_MODE:-sqlite}"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"
API_PORT="${SOLON_API_PORT:-8000}"
WEB_PORT="${SOLON_WEB_PORT:-3000}"
API_HOST="${SOLON_API_HOST:-127.0.0.1}"
WEB_HOST="${SOLON_WEB_HOST:-127.0.0.1}"
API_RELOAD="${SOLON_API_RELOAD:-1}"
LOG_DIR="$ROOT_DIR/.logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
SOLANA_NETWORK="${SOLANA_NETWORK:-mainnet}"
SOLANA_RPC_URLS="${SOLANA_RPC_URLS:-https://api.mainnet-beta.solana.com,https://solana-rpc.publicnode.com}"
SOLON_PROXY_URL="${SOLON_PROXY_URL:-}"
SOLON_DEMO_MODE="${SOLON_DEMO_MODE:-0}"

mkdir -p "$LOG_DIR"

API_PID=""
WEB_PID=""

command_exists() {
    command -v "$1" &> /dev/null
}

detect_python_bin() {
    if [ -n "${SOLON_PYTHON_BIN:-}" ] && command_exists "$SOLON_PYTHON_BIN"; then
        echo "$SOLON_PYTHON_BIN"
        return 0
    fi

    local candidates=("python3.11" "python3.10" "python3")
    local candidate

    for candidate in "${candidates[@]}"; do
        if command_exists "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

PYTHON_BIN="$(detect_python_bin || true)"
VENV_PYTHON="$API_DIR/.venv/bin/python"

wait_for_http() {
    local url="$1"
    local name="$2"
    local max_attempts="${3:-30}"
    local attempt=1

    while [ "$attempt" -le "$max_attempts" ]; do
        if command_exists curl && curl -fsS "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ ${name} 启动超时: ${url}${NC}"
    return 1
}

ensure_process_alive() {
    local pid="$1"
    local name="$2"
    local log_file="$3"

    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}❌ ${name} 启动失败${NC}"
        if [ -f "$log_file" ]; then
            echo -e "${YELLOW}--- ${name} 日志 ---${NC}"
            tail -n 80 "$log_file" || true
            echo -e "${YELLOW}--- 日志结束 ---${NC}"
        fi
        exit 1
    fi
}

validate_backend_env() {
    if "$VENV_PYTHON" -c "import fastapi, pydantic, sqlalchemy, uvicorn" > /dev/null 2>&1; then
        return 0
    fi

    echo -e "${RED}❌ apps/api/.venv 当前不可用，无法导入后端关键依赖${NC}"
    echo -e "${YELLOW}  常见原因：${NC}"
    echo -e "    1. 虚拟环境里的二进制包架构不匹配（例如 Rosetta/x86_64 与 arm64 混用）"
    echo -e "    2. 依赖未完整安装"
    echo -e "    3. 使用了错误版本的 Python 创建 .venv"
    echo -e "${YELLOW}  建议重建方式：${NC}"
    echo -e "    cd apps/api"
    echo -e "    rm -rf .venv"
    echo -e "    python3 -m venv .venv"
    echo -e "    source .venv/bin/activate"
    echo -e "    python -m pip install --upgrade pip"
    echo -e "    python -m pip install -r requirements.txt"
    echo -e "${YELLOW}  详细错误：${NC}"
    "$VENV_PYTHON" -c "import fastapi, pydantic, sqlalchemy, uvicorn" || true
    exit 1
}

# ===== 检查环境 =====
echo -e "${YELLOW}[1/4] 检查环境...${NC}"

# 检查 Node.js
if ! command_exists node; then
    echo -e "${RED}❌ 未安装 Node.js，请先安装: https://nodejs.org${NC}"
    exit 1
fi
echo -e "  ✅ Node.js $(node -v)"

# 检查 Python3
if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}❌ 未安装可用的 Python3${NC}"
    exit 1
fi
echo -e "  ✅ Python $("$PYTHON_BIN" --version) (${BLUE}${PYTHON_BIN}${NC})"

if [ "$DB_MODE" = "sqlite" ]; then
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./solon_ai.db}"
elif [ "$DB_MODE" = "postgres" ]; then
    export DATABASE_URL="${DATABASE_URL:-postgresql://solon:solon_password@localhost:5432/solon_ai}"
else
    echo -e "${RED}❌ 不支持的 SOLON_DB_MODE: $DB_MODE${NC}"
    echo -e "  可选值: sqlite / postgres"
    exit 1
fi
export SOLANA_NETWORK
export SOLANA_RPC_URLS
export SOLON_DEMO_MODE
echo -e "  ✅ 数据库模式: ${BLUE}$DB_MODE${NC}"
echo -e "  ✅ 后端地址: ${BLUE}http://${API_HOST}:${API_PORT}${NC}"
echo -e "  ✅ 前端地址: ${BLUE}http://${WEB_HOST}:${WEB_PORT}${NC}"
echo -e "  ✅ Solana 网络: ${BLUE}${SOLANA_NETWORK}${NC}"
echo -e "  ✅ Solana RPC: ${BLUE}${SOLANA_RPC_URLS}${NC}"
echo -e "  ✅ Demo 模式: ${BLUE}${SOLON_DEMO_MODE}${NC}"
if [ -n "$SOLON_PROXY_URL" ]; then
    export HTTP_PROXY="$SOLON_PROXY_URL"
    export HTTPS_PROXY="$SOLON_PROXY_URL"
    export ALL_PROXY="$SOLON_PROXY_URL"
    export NO_PROXY="${NO_PROXY:-127.0.0.1,localhost}"
    echo -e "  ✅ 代理地址: ${BLUE}${SOLON_PROXY_URL}${NC}"
fi

# 检查 AI 服务的 .env 文件
if [ ! -f "$ROOT_DIR/services/ai-agents/.env" ]; then
    echo -e "${YELLOW}  ⚠️  未找到 AI 服务配置文件，复制模板...${NC}"
    cp "$ROOT_DIR/services/ai-agents/.env.example" "$ROOT_DIR/services/ai-agents/.env"
    echo -e "${YELLOW}  ⚠️  请编辑 services/ai-agents/.env 填写你的大模型 API Key${NC}"
fi

# ===== 安装依赖 =====
echo -e "${YELLOW}[2/4] 检查依赖...${NC}"

# 前端依赖
if [ ! -d "$ROOT_DIR/node_modules" ]; then
    echo -e "  📦 安装前端依赖..."
    cd "$ROOT_DIR" && npm install
else
    echo -e "  ✅ 前端依赖已安装"
fi

# 后端依赖
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}  ⚠️  未找到 apps/api/.venv，请先创建虚拟环境并安装依赖${NC}"
    echo -e "     cd apps/api && ${PYTHON_BIN} -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt"
    exit 1
fi

echo -e "  ✅ 使用虚拟环境: $VENV_PYTHON"
echo -e "  ✅ 所有依赖请通过 apps/api/.venv 维护"
validate_backend_env

# 初始化数据库
echo -e "  🗄️  初始化数据库表..."
cd "$API_DIR"
"$VENV_PYTHON" -m app.core.init_db > "$BACKEND_LOG" 2>&1
echo -e "  ✅ 数据库初始化完成"

# ===== 启动服务 =====
echo -e "${YELLOW}[3/4] 启动服务...${NC}"

# 添加 Python 用户安装路径
export PATH="$PATH:$HOME/Library/Python/3.9/bin:$HOME/.local/bin"

# 清理之前的进程
lsof -ti:"$WEB_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:3001 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:"$API_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true

API_RELOAD_FLAG=""
if [ "$API_RELOAD" = "1" ]; then
    API_RELOAD_FLAG="--reload"
fi

# 启动后端 API
echo -e "  🚀 启动后端 API (http://${API_HOST}:${API_PORT})..."
cd "$API_DIR"
PYTHONPATH="$ROOT_DIR/services:$ROOT_DIR/services/ai-agents:${PYTHONPATH:-}" \
    "$VENV_PYTHON" -m uvicorn main:app --host "$API_HOST" --port "$API_PORT" $API_RELOAD_FLAG \
    > "$BACKEND_LOG" 2>&1 &
API_PID=$!

sleep 2
ensure_process_alive "$API_PID" "后端 API" "$BACKEND_LOG"
wait_for_http "http://${API_HOST}:${API_PORT}/health" "后端 API"

# 启动前端
echo -e "  🚀 启动前端 (http://${WEB_HOST}:${WEB_PORT})..."
cd "$WEB_DIR"
npx next dev -H "$WEB_HOST" -p "$WEB_PORT" > "$FRONTEND_LOG" 2>&1 &
WEB_PID=$!

sleep 3
ensure_process_alive "$WEB_PID" "前端" "$FRONTEND_LOG"
wait_for_http "http://${WEB_HOST}:${WEB_PORT}" "前端"

# ===== 启动完成 =====
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ Solon AI 启动完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  🗄️  数据库:   ${BLUE}$DB_MODE${NC}"
echo -e "  🌐 前端:     ${BLUE}http://${WEB_HOST}:${WEB_PORT}${NC}"
echo -e "  🔌 后端API:  ${BLUE}http://${API_HOST}:${API_PORT}${NC}"
echo -e "  📚 API文档:  ${BLUE}http://${API_HOST}:${API_PORT}/docs${NC}"
echo -e "  📝 后端日志: ${BLUE}${BACKEND_LOG}${NC}"
echo -e "  📝 前端日志: ${BLUE}${FRONTEND_LOG}${NC}"
echo ""
echo -e "  按 ${RED}Ctrl+C${NC} 停止所有服务"
echo ""

# 捕获 Ctrl+C，优雅退出
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"
    if [ -n "${API_PID:-}" ]; then
        kill "$API_PID" 2>/dev/null || true
    fi
    if [ -n "${WEB_PID:-}" ]; then
        kill "$WEB_PID" 2>/dev/null || true
    fi
    lsof -ti:"$WEB_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:"$API_PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 保持运行
wait
