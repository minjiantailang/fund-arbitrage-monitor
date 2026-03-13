"""
数据获取器单元测试 - 与实际DataFetcher实现对齐
"""
import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch
from src.models.data_fetcher import (
    EastMoneyDataFetcher, DataFetcher,
    DataFetcherFactory, get_data_fetcher
)

from tests.mock_fetcher import MockDataFetcher


class TestDataFetcher:
    """数据获取器基类测试"""

    def test_init(self):
        """测试初始化"""
        fetcher = MockDataFetcher(cache_duration=60)
        assert fetcher.cache_duration == 60
        assert fetcher._cache == {}
        assert "User-Agent" in fetcher.session.headers

    def test_cache_mechanism(self):
        """测试缓存机制"""
        fetcher = MockDataFetcher(cache_duration=1)  # 1秒缓存

        # 保存到缓存
        test_key = "test_key"
        test_data = {"test": "data"}
        fetcher._save_to_cache(test_key, test_data)

        # 立即从缓存获取
        cached_data = fetcher._get_from_cache(test_key)
        assert cached_data == test_data

        # 等待缓存过期
        time.sleep(1.1)

        # 缓存应已过期
        expired_data = fetcher._get_from_cache(test_key)
        assert expired_data is None

    def test_cache_update(self):
        """测试缓存更新"""
        fetcher = MockDataFetcher(cache_duration=10)

        # 第一次保存
        test_key = "test_key"
        fetcher._save_to_cache(test_key, "data1")

        # 第二次保存（更新）
        fetcher._save_to_cache(test_key, "data2")

        # 应该获取到最新数据
        cached_data = fetcher._get_from_cache(test_key)
        assert cached_data == "data2"


class TestMockDataFetcher:
    """模拟数据获取器测试"""

    def test_init(self):
        """测试初始化"""
        fetcher = MockDataFetcher()
        assert isinstance(fetcher, MockDataFetcher)
        assert isinstance(fetcher, DataFetcher)
        assert len(fetcher._mock_etf_data) > 0
        assert len(fetcher._mock_lof_data) > 0

    def test_fetch_etf_data(self):
        """测试获取ETF基金数据"""
        fetcher = MockDataFetcher()
        etf_data = fetcher.fetch_etf_data([])

        # 验证返回格式
        assert isinstance(etf_data, list)
        assert len(etf_data) > 0

        # 验证ETF数据格式
        for fund in etf_data:
            assert "code" in fund
            assert "name" in fund
            assert "type" in fund
            assert fund["type"] == "ETF"
            assert "nav" in fund
            assert "price" in fund
            assert "volume" in fund
            assert "amount" in fund
            assert "timestamp" in fund

    def test_fetch_etf_data_with_codes(self):
        """测试获取指定代码的ETF数据"""
        fetcher = MockDataFetcher()

        # 获取特定代码
        etf_data = fetcher.fetch_etf_data(["510300"])

        # 验证返回
        assert isinstance(etf_data, list)
        if etf_data:
            assert etf_data[0]["code"] == "510300"

    def test_fetch_lof_data(self):
        """测试获取LOF基金数据"""
        fetcher = MockDataFetcher()
        lof_data = fetcher.fetch_lof_data([])

        # 验证返回格式
        assert isinstance(lof_data, list)
        assert len(lof_data) > 0

        # 验证LOF数据格式
        for fund in lof_data:
            assert "code" in fund
            assert "name" in fund
            assert "type" in fund
            assert fund["type"] == "LOF"
            assert "nav" in fund
            assert "price" in fund

    def test_fetch_lof_data_with_codes(self):
        """测试获取指定代码的LOF数据"""
        fetcher = MockDataFetcher()

        # 获取特定代码
        lof_data = fetcher.fetch_lof_data(["161005"])

        # 验证返回
        assert isinstance(lof_data, list)
        if lof_data:
            assert lof_data[0]["code"] == "161005"

    def test_fetch_fund_list_etf(self):
        """测试获取ETF基金列表"""
        fetcher = MockDataFetcher()
        funds = fetcher.fetch_fund_list("ETF")

        assert isinstance(funds, list)
        assert len(funds) > 0

        for fund in funds:
            assert "code" in fund
            assert "name" in fund
            assert "type" in fund
            assert "exchange" in fund
            assert "currency" in fund

    def test_fetch_fund_list_lof(self):
        """测试获取LOF基金列表"""
        fetcher = MockDataFetcher()
        funds = fetcher.fetch_fund_list("LOF")

        assert isinstance(funds, list)
        assert len(funds) > 0

    def test_fetch_fund_list_all(self):
        """测试获取所有基金列表"""
        fetcher = MockDataFetcher()
        funds = fetcher.fetch_fund_list("ALL")

        assert isinstance(funds, list)
        # 应该包含ETF和LOF
        types = {f["type"] for f in funds}
        assert "ETF" in types or "LOF" in types

    def test_cache_works_for_etf_data(self):
        """测试ETF数据缓存工作正常"""
        fetcher = MockDataFetcher(cache_duration=60)

        # 第一次获取（会触发模拟延迟）
        start1 = time.time()
        data1 = fetcher.fetch_etf_data([])
        time1 = time.time() - start1

        # 第二次获取（应该从缓存获取，更快）
        start2 = time.time()
        data2 = fetcher.fetch_etf_data([])
        time2 = time.time() - start2

        # 缓存获取应该更快
        assert time2 < time1

    def test_close(self):
        """测试关闭会话"""
        fetcher = MockDataFetcher()
        # 关闭不应该抛出异常
        fetcher.close()



