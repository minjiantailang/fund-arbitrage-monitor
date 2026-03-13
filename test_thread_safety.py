#!/usr/bin/env python3
"""
测试数据库线程安全性
"""
import sys
import logging
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

def test_database_in_thread():
    """在线程中测试数据库操作"""
    from src.models.database import get_database
    from src.models.fund_manager import FundManager

    logger = logging.getLogger("thread_test")

    try:
        # 在线程中创建基金管理器和刷新数据
        manager = FundManager("mock")
        result = manager.refresh_all_data()

        logger.info(f"线程中数据刷新结果: {result}")

        # 获取数据
        funds = manager.get_latest_prices()
        logger.info(f"线程中获取到 {len(funds)} 条基金数据")

        manager.close()
        return True

    except Exception as e:
        logger.error(f"线程中数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("数据库线程安全性测试")
    print("=" * 60)

    # 在主线程中测试
    print("1. 在主线程中测试数据库操作...")
    try:
        from src.models.database import get_database
        from src.models.fund_manager import FundManager

        manager = FundManager("mock")
        result = manager.refresh_all_data()
        print(f"   主线程刷新结果: {result['success']}, 基金数: {result['total_funds']}")

        funds = manager.get_latest_prices()
        print(f"   主线程获取到 {len(funds)} 条基金数据")

        manager.close()
        print("   ✅ 主线程测试通过")

    except Exception as e:
        print(f"   ❌ 主线程测试失败: {e}")
        return 1

    # 在多个线程中测试
    print("\n2. 在多个线程中测试数据库操作...")
    threads = []
    results = []

    for i in range(3):
        thread = threading.Thread(
            target=lambda idx=i, res_list=results: res_list.append((idx, test_database_in_thread())),
            name=f"TestThread-{i}"
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 检查结果
    success_count = sum(1 for idx, success in results if success)
    total_count = len(results)

    print(f"   线程测试结果: {success_count}/{total_count} 个线程成功")

    for idx, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   线程 {idx}: {status}")

    if success_count == total_count:
        print("   ✅ 所有线程测试通过")
    else:
        print(f"   ❌ {total_count - success_count} 个线程失败")
        return 1

    print("\n" + "=" * 60)
    print("🎉 数据库线程安全性测试全部通过！")
    return 0

if __name__ == "__main__":
    sys.exit(main())