#!/usr/bin/env python3
"""
基金套利监控应用 - 功能演示
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

def demo_data_models():
    """演示数据模型功能"""
    print("\n" + "="*60)
    print("数据模型层功能演示")
    print("="*60)

    try:
        from src.models.fund_manager import FundManager

        print("1. 创建基金管理器...")
        manager = FundManager("mock")

        print("2. 刷新基金数据...")
        result = manager.refresh_all_data()
        print(f"   刷新结果: {result}")

        print("3. 获取统计信息...")
        stats = manager.get_statistics()
        print(f"   总基金数: {stats['total_funds']}")
        print(f"   ETF基金: {stats['etf_count']}")
        print(f"   LOF基金: {stats['lof_count']}")
        print(f"   套利机会: {stats['opportunity_count']}")
        print(f"   平均价差: {stats['avg_spread']}%")

        print("4. 获取基金列表...")
        funds = manager.get_latest_prices()
        print(f"   获取到 {len(funds)} 条基金数据")

        if funds:
            print("\n   前3只基金信息:")
            for i, fund in enumerate(funds[:3]):
                print(f"   {i+1}. {fund.get('fund_code', 'N/A')} - {fund.get('name', 'N/A')}")
                print(f"      类型: {fund.get('type', 'N/A')}, 净值: {fund.get('nav', 'N/A')}")
                print(f"      价格: {fund.get('price', 'N/A')}, 价差: {fund.get('spread_pct', 'N/A')}%")
                print(f"      机会等级: {fund.get('opportunity_level', 'N/A')}")

        print("5. 搜索基金...")
        search_results = manager.search_funds("300")
        print(f"   搜索'300'找到 {len(search_results)} 条结果")

        manager.close()
        print("\n✅ 数据模型层演示完成")
        return True

    except Exception as e:
        print(f"\n❌ 数据模型层演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_controllers():
    """演示控制器功能"""
    print("\n" + "="*60)
    print("控制器层功能演示")
    print("="*60)

    try:
        from src.controllers.main_controller import MainController

        print("1. 创建主控制器...")
        controller = MainController()

        print("2. 获取统计信息...")
        stats = controller.get_statistics()
        print(f"   统计信息: {stats}")

        print("3. 获取基金数据...")
        funds = controller.get_all_funds()
        print(f"   基金数据: {len(funds)} 条记录")

        print("4. 应用筛选条件...")
        filter_params = {
            "fund_type": "all",
            "min_spread": -5.0,
            "max_spread": 5.0,
            "opportunity_levels": ["excellent", "good", "weak"],
            "sort_by": "spread_pct_desc",
            "only_opportunities": False,
        }

        filtered_funds = controller.apply_filters(filter_params)
        print(f"   筛选后数据: {len(filtered_funds)} 条记录")

        print("5. 搜索基金...")
        search_results = controller.search_funds("ETF")
        print(f"   搜索'ETF'找到 {len(search_results)} 条结果")

        controller.cleanup()
        print("\n✅ 控制器层演示完成")
        return True

    except Exception as e:
        print(f"\n❌ 控制器层演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_arbitrage_calculation():
    """演示套利计算功能"""
    print("\n" + "="*60)
    print("套利计算功能演示")
    print("="*60)

    try:
        from src.models.arbitrage_calculator import get_calculator
        from decimal import Decimal

        calculator = get_calculator()

        print("1. ETF套利计算示例:")
        etf_result = calculator.calculate_etf_arbitrage(
            nav=Decimal("3.56"),
            price=Decimal("3.58"),
            fund_code="510300"
        )
        print(f"   基金: {etf_result['fund_code']}")
        print(f"   净值: {etf_result['nav']}, 价格: {etf_result['price']}")
        print(f"   价差: {etf_result['spread_pct']}%")
        print(f"   净收益: {etf_result['net_yield_pct']}%")
        print(f"   机会等级: {etf_result['opportunity_level']}")
        print(f"   描述: {etf_result['description']}")

        print("\n2. LOF套利计算示例:")
        lof_result = calculator.calculate_lof_arbitrage(
            nav=Decimal("1.56"),
            price=Decimal("1.58"),
            fund_code="161005"
        )
        print(f"   基金: {lof_result['fund_code']}")
        print(f"   净值: {lof_result['nav']}, 价格: {lof_result['price']}")
        print(f"   价差: {lof_result['spread_pct']}%")
        print(f"   净收益: {lof_result['net_yield_pct']}%")
        print(f"   机会等级: {lof_result['opportunity_level']}")
        print(f"   方向: {lof_result['direction']}")

        print("\n3. 交易费用汇总:")
        fee_summary = calculator.get_fee_summary()
        for fund_type, fees in fee_summary.items():
            print(f"   {fund_type}: {fees}")

        print("\n✅ 套利计算演示完成")
        return True

    except Exception as e:
        print(f"\n❌ 套利计算演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主演示函数"""
    print("基金套利监控应用 - 功能演示")
    print("="*60)

    demos = [
        ("数据模型层", demo_data_models),
        ("控制器层", demo_controllers),
        ("套利计算", demo_arbitrage_calculation),
    ]

    results = []
    for demo_name, demo_func in demos:
        try:
            success = demo_func()
            results.append((demo_name, success))
        except Exception as e:
            print(f"{demo_name}演示异常: {e}")
            results.append((demo_name, False))

    # 输出演示总结
    print("\n" + "="*60)
    print("演示总结:")
    print("="*60)

    total_demos = len(results)
    passed_demos = sum(1 for _, success in results if success)

    for demo_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{demo_name}: {status}")

    print(f"\n总计: {passed_demos}/{total_demos} 个演示通过")

    if passed_demos == total_demos:
        print("\n🎉 所有功能演示通过！应用核心功能正常。")
        print("\n启动GUI应用: python -m src.main")
        return 0
    else:
        print(f"\n⚠️  {total_demos - passed_demos} 个演示失败，需要检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())