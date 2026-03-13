from src.models.data_fetcher import DataFetcher

class MockDataFetcher(DataFetcher):
    """模拟数据获取器，用于测试"""
    def __init__(self, cache_duration: int = 300):
        super().__init__(cache_duration)
        self._mock_etf_data = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF", "nav": 3.5, "price": 3.51, "volume": 10000, "amount": 35000, "timestamp": "2023-01-01 15:00:00"}
        ]
        self._mock_lof_data = [
            {"code": "161005", "name": "富国天惠", "type": "LOF", "nav": 2.5, "price": 2.45, "volume": 5000, "amount": 12500, "timestamp": "2023-01-01 15:00:00"}
        ]
        
    def fetch_etf_data(self, fund_codes):
        # 检查缓存
        cache_key = f"etf_{','.join(sorted(fund_codes))}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        # 模拟网络延迟
        import time
        time.sleep(0.01)
        
        if not fund_codes:
            data = self._mock_etf_data
        else:
            data = [f for f in self._mock_etf_data if f["code"] in fund_codes]
            
        # 保存到缓存
        self._save_to_cache(cache_key, data)
        return data
        
    def fetch_lof_data(self, fund_codes):
        # 检查缓存
        cache_key = f"lof_{','.join(sorted(fund_codes))}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        # 模拟网络延迟
        import time
        time.sleep(0.01)
        
        if not fund_codes:
            data = self._mock_lof_data
        else:
            data = [f for f in self._mock_lof_data if f["code"] in fund_codes]
            
        # 保存到缓存
        self._save_to_cache(cache_key, data)
        return data
        
    def fetch_fund_list(self, fund_type):
        if fund_type == "ETF":
            return [{"code": "510300", "name": "沪深300ETF", "type": "ETF", "exchange": "SH", "currency": "CNY"}]
        elif fund_type == "LOF":
            return [{"code": "161005", "name": "富国天惠", "type": "LOF", "exchange": "SZ", "currency": "CNY"}]
        else:
            return self.fetch_fund_list("ETF") + self.fetch_fund_list("LOF")
