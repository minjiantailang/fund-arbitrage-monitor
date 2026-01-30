#!/usr/bin/env python3
"""
测试应用启动
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

def test_imports():
    """测试导入"""
    print("测试模块导入...")

    modules_to_test = [
        ("src.ui.main_window", "MainWindow"),
        ("src.ui.dashboard_widget", "DashboardWidget"),
        ("src.ui.fund_list_widget", "FundListWidget"),
        ("src.ui.filters_widget", "FiltersWidget"),
        ("src.controllers.main_controller", "MainController"),
    ]

    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_path}.{class_name}")
        except Exception as e:
            print(f"❌ {module_path}.{class_name}: {e}")
            return False

    return True

def test_controller():
    """测试控制器"""
    print("\n测试控制器...")

    try:
        from src.controllers.main_controller import MainController
        controller = MainController()

        # 测试获取统计信息
        stats = controller.get_statistics()
        print(f"✅ 控制器初始化成功")
        print(f"   统计信息: {stats}")

        # 测试获取基金数据
        funds = controller.get_all_funds()
        print(f"✅ 获取基金数据: {len(funds)} 条记录")

        controller.cleanup()
        return True

    except Exception as e:
        print(f"❌ 控制器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_creation():
    """测试UI创建"""
    print("\n测试UI创建...")

    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow

        # 创建应用实例（不显示）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # 创建主窗口
        window = MainWindow()
        print(f"✅ 主窗口创建成功")

        # 测试窗口属性
        print(f"   窗口标题: {window.windowTitle()}")
        print(f"   窗口大小: {window.width()}x{window.height()}")

        # 不显示窗口，直接关闭
        window.close()
        return True

    except Exception as e:
        print(f"❌ UI创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("基金套利监控应用 - 启动测试")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("控制器", test_controller),
        ("UI创建", test_ui_creation),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"执行测试: {test_name}")
        print('='*40)

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试异常: {e}")
            results.append((test_name, False))

    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！应用可以正常启动。")
        print("\n启动命令: python -m src.main")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())