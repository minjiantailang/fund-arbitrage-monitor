#!/usr/bin/env python3
"""
性能测试脚本 - 测量东方财富数据获取性能
"""

import sys
import os
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.data_fetcher import DataFetcherFactory
from src.models.fund_manager import FundManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_eastmoney_fetcher_performance():
    """测试东方财富数据获取器性能"""
    print("=" * 60)
    print("东方财富数据获取器性能测试")
    print("=" * 60)

    # 创建数据获取器
    print("1. 创建东方财富数据获取器...")
    start_time = time.time()
    fetcher = DataFetcherFactory.create_fetcher("eastmoney")
    creation_time = time.time() - start_time
    print(f"   创建时间: {creation_time:.2f}秒")

    # 测试基金列表获取
    print("\n2. 测试基金列表获取...")
    start_time = time.time()
    try:
        fund_list = fetcher.fetch_fund_list("ETF")
        list_time = time.time() - start_time
        print(f"   ETF基金数量: {len(fund_list)}")
        print(f"   获取时间: {list_time:.2f}秒")
        print(f"   平均每个基金: {list_time/len(fund_list)*1000:.1f}毫秒")
    except Exception as e:
        print(f"   获取失败: {e}")
        list_time = 0

    # 测试ETF数据获取（少量）
    print("\n3. 测试少量ETF数据获取...")
    test_codes = ["510300", "510500", "510050", "159919", "159915"]
    start_time = time.time()
    try:
        etf_data = fetcher.fetch_etf_data(test_codes)
        etf_time = time.time() - start_time
        print(f"   获取数量: {len(etf_data)}/{len(test_codes)}")
        print(f"   获取时间: {etf_time:.2f}秒")
        print(f"   平均每个基金: {etf_time/len(etf_data)*1000:.1f}毫秒")
    except Exception as e:
        print(f"   获取失败: {e}")
        etf_time = 0

    # 测试LOF数据获取（少量）
    print("\n4. 测试少量LOF数据获取...")
    test_codes = ["161005", "163402", "161903", "162605", "163406"]
    start_time = time.time()
    try:
        lof_data = fetcher.fetch_lof_data(test_codes)
        lof_time = time.time() - start_time
        print(f"   获取数量: {len(lof_data)}/{len(test_codes)}")
        print(f"   获取时间: {lof_time:.2f}秒")
        print(f"   平均每个基金: {lof_time/len(lof_data)*1000:.1f}毫秒")
    except Exception as e:
        print(f"   获取失败: {e}")
        lof_time = 0

    # 清理资源
    fetcher.close()

    return {
        "creation_time": creation_time,
        "list_time": list_time,
        "etf_time": etf_time,
        "lof_time": lof_time,
        "total_time": creation_time + list_time + etf_time + lof_time
    }

def test_fund_manager_performance():
    """测试基金管理器性能"""
    print("\n" + "=" * 60)
    print("基金管理器性能测试")
    print("=" * 60)

    # 创建基金管理器
    print("1. 创建基金管理器...")
    start_time = time.time()
    manager = FundManager(fetcher_type="eastmoney")
    creation_time = time.time() - start_time
    print(f"   创建时间: {creation_time:.2f}秒")

    # 测试刷新少量数据
    print("\n2. 测试刷新少量基金数据...")
    test_codes = ["510300", "510500", "161005", "163402"]
    start_time = time.time()
    try:
        result = manager.refresh_fund_data(test_codes)
        refresh_time = time.time() - start_time
        print(f"   处理基金数: {result.get('processed_funds', 0)}")
        print(f"   套利机会数: {result.get('total_opportunities', 0)}")
        print(f"   总耗时: {result.get('elapsed_seconds', 0):.2f}秒")
        print(f"   实际耗时: {refresh_time:.2f}秒")
    except Exception as e:
        print(f"   刷新失败: {e}")
        refresh_time = 0

    # 测试获取最新价格
    print("\n3. 测试获取最新价格...")
    start_time = time.time()
    try:
        prices = manager.get_latest_prices(test_codes)
        prices_time = time.time() - start_time
        print(f"   获取价格数: {len(prices)}")
        print(f"   获取时间: {prices_time:.2f}秒")
    except Exception as e:
        print(f"   获取失败: {e}")
        prices_time = 0

    # 清理资源
    manager.close()

    return {
        "creation_time": creation_time,
        "refresh_time": refresh_time,
        "prices_time": prices_time,
        "total_time": creation_time + refresh_time + prices_time
    }

