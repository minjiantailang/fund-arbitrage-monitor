#!/usr/bin/env python3
"""
测试数据模型层功能
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

from src.models.database import get_database
from src.models.arbitrage_calculator import get_calculator
from src.models.data_fetcher import get_data_fetcher
from src.models.fund_manager import get_fund_manager


def test_database():
    """测试数据库功能"""
    print("\n=== 测试数据库功能 ===")

    try:
        # 重置数据库单例
        from src.models.database import _db_instance
        global _db_instance
        if _db_instance:
            _db_instance.close()
            _db_instance = None

        db = get_database(":memory:")  # 使用内存数据库进行测试

        # 测试保存基金信息
        fund_data = {
            "code": "510300",
            "name": "沪深300ETF",
            "type": "ETF",
            "exchange": "SH",
            "currency": "CNY",
            "management_fee": 0.5
        }

        success = db.save_fund(fund_data)
        print(f"保存基金信息: {'成功' if success else '失败'}")

        # 测试获取基金列表
        funds = db.get_funds()
        print(f"获取基金列表: {len(funds)} 条记录")
        if funds:
            print(f"第一条记录: {funds[0]}")

        # 测试保存价格数据
        price_data = {
            "fund_code": "510300",
            "nav": 3.56,
            "price": 3.58,
            "spread_pct": 0.56,
            "yield_pct": 0.43,
            "volume": 1000000,
            "amount": 3580000,
            "timestamp": "2026-01-30T14:30:00"
        }

        success = db.save_fund_price(price_data)
        print(f"保存价格数据: {'成功' if success else '失败'}")

        # 测试获取最新价格
        prices = db.get_latest_prices(["510300"])
        print(f"获取最新价格: {len(prices)} 条记录")
        if prices:
            print(f"价格数据: {prices[0]}")

        db.close()
        print("数据库测试完成")
        return True

    except Exception as e:
        print(f"数据库测试失败: {e}")
        return False


def test_calculator():
    """测试套利计算器"""
    print("\n=== 测试套利计算器 ===")

    try:
        calculator = get_calculator()

        # 测试ETF套利计算
        from decimal import Decimal
        etf_result = calculator.calculate_etf_arbitrage(
            nav=Decimal("3.56"),
            price=Decimal("3.58"),
            fund_code="510300"
        )

        print(f"ETF套利计算结果:")
        print(f"  价差: {etf_result['spread_pct']}%")
        print(f"  净收益: {etf_result['net_yield_pct']}%")
        print(f"  机会等级: {etf_result['opportunity_level']}")
        print(f"  描述: {etf_result['description']}")

        # 测试LOF套利计算
        lof_result = calculator.calculate_lof_arbitrage(
            nav=Decimal("1.56"),
            price=Decimal("1.58"),
            fund_code="161005"
        )

        print(f"\nLOF套利计算结果:")
        print(f"  价差: {lof_result['spread_pct']}%")
        print(f"  净收益: {lof_result['net_yield_pct']}%")
        print(f"  机会等级: {lof_result['opportunity_level']}")
        print(f"  方向: {lof_result['direction']}")

        # 测试费用汇总
        fee_summary = calculator.get_fee_summary()
        print(f"\n费用汇总:")
        for fund_type, fees in fee_summary.items():
            print(f"  {fund_type}: {fees}")

        print("计算器测试完成")
        return True

    except Exception as e:
        print(f"计算器测试失败: {e}")
        return False


def test_data_fetcher():
    """测试数据获取器"""
    print("\n=== 测试数据获取器 ===")

    try:
        fetcher = get_data_fetcher("mock")

        # 测试获取ETF数据
        etf_data = fetcher.fetch_etf_data([])
        print(f"获取ETF数据: {len(etf_data)} 条记录")
        if etf_data:
            print(f"第一条ETF: {etf_data[0]['code']} - {etf_data[0]['name']}")

        # 测试获取LOF数据
        lof_data = fetcher.fetch_lof_data([])
        print(f"获取LOF数据: {len(lof_data)} 条记录")
        if lof_data:
            print(f"第一条LOF: {lof_data[0]['code']} - {lof_data[0]['name']}")

        # 测试获取基金列表
        fund_list = fetcher.fetch_fund_list("ETF")
        print(f"获取ETF基金列表: {len(fund_list)} 条记录")

        fetcher.close()
        print("数据获取器测试完成")
        return True

    except Exception as e:
        print(f"数据获取器测试失败: {e}")
        return False


def test_fund_manager():
    """测试基金管理器"""
    print("\n=== 测试基金管理器 ===")

    try:
        # 直接创建新的基金管理器实例，不使用单例
        from src.models.fund_manager import FundManager
        manager = FundManager("mock")

        # 测试刷新数据
        print("刷新所有基金数据...")
        refresh_result = manager.refresh_all_data()
        print(f"刷新结果: {refresh_result}")

        # 测试获取基金列表
        funds = manager.get_funds()
        print(f"获取基金列表: {len(funds)} 条记录")

        # 测试获取最新价格
        prices = manager.get_latest_prices()
        print(f"获取最新价格: {len(prices)} 条记录")
        if prices:
            print(f"第一条价格数据:")
            for key, value in list(prices[0].items())[:5]:
                print(f"  {key}: {value}")

        # 测试搜索基金
        search_results = manager.search_funds("300")
        print(f"搜索'300': {len(search_results)} 条结果")

        # 测试获取统计信息
        stats = manager.get_statistics()
        print(f"统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        manager.close()
        print("基金管理器测试完成")
        return True

    except Exception as e:
        print(f"基金管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试数据模型层功能...")

    tests = [
        ("数据库", test_database),
        ("套利计算器", test_calculator),
        ("数据获取器", test_data_fetcher),
        ("基金管理器", test_fund_manager),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"执行测试: {test_name}")
        print('='*50)

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试异常: {e}")
            results.append((test_name, False))

    # 输出测试总结
    print("\n" + "="*50)
    print("测试总结:")
    print("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！数据模型层功能正常。")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())