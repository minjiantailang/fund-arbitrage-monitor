import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ["build", "dist"]
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            shutil.rmtree(d)

def build_app():
    """使用PyInstaller构建应用"""
    print("Starting build process...")
    
    # 确定分隔符
    sep = os.pathsep
    
    # 基本命令参数
    cmd = [
        "pyinstaller",
        "--name=fund-arbitrage-monitor",
        "--noconfirm",
        "--windowed",  # 无控制台窗口
        "--clean",
    ]
    
    # 添加数据文件（如果有assets目录）
    if os.path.exists("assets"):
        if platform.system() == "Windows":
            cmd.append("--add-data=assets;assets")
        else:
            cmd.append("--add-data=assets:assets")
            
    # 入口脚本
    cmd.append("src/main.py")
    
    # 执行命令
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("Build successful!")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

def post_build_cleanup():
    """构建后清理（可选）"""
    # 可以在这里移动构建产物或进行其他清理
    pass

if __name__ == "__main__":
    # 确保在项目根目录运行
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    clean_build_dirs()
    build_app()
    post_build_cleanup()
    
    print(f"\nExecutable can be found in: {os.path.join(project_root, 'dist')}")