def test_mock_fetcher_performance():
    """测试模拟数据获取器性能（作为基准）"""
    print("\n" + "=" * 60)
    print("模拟数据获取器性能测试（基准）")
    print("=" * 60)

    # 创建模拟数据获取器
    print("1. 创建模拟数据获取器...")
    start_time = time.time()
    fetcher = DataFetcherFactory.create_fetcher("mock")
    creation_time = time.time() - start_time
    print(f"   创建时间: {creation_time:.2f}秒")

    # 测试基金列表获取
    print("\n2. 测试基金列表获取...")
    start_time = time.time()
    fund_list = fetcher.fetch_fund_list("ETF")
    list_time = time.time() - start_time
    print(f"   ETF基金数量: {len(fund_list)}")
    print(f"   获取时间: {list_time:.2f}秒")

    # 测试ETF数据获取
    print("\n3. 测试ETF数据获取...")
    start_time = time.time()
    etf_data = fetcher.fetch_etf_data([])
    etf_time = time.time() - start_time
    print(f"   获取数量: {len(etf_data)}")
    print(f"   获取时间: {etf_time:.2f}秒")

    # 测试LOF数据获取
    print("\n4. 测试LOF数据获取...")
    start_time = time.time()
    lof_data = fetcher.fetch_lof_data([])
    lof_time = time.time() - start_time
    print(f"   获取数量: {len(lof_data)}")
    print(f"   获取时间: {lof_time:.2f}秒")

    # 清理资源
    fetcher.close()

    return {
        "creation_time": creation_time,
        "list_time": list_time,
        "etf_time": etf_time,
        "lof_time": lof_time,
        "total_time": creation_time + list_time + etf_time + lof_time
    }

def main():
    """主函数"""
    print("基金套利监控应用性能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    try:
        # 测试模拟数据获取器（基准）
        results["mock"] = test_mock_fetcher_performance()
    except Exception as e:
        print(f"模拟数据获取器测试失败: {e}")
        results["mock"] = None

    try:
        # 测试东方财富数据获取器
        results["eastmoney"] = test_eastmoney_fetcher_performance()
    except Exception as e:
        print(f"东方财富数据获取器测试失败: {e}")
        results["eastmoney"] = None

    try:
        # 测试基金管理器
        results["manager"] = test_fund_manager_performance()
    except Exception as e:
        print(f"基金管理器测试失败: {e}")
        results["manager"] = None

    # 输出总结
    print("\n" + "=" * 60)
    print("性能测试总结")
    print("=" * 60)

    if results.get("mock"):
        print(f"模拟数据获取器总耗时: {results['mock']['total_time']:.2f}秒")

    if results.get("eastmoney"):
        print(f"东方财富数据获取器总耗时: {results['eastmoney']['total_time']:.2f}秒")
        if results.get("mock"):
            slowdown = results['eastmoney']['total_time'] / results['mock']['total_time'] if results['mock']['total_time'] > 0 else 0
            print(f"相比模拟数据慢: {slowdown:.1f}倍")

    if results.get("manager"):
        print(f"基金管理器总耗时: {results['manager']['total_time']:.2f}秒")

    print("\n建议：")
    print("1. 如果东方财富API测试失败，可能是网络问题或API限制")
    print("2. 如果耗时过长，考虑优化缓存策略和并发处理")
    print("3. 建议在实际使用场景中测试完整数据刷新")

if __name__ == "__main__":
    main()