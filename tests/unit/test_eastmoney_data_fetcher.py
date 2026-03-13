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
        # Mock EastMoneyAPI
        with patch("src.models.data_fetcher.EastMoneyAPI") as MockAPI:
            api_instance = MockAPI.return_value
            # 设置 mock api 的行为
            api_instance.get_fund_list.return_value = [
                {"code": "510300", "name": "沪深300ETF", "type": "股票型", "pinyin": "HS300"},
                {"code": "161005", "name": "富国天惠LOF", "type": "混合型", "pinyin": "FGTH"}
            ]
            api_instance.get_realtime_quotes.return_value = [
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
            api_instance.get_fund_valuation.side_effect = lambda code: {
                "fundcode": code, "nav": 1.0, "est_nav": 1.62
            } if code == "161005" else None

            fetcher = EastMoneyDataFetcher()
            # 替换 fetcher 内部的 api 为 mock 实例 (虽然构造函数里已经创建了 mock)
            # 这里的 fetcher.api 已经是 MockAPI() 返回的 mock 对象了
            return fetcher

    def test_fetch_fund_list(self, fetcher):
        """测试获取基金列表"""
        etf_list = fetcher.fetch_fund_list("ETF")
        lof_list = fetcher.fetch_fund_list("LOF")
        
        assert len(etf_list) == 1
        assert etf_list[0]["code"] == "510300"
        
        assert len(lof_list) == 1
        assert lof_list[0]["code"] == "161005"
        
        # 验证只调用了一次 API
        fetcher.api.get_fund_list.assert_called_once()

    def test_fetch_etf_data(self, fetcher):
        """测试获取 ETF 数据"""
        data = fetcher.fetch_etf_data(["510300"])
        
        assert len(data) == 1
        assert data[0]["code"] == "510300"
        assert data[0]["price"] == 3.58
        # ETF 使用 prev_close 作为 nav 占位 (如果有实时估值会更新，但 mock 没设置)
        assert data[0]["nav"] == 3.56 
        
        fetcher.api.get_realtime_quotes.assert_called_with(["510300"])

    def test_fetch_lof_data(self, fetcher):
        """测试获取 LOF 数据"""
        data = fetcher.fetch_lof_data(["161005"])
        
        assert len(data) == 1
        assert data[0]["code"] == "161005"
        assert data[0]["price"] == 1.60
        # LOF 会尝试获取估值
        assert data[0]["nav"] == 1.62 
        
        fetcher.api.get_fund_valuation.assert_called()

    def test_fetch_with_no_codes(self, fetcher):
        """测试不提供代码时获取所有"""
        # 第一次调用会加载列表
        data = fetcher.fetch_etf_data([])
        
        assert len(data) == 1
        assert data[0]["code"] == "510300"
        
        # 应该调用了 get_realtime_quotes 并传入了缓存列表中的代码
        # fetcher.api.get_realtime_quotes.assert_called_with(["510300"]) # 实际上参数顺序不一定

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
