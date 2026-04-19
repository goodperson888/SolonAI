#!/bin/bash

# =============================================
# Solon AI - 一键启动脚本
# 同时启动：前端 + 后端API + AI服务
# =============================================

set -e

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
VENV_PYTHON="$API_DIR/.venv/bin/python"

# ===== 检查环境 =====
echo -e "${YELLOW}[1/4] 检查环境...${NC}"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 未安装 Node.js，请先安装: https://nodejs.org${NC}"
    exit 1
fi
echo -e "  ✅ Node.js $(node -v)"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未安装 Python3${NC}"
    exit 1
fi
echo -e "  ✅ Python $(python3 --version)"

if [ "$DB_MODE" = "sqlite" ]; then
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./solon_ai.db}"
elif [ "$DB_MODE" = "postgres" ]; then
    export DATABASE_URL="${DATABASE_URL:-postgresql://solon:solon_password@localhost:5432/solon_ai}"
else
    echo -e "${RED}❌ 不支持的 SOLON_DB_MODE: $DB_MODE${NC}"
    echo -e "  可选值: sqlite / postgres"
    exit 1
fi
echo -e "  ✅ 数据库模式: ${BLUE}$DB_MODE${NC}"

# 检查 AI 服务的 .env 文件
if [ ! -f "$ROOT_DIR/services/ai-agents/.env" ]; then
    echo -e "${YELLOW}  ⚠️  未找到 AI 服务配置文件，复制模板...${NC}"
    cp "$ROOT_DIR/services/ai-agents/.env.example" "$ROOT_DIR/services/ai-agents/.env"
    echo -e "${YELLOW}  ⚠️  请编辑 services/ai-agents/.env 填写你的大模型 API Key${NC}"
fi

# ===== 安装依赖 =====
echo -e "${YELLOW}[2/4] 检查依赖...${NC}"

# 前端依赖
if [ ! -d "$ROOT_DIR/apps/web/node_modules" ]; then
    echo -e "  📦 安装前端依赖..."
    cd "$ROOT_DIR" && npm install
else
    echo -e "  ✅ 前端依赖已安装"
fi

# 后端依赖
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}  ⚠️  未找到 apps/api/.venv，请先创建虚拟环境并安装依赖${NC}"
    echo -e "     cd apps/api && python3.11 -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt"
    exit 1
fi

echo -e "  ✅ 使用虚拟环境: $VENV_PYTHON"
echo -e "  ✅ 所有依赖请通过 apps/api/.venv 维护"

# ===== 启动服务 =====
echo -e "${YELLOW}[3/4] 启动服务...${NC}"

# 添加 Python 用户安装路径
export PATH="$PATH:$HOME/Library/Python/3.9/bin:$HOME/.local/bin"

# 清理之前的进程
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:3001 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true

# 启动后端 API（端口 8000）
echo -e "  🚀 启动后端 API (http://localhost:8000)..."
cd "$API_DIR"
PYTHONPATH="$ROOT_DIR/services/ai-agents:$PYTHONPATH" "$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 等待后端启动
sleep 2

# 启动前端（端口 3000）
echo -e "  🚀 启动前端 (http://localhost:3000)..."
cd "$ROOT_DIR/apps/web"
npx next dev -p 3000 &
WEB_PID=$!

# ===== 启动完成 =====
sleep 3
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ Solon AI 启动完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  🗄️  数据库:   ${BLUE}$DB_MODE${NC}"
echo -e "  🌐 前端:     ${BLUE}http://localhost:3000${NC}"
echo -e "  🔌 后端API:  ${BLUE}http://localhost:8000${NC}"
echo -e "  📚 API文档:  ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "  按 ${RED}Ctrl+C${NC} 停止所有服务"
echo ""

# 捕获 Ctrl+C，优雅退出
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"
    kill $API_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
    lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 保持运行
wait