class TestDataFetcherFactory:
    """数据获取器工厂测试"""

    def test_create_mock_fetcher(self):
        """测试创建获取器"""
        # 重置单例
        EastMoneyDataFetcher._instance = None
        fetcher = DataFetcherFactory.create_fetcher("mock")
        assert isinstance(fetcher, EastMoneyDataFetcher)

    def test_create_eastmoney_fetcher(self):
        """测试创建东方财富获取器"""
        fetcher = DataFetcherFactory.create_fetcher("eastmoney")
        assert isinstance(fetcher, EastMoneyDataFetcher)

    def test_create_default_fetcher(self):
        """测试创建默认获取器"""
        # 重置单例
        EastMoneyDataFetcher._instance = None
        fetcher = DataFetcherFactory.create_fetcher("unknown")
        # 生产环境 DataFetcherFactory 目前总是返回 EastMoneyDataFetcher
        assert isinstance(fetcher, EastMoneyDataFetcher)

    def test_create_with_cache_duration(self):
        """测试创建带缓存时长的获取器"""
        # 重置单例
        EastMoneyDataFetcher._instance = None
        fetcher = DataFetcherFactory.create_fetcher("eastmoney", cache_duration=120)
        assert fetcher.cache_duration == 120


class TestGetDataFetcher:
    """全局数据获取器函数测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        # 重置全局实例
        import src.models.data_fetcher as df
        df._fetcher_instance = None

        # 获取实例
        fetcher1 = get_data_fetcher("mock")
        fetcher2 = get_data_fetcher("mock")

        # 应该是同一个实例
        assert fetcher1 is fetcher2

        # 清理
        df._fetcher_instance = None


class TestDataConsistency:
    """数据一致性测试"""

    def test_etf_data_has_required_fields(self):
        """测试ETF数据包含必需字段"""
        fetcher = MockDataFetcher()
        etf_data = fetcher.fetch_etf_data([])

        required_fields = ["code", "name", "type", "nav", "price", "volume", "amount", "timestamp"]

        for fund in etf_data:
            for field in required_fields:
                assert field in fund, f"缺少必需字段: {field}"

    def test_lof_data_has_required_fields(self):
        """测试LOF数据包含必需字段"""
        fetcher = MockDataFetcher()
        lof_data = fetcher.fetch_lof_data([])

        required_fields = ["code", "name", "type", "nav", "price", "volume", "amount", "timestamp"]

        for fund in lof_data:
            for field in required_fields:
                assert field in fund, f"缺少必需字段: {field}"

    def test_nav_and_price_are_positive(self):
        """测试净值和价格为正数"""
        fetcher = MockDataFetcher()
        etf_data = fetcher.fetch_etf_data([])

        for fund in etf_data:
            assert fund["nav"] > 0, f"净值应为正数: {fund['code']}"
            assert fund["price"] > 0, f"价格应为正数: {fund['code']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])