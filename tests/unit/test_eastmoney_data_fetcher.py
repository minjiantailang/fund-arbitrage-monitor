"""
测试 EastMoneyDataFetcher
"""
import pytest
from unittest.mock import Mock, patch
from src.models.data_fetcher import EastMoneyDataFetcher


class TestEastMoneyDataFetcher:
    """测试 EastMoneyDataFetcher 类"""

    @pytest.fixture
    def fetcher(self):
        # 重置单例以避免测试间干扰
        EastMoneyDataFetcher._instance = None
        
        # Mock API
        with patch("src.models.data_fetcher.EastMoneyAPI") as MockEastAPI, \
             patch("src.models.data_fetcher.SinaAPI") as MockSinaAPI, \
             patch("src.models.data_fetcher.get_database") as MockDB:
            
            east_api_instance = MockEastAPI.return_value
            sina_api_instance = MockSinaAPI.return_value
            db_instance = MockDB.return_value
            
            # 设置 mock api 的行为
            east_api_instance.get_fund_list.return_value = [
                {"code": "510300", "name": "沪深300ETF", "type": "股票型", "pinyin": "HS300"},
                {"code": "161005", "name": "富国天惠LOF", "type": "混合型", "pinyin": "FGTH"}
            ]
            
            # 让新浪 API 返回行情数据
            sina_api_instance.get_realtime_quotes.return_value = [
                {
                    "code": "510300", 
                    "name": "沪深300ETF", 
                    "price": 3.58, 
                    "volume": 1000, 
                    "amount": 3580.0,
                    "timestamp": "2023-01-01 10:00:00",
                    "prev_close": 3.56
                },
                {
                    "code": "161005", 
                    "name": "富国天惠LOF", 
                    "price": 1.60, 
                    "volume": 500, 
                    "amount": 800.0,
                    "timestamp": "2023-01-01 10:00:00",
                    "prev_close": 1.58
                }
            ]
            
            # 设置 LOF 估值 Mock
            east_api_instance.get_fund_valuation.side_effect = lambda code: {
                "fundcode": code, "nav": 1.62, "est_nav": 1.63
            } if code == "161005" else None

            # 模拟数据库设置
            db_instance.get_setting.return_value = None
            
            # 手动设置缓存时间戳防止自动清空
            import src.models.data_fetcher as df_mod
            import time
            df_mod._NAV_CACHE_TIME = time.time()
            df_mod._FUND_LIST_CACHE_TIME = time.time()
            
            fetcher = EastMoneyDataFetcher()
            # 预填充净值缓存以测试 ETF 的 NAV 处理
            fetcher._nav_cache["510300"] = 3.55
            return fetcher

    def test_fetch_fund_list(self, fetcher):
        """测试获取基金列表"""
        etf_list = fetcher.fetch_fund_list("ETF")
        lof_list = fetcher.fetch_fund_list("LOF")
        
        assert len(etf_list) == 1
        assert etf_list[0]["code"] == "510300"
        
        assert len(lof_list) == 1
        assert lof_list[0]["code"] == "161005"
        
        # 验证只调用了一次 API 获取列表
        fetcher.api.get_fund_list.assert_called_once()

    def test_fetch_etf_data(self, fetcher):
        """测试获取 ETF 数据"""
        data = fetcher.fetch_etf_data(["510300"])
        
        assert len(data) == 1
        assert data[0]["code"] == "510300"
        assert data[0]["price"] == 3.58
        # 使用预填充的 nav 缓存 (3.55) 而不是 prev_close (3.56)
        assert data[0]["nav"] == 3.55 
        
        # 应该调用新浪 API 获取行情
        fetcher.sina_api.get_realtime_quotes.assert_called_with(["510300"])

    def test_fetch_lof_data(self, fetcher):
        """测试获取 LOF 数据"""
        data = fetcher.fetch_lof_data(["161005"])
        
        assert len(data) == 1
        assert data[0]["code"] == "161005"
        assert data[0]["price"] == 1.60
        # LOF 没有缓存时会通过 get_fund_valuation 获取 nav (1.62)
        assert data[0]["nav"] == 1.62 
        
        fetcher.api.get_fund_valuation.assert_called()

    def test_fetch_with_no_codes(self, fetcher):
        """测试不提供代码时获取所有"""
        data = fetcher.fetch_etf_data([])
        
        assert len(data) == 1
        assert data[0]["code"] == "510300"
        
        # 应该调用了 get_realtime_quotes
        assert fetcher.sina_api.get_realtime_quotes.called

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
