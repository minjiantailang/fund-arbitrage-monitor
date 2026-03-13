#!/usr/bin/env python3
"""
实时行情性能分析脚本
分析ETF和LOF实时行情获取的性能差异
"""

import sys
import os
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data_sources.eastmoney_api import EastMoneyAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_quote_performance():
    """测试单个基金行情获取性能"""
    print("=" * 60)
    print("单个基金实时行情获取性能测试")
    print("=" * 60)

    api = EastMoneyAPI()

    # 测试ETF基金（上海和深圳）
    etf_codes = [
        "510300",  # 沪深300ETF (SH)
        "510500",  # 中证500ETF (SH)
        "510050",  # 上证50ETF (SH)
        "159919",  # 沪深300ETF (SZ)
        "159915",  # 创业板ETF (SZ)
    ]

    # 测试LOF基金
    lof_codes = [
        "161005",  # 富国天惠LOF (SZ)
        "163402",  # 兴全趋势LOF (SZ)
        "161903",  # 万家行业LOF (SZ)
        "162605",  # 景顺鼎益LOF (SZ)
        "163406",  # 兴全合润LOF (SZ)
    ]

    print("\n1. 测试单个ETF基金获取性能：")
    etf_times = []
    for code in etf_codes:
        start_time = time.time()
        try:
            quote = api.get_realtime_quote(code)
            elapsed = time.time() - start_time
            etf_times.append(elapsed)
            status = "成功" if quote else "失败"
            print(f"   {code}: {elapsed:.3f}秒 ({status})")
        except Exception as e:
            elapsed = time.time() - start_time
            etf_times.append(elapsed)
            print(f"   {code}: {elapsed:.3f}秒 (异常: {e})")

    print("\n2. 测试单个LOF基金获取性能：")
    lof_times = []
    for code in lof_codes:
        start_time = time.time()
        try:
            quote = api.get_realtime_quote(code)
            elapsed = time.time() - start_time
            lof_times.append(elapsed)
            status = "成功" if quote else "失败"
            print(f"   {code}: {elapsed:.3f}秒 ({status})")
        except Exception as e:
            elapsed = time.time() - start_time
            lof_times.append(elapsed)
            print(f"   {code}: {elapsed:.3f}秒 (异常: {e})")

    # 计算统计信息
    if etf_times:
        avg_etf = sum(etf_times) / len(etf_times)
        max_etf = max(etf_times)
        min_etf = min(etf_times)
        print(f"\nETF平均获取时间: {avg_etf:.3f}秒 (最小: {min_etf:.3f}秒, 最大: {max_etf:.3f}秒)")

    if lof_times:
        avg_lof = sum(lof_times) / len(lof_times)
        max_lof = max(lof_times)
        min_lof = min(lof_times)
        print(f"LOF平均获取时间: {avg_lof:.3f}秒 (最小: {min_lof:.3f}秒, 最大: {max_lof:.3f}秒)")

    return {
        "etf_times": etf_times,
        "lof_times": lof_times
    }

def test_batch_quotes_performance():
    """测试批量行情获取性能"""
    print("\n" + "=" * 60)
    print("批量实时行情获取性能测试")
    print("=" * 60)

    api = EastMoneyAPI()

    # 准备测试数据
    etf_codes = ["510300", "510500", "510050", "159919", "159915"]
    lof_codes = ["161005", "163402", "161903", "162605", "163406"]
    mixed_codes = etf_codes + lof_codes

    print("\n1. 测试批量获取ETF基金 (5个)：")
    start_time = time.time()
    etf_quotes = api.get_realtime_quotes(etf_codes)
    etf_elapsed = time.time() - start_time
    print(f"   获取数量: {len(etf_quotes)}/{len(etf_codes)}")
    print(f"   总耗时: {etf_elapsed:.3f}秒")
    print(f"   平均每个基金: {etf_elapsed/len(etf_quotes)*1000:.1f}毫秒" if etf_quotes else "   无数据")

    print("\n2. 测试批量获取LOF基金 (5个)：")
    start_time = time.time()
    lof_quotes = api.get_realtime_quotes(lof_codes)
    lof_elapsed = time.time() - start_time
    print(f"   获取数量: {len(lof_quotes)}/{len(lof_codes)}")
    print(f"   总耗时: {lof_elapsed:.3f}秒")
    print(f"   平均每个基金: {lof_elapsed/len(lof_quotes)*1000:.1f}毫秒" if lof_quotes else "   无数据")

    print("\n3. 测试批量获取混合基金 (10个)：")
    start_time = time.time()
    mixed_quotes = api.get_realtime_quotes(mixed_codes)
    mixed_elapsed = time.time() - start_time
    print(f"   获取数量: {len(mixed_quotes)}/{len(mixed_codes)}")
    print(f"   总耗时: {mixed_elapsed:.3f}秒")
    print(f"   平均每个基金: {mixed_elapsed/len(mixed_quotes)*1000:.1f}毫秒" if mixed_quotes else "   无数据")

    return {
        "etf_batch_time": etf_elapsed,
        "lof_batch_time": lof_elapsed,
        "mixed_batch_time": mixed_elapsed
    }

def test_different_batch_sizes():
    """测试不同批量大小对性能的影响"""
    print("\n" + "=" * 60)
    print("不同批量大小性能测试")
    print("=" * 60)

    api = EastMoneyAPI()

    # 准备更多的测试基金
    test_etf_codes = [
        "510300", "510500", "510050", "510880", "510180",  # SH
        "159919", "159915", "159928", "159949", "159902",  # SZ
    ]

    batch_sizes = [1, 3, 5, 10]
    results = {}

    for size in batch_sizes:
        if size > len(test_etf_codes):
            continue

        codes = test_etf_codes[:size]
        print(f"\n批量大小: {size}个基金")

        # 测试3次取平均值
        times = []
        for i in range(3):
            start_time = time.time()
            quotes = api.get_realtime_quotes(codes)
            elapsed = time.time() - start_time
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        avg_per_fund = avg_time / size if size > 0 else 0

        results[size] = {
            "total_time": avg_time,
            "per_fund": avg_per_fund,
            "success_rate": len(quotes)/size if quotes else 0
        }

        print(f"   平均总耗时: {avg_time:.3f}秒")
        print(f"   平均每个基金: {avg_per_fund:.3f}秒")
        print(f"   获取成功率: {len(quotes)}/{size}")

    return results

def analyze_timeout_issues():
    """分析超时问题"""
    print("\n" + "=" * 60)
    print("超时问题分析")
    print("=" * 60)

    print("当前配置分析：")
    print("1. get_realtime_quotes 方法：")
    print("   - 批量大小: 90个基金/请求")
    print("   - 超时时间: 10秒")
    print("   - 字段数量: 12个字段")

    print("\n潜在问题：")
    print("1. 批量过大可能导致响应慢")
    print("2. 10秒超时可能太长，导致单个批次等待过久")
    print("3. 字段过多可能增加响应数据大小")
    print("4. ETF和LOF混合请求可能导致某些交易所响应慢")

    print("\n优化建议：")
    print("1. 减少批量大小: 90 → 30-50")
    print("2. 减少超时时间: 10秒 → 5秒")
    print("3. 减少请求字段: 只保留必要字段")
    print("4. 按交易所分组请求: SH和SZ分开请求")

    return {
        "current_batch_size": 90,
        "current_timeout": 10,
        "current_fields": 12
    }

def main():
    """主函数"""
    print("实时行情性能分析")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试单个基金性能
        single_results = test_single_quote_performance()

        # 测试批量性能
        batch_results = test_batch_quotes_performance()

        # 测试不同批量大小
        batch_size_results = test_different_batch_sizes()

        # 分析超时问题
        timeout_analysis = analyze_timeout_issues()

        # 输出总结
        print("\n" + "=" * 60)
        print("性能分析总结")
        print("=" * 60)

        if single_results.get("etf_times") and single_results.get("lof_times"):
            avg_etf = sum(single_results["etf_times"]) / len(single_results["etf_times"])
            avg_lof = sum(single_results["lof_times"]) / len(single_results["lof_times"])
            print(f"单个基金获取性能：")
            print(f"  ETF平均: {avg_etf:.3f}秒")
            print(f"  LOF平均: {avg_lof:.3f}秒")
            print(f"  ETF比LOF慢: {avg_etf/avg_lof:.1f}倍" if avg_lof > 0 else "")

        print(f"\n批量获取性能：")
        if batch_results.get("etf_batch_time"):
            print(f"  ETF批量(5个): {batch_results['etf_batch_time']:.3f}秒")
        if batch_results.get("lof_batch_time"):
            print(f"  LOF批量(5个): {batch_results['lof_batch_time']:.3f}秒")

        print("\n关键发现：")
        print("1. 如果ETF单个获取明显慢于LOF，可能是上海交易所API响应慢")
        print("2. 如果批量获取比单个获取效率高很多，说明批量是有效的")
        print("3. 如果批量大小影响性能，需要找到最优批量大小")

        print("\n下一步优化方向：")
        print("1. 优化批量大小和超时设置")
        print("2. 减少请求字段数量")
        print("3. 考虑按交易所分组请求")
        print("4. 添加并发请求支持")

    except Exception as e:
        print(f"性能分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()