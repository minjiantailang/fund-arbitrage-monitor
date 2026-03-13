#!/usr/bin/env python3
"""
最终应用测试 - 启动应用并测试基本功能
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
from src.ui.main_window import MainWindow

def test_app_startup():
    """测试应用启动"""
    print("测试应用启动...")

    try:
        # 创建应用
        app = QApplication.instance() or QApplication(sys.argv)

        # 创建主窗口
        window = MainWindow()
        window.show()

        print("✅ 应用启动成功")
        print("✅ 主窗口创建成功")

        # 短暂显示后退出
        window.close()

        return True

    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_refresh():
    """测试数据刷新功能"""
    print("\n测试数据刷新功能...")

    try:
        from src.controllers.main_controller import MainController

        controller = MainController()

        # 异步刷新数据
        print("  启动异步数据刷新...")
        result = controller.refresh_all_data()

        if result.get("success"):
            print(f"  ✅ 数据刷新成功: {result['total_funds']} 只基金，{result['total_opportunities']} 个套利机会")

            # 获取统计信息
            stats = controller.get_statistics()
            print(f"  ✅ 统计信息: {stats['total_funds']} 只基金，{stats['opportunity_count']} 个机会")

            controller.cleanup()
            return True
        else:
            print(f"  ❌ 数据刷新失败: {result.get('error', '未知错误')}")
            controller.cleanup()
            return False

    except Exception as e:
        print(f"  ❌ 数据刷新测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("基金套利监控应用 - 最终测试")
    print("=" * 60)

    # 测试1：应用启动
    startup_ok = test_app_startup()

    # 测试2：数据刷新
    refresh_ok = test_data_refresh()

    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  应用启动: {'✅ 通过' if startup_ok else '❌ 失败'}")
    print(f"  数据刷新: {'✅ 通过' if refresh_ok else '❌ 失败'}")

    if startup_ok and refresh_ok:
        print("\n🎉 所有测试通过！应用功能完整。")
        print("\n启动完整应用:")
        print("  venv/bin/python -m src.main")
        print("\n运行演示:")
        print("  python demo.py")
        return 0
    else:
        print("\n⚠️  测试失败，需要修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())