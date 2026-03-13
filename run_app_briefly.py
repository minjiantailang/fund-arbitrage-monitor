#!/usr/bin/env python3
"""
短暂运行应用测试
"""
import sys
import time
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.main_window import MainWindow

class AppRunner:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = MainWindow()

    def start(self):
        """启动应用"""
        self.window.show()
        print("✅ 应用已启动")

        # 5秒后自动退出
        QTimer.singleShot(5000, self.app.quit)

        # 运行应用
        return self.app.exec()

    def test_refresh(self):
        """测试数据刷新"""
        print("测试数据刷新...")
        # 模拟点击刷新按钮
        self.window.refresh_requested.emit()
        print("✅ 刷新请求已发送")

def main():
    print("启动基金套利监控应用...")

    try:
        runner = AppRunner()

        # 在2秒后测试刷新
        QTimer.singleShot(2000, runner.test_refresh)

        # 启动应用
        runner.start()

        print("✅ 应用运行正常")
        return 0

    except Exception as e:
        print(f"❌ 应用运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())