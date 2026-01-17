#!/bin/bash
# Mac 一键启动脚本 - 双击即可运行

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    🔥  抖音热搜监控系统  🔥              ║"
echo "║        正在准备环境，请稍候...            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python！"
    echo ""
    echo "请先安装 Python："
    echo "  方法1: 访问 https://www.python.org/downloads/"
    echo "  方法2: 使用 Homebrew: brew install python3"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo "[1/3] 检测到 Python ✓"

# 检查/创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[2/3] 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败！"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "      虚拟环境创建成功 ✓"
    
    echo "[2/3] 正在安装依赖包（可能需要几分钟）..."
    source venv/bin/activate
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        echo "[错误] 安装依赖失败！"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "      依赖安装完成 ✓"
else
    echo "[2/3] 虚拟环境已存在 ✓"
    source venv/bin/activate
fi

echo "[3/3] 正在启动服务..."
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  服务已启动！                              ║"
echo "║                                            ║"
echo "║  请在浏览器打开:  http://localhost:5001    ║"
echo "║                                            ║"
echo "║  按 Ctrl+C 可停止服务                      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 自动打开浏览器
sleep 2 && open "http://localhost:5001" &

# 启动服务
python run.py
