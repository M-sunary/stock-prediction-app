#!/bin/bash
# 量策 AI - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# 确保 libomp symlink（macOS XGBoost 需要）
if [ "$(uname)" = "Darwin" ]; then
    LIBOMP_PATH=$(find /opt/homebrew/Cellar/libomp -name "libomp.dylib" 2>/dev/null | head -1)
    if [ -n "$LIBOMP_PATH" ] && [ ! -f "/opt/homebrew/lib/libomp.dylib" ]; then
        ln -sf "$LIBOMP_PATH" /opt/homebrew/lib/libomp.dylib 2>/dev/null || true
    fi
fi

echo "启动量策 AI..."
./venv/bin/python3 main.py
