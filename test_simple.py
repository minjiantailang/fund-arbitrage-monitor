#!/usr/bin/env python3
"""
简单测试数据模型层
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.database import Database
from src.models.arbitrage_calculator import ArbitrageCalculator
from src.models.data_fetcher import MockDataFetcher
from src.models.fund_manager import FundManager


def main():
    print("简单测试数据模型层...")

    # 测试1: 数据库
    print("\n1. 测试数据库...")
    try:
        db = Database(":memory:")
        print("✅ 数据库初始化成功")
        db.close()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

    # 测试2: 计算器
    print("\n2. 测试套利计算器...")
    try:
        calculator = ArbitrageCalculator()
        result = calculator.calculate_etf_arbitrage(3.56, 3.58, "510300")
        print(f"✅ 套利计算成功: 价差={result['spread_pct']}%")
    except Exception as e:
        print(f"❌ 套利计算失败: {e}")

    # 测试3: 数据获取器
    print("\n3. 测试数据获取器...")
    try:
        fetcher = MockDataFetcher()
        data = fetcher.fetch_etf_data([])
        print(f"✅ 数据获取成功: {len(data)} 条记录")
        fetcher.close()
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")

    # 测试4: 基金管理器（简化）
    print("\n4. 测试基金管理器（简化）...")
    try:
        manager = FundManager("mock")
        print("✅ 基金管理器初始化成功")

        # 测试基本功能
        funds = manager.get_funds()
        print(f"✅ 获取基金列表: {len(funds)} 条记录")

        manager.close()
        print("✅ 基金管理器测试完成")
    except Exception as e:
        print(f"❌ 基金管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n测试完成！")


if __name__ == "__main__":
    main()