#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ -d "venv" ]; then
    echo "正在激活虚拟环境..."
    source venv/bin/activate
else
    echo "警告: 未找到虚拟环境 (venv)，将尝试使用系统 Python"
fi

# 设置 PYTHONPATH以包含项目根目录
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 运行主程序
echo "正在启动基金套利监控..."
python3 -m src.main
