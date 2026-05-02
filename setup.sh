#!/bin/bash
set -e

echo "========================================"
echo "NoteAgents 项目初始化脚本 (使用 uv)"
echo "========================================"
echo ""

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "[错误] 未检测到 uv，请先安装 uv"
    echo "安装方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "或者: pip install uv"
    echo ""
    exit 1
fi

echo "[1/5] 检查 Python 版本..."
python --version
echo ""

echo "[2/5] 创建虚拟环境 (使用 uv)..."
if [ -d ".venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    uv venv .venv
fi
echo ""

echo "[3/5] 激活虚拟环境..."
source .venv/bin/activate
echo ""

echo "[4/5] 安装依赖 (使用 uv)..."
uv pip install -r requirements.txt
echo ""

echo "[5/5] 安装开发依赖 (可选)..."
uv pip install pytest pytest-asyncio pytest-cov
echo ""

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "创建 .env 配置文件..."
    cp .env.example .env
    echo "[提示] 请编辑 .env 文件配置您的 API 密钥和其他设置"
    echo ""
fi

echo "========================================"
echo "初始化完成！"
echo "========================================"
echo ""
echo "常用命令:"
echo "  激活环境: source .venv/bin/activate"
echo "  运行测试: pytest"
echo "  运行程序: python main.py"
echo ""
