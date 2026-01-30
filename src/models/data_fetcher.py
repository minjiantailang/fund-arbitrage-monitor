"""
数据获取器 - 从API获取基金数据
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
from decimal import Decimal

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器基类"""

    def __init__(self, cache_duration: int = 300):
        """
        初始化数据获取器

        Args:
            cache_duration: 缓存持续时间（秒）
        """
        self.cache_duration = cache_duration
        self._cache: Dict[str, Tuple[float, Any]] = {}  # key -> (timestamp, data)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        })

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self.cache_duration:
                logger.debug(f"从缓存获取数据: {key}")
                return data
            else:
                del self._cache[key]  # 缓存过期
        return None

    def _save_to_cache(self, key: str, data: Any):
        """保存数据到缓存"""
        self._cache[key] = (time.time(), data)

    def fetch_etf_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取ETF数据（需子类实现）

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[Dict]: ETF数据列表
        """
        raise NotImplementedError

    def fetch_lof_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取LOF数据（需子类实现）

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[Dict]: LOF数据列表
        """
        raise NotImplementedError

    def fetch_fund_list(self, fund_type: str) -> List[Dict[str, Any]]:
        """
        获取基金列表（需子类实现）

        Args:
            fund_type: 基金类型（ETF/LOF）

        Returns:
            List[Dict]: 基金列表
        """
        raise NotImplementedError

    def close(self):
        """关闭会话"""
        self.session.close()


class MockDataFetcher(DataFetcher):
    """模拟数据获取器（用于开发和测试）"""

    def __init__(self, cache_duration: int = 300):
        super().__init__(cache_duration)
        self._mock_etf_data = self._create_mock_etf_data()
        self._mock_lof_data = self._create_mock_lof_data()

    def _create_mock_etf_data(self) -> List[Dict[str, Any]]:
        """创建模拟ETF数据"""
        etf_funds = [
            {"code": "510300", "name": "沪深300ETF", "nav": 3.56, "price": 3.58},
            {"code": "510500", "name": "中证500ETF", "nav": 5.23, "price": 5.20},
            {"code": "510050", "name": "上证50ETF", "nav": 2.45, "price": 2.47},
            {"code": "159919", "name": "沪深300ETF", "nav": 3.55, "price": 3.57},
            {"code": "159915", "name": "创业板ETF", "nav": 1.89, "price": 1.88},
        ]
        return etf_funds

    def _create_mock_lof_data(self) -> List[Dict[str, Any]]:
        """创建模拟LOF数据"""
        lof_funds = [
            {"code": "161005", "name": "富国天惠LOF", "nav": 1.56, "price": 1.58},
            {"code": "163402", "name": "兴全趋势LOF", "nav": 0.89, "price": 0.88},
            {"code": "161903", "name": "万家行业LOF", "nav": 1.23, "price": 1.25},
            {"code": "162605", "name": "景顺鼎益LOF", "nav": 2.34, "price": 2.36},
            {"code": "163406", "name": "兴全合润LOF", "nav": 1.67, "price": 1.65},
        ]
        return lof_funds

    def fetch_etf_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """获取模拟ETF数据"""
        cache_key = f"etf_data_{'_'.join(sorted(fund_codes))}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 模拟网络延迟
        time.sleep(0.5)

        result = []
        for fund in self._mock_etf_data:
            if not fund_codes or fund["code"] in fund_codes:
                # 添加一些随机波动
                import random
                nav = fund["nav"] * (1 + random.uniform(-0.01, 0.01))
                price = fund["price"] * (1 + random.uniform(-0.02, 0.02))

                result.append({
                    "code": fund["code"],
                    "name": fund["name"],
                    "type": "ETF",
                    "nav": round(nav, 3),
                    "price": round(price, 3),
                    "volume": random.randint(1000000, 5000000),
                    "amount": round(price * random.randint(1000000, 5000000), 2),
                    "timestamp": datetime.now().isoformat(),
                })

        self._save_to_cache(cache_key, result)
        logger.info(f"获取模拟ETF数据: {len(result)} 条记录")
        return result

    def fetch_lof_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """获取模拟LOF数据"""
        cache_key = f"lof_data_{'_'.join(sorted(fund_codes))}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 模拟网络延迟
        time.sleep(0.5)

        result = []
        for fund in self._mock_lof_data:
            if not fund_codes or fund["code"] in fund_codes:
                # 添加一些随机波动
                import random
                nav = fund["nav"] * (1 + random.uniform(-0.005, 0.005))
                price = fund["price"] * (1 + random.uniform(-0.01, 0.01))

                result.append({
                    "code": fund["code"],
                    "name": fund["name"],
                    "type": "LOF",
                    "nav": round(nav, 3),
                    "price": round(price, 3),
                    "volume": random.randint(500000, 2000000),
                    "amount": round(price * random.randint(500000, 2000000), 2),
                    "timestamp": datetime.now().isoformat(),
                })

        self._save_to_cache(cache_key, result)
        logger.info(f"获取模拟LOF数据: {len(result)} 条记录")
        return result

    def fetch_fund_list(self, fund_type: str) -> List[Dict[str, Any]]:
        """获取模拟基金列表"""
        cache_key = f"fund_list_{fund_type}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if fund_type.upper() == "ETF":
            funds = self._mock_etf_data
        elif fund_type.upper() == "LOF":
            funds = self._mock_lof_data
        else:
            funds = self._mock_etf_data + self._mock_lof_data

        result = []
        for fund in funds:
            fund_type = "ETF" if fund["code"] in [f["code"] for f in self._mock_etf_data] else "LOF"
            result.append({
                "code": fund["code"],
                "name": fund["name"],
                "type": fund_type,
                "exchange": "SZ" if fund["code"].startswith("15") else "SH",
                "currency": "CNY",
                "management_fee": 0.5 if fund_type == "ETF" else 1.5,
            })

        self._save_to_cache(cache_key, result)
        logger.info(f"获取模拟基金列表: {fund_type}, {len(result)} 条记录")
        return result


class EastMoneyDataFetcher(DataFetcher):
    """东方财富数据获取器"""

    def __init__(self, cache_duration: int = 300):
        super().__init__(cache_duration)
        self.base_url = "http://fund.eastmoney.com"

    def fetch_etf_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """从东方财富获取ETF数据"""
        # TODO: 实现实际的东方财富API调用
        # 这里先返回模拟数据作为占位符
        mock_fetcher = MockDataFetcher(cache_duration=self.cache_duration)
        return mock_fetcher.fetch_etf_data(fund_codes)

    def fetch_lof_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """从东方财富获取LOF数据"""
        # TODO: 实现实际的东方财富API调用
        # 这里先返回模拟数据作为占位符
        mock_fetcher = MockDataFetcher(cache_duration=self.cache_duration)
        return mock_fetcher.fetch_lof_data(fund_codes)

    def fetch_fund_list(self, fund_type: str) -> List[Dict[str, Any]]:
        """从东方财富获取基金列表"""
        # TODO: 实现实际的东方财富API调用
        # 这里先返回模拟数据作为占位符
        mock_fetcher = MockDataFetcher(cache_duration=self.cache_duration)
        return mock_fetcher.fetch_fund_list(fund_type)


# 数据获取器工厂
class DataFetcherFactory:
    """数据获取器工厂"""

    @staticmethod
    def create_fetcher(fetcher_type: str = "mock", **kwargs) -> DataFetcher:
        """
        创建数据获取器

        Args:
            fetcher_type: 获取器类型（mock/eastmoney）
            **kwargs: 传递给获取器的参数

        Returns:
            DataFetcher: 数据获取器实例
        """
        if fetcher_type.lower() == "eastmoney":
            logger.info("创建东方财富数据获取器")
            return EastMoneyDataFetcher(**kwargs)
        else:
            logger.info("创建模拟数据获取器")
            return MockDataFetcher(**kwargs)


# 全局数据获取器实例
_fetcher_instance: Optional[DataFetcher] = None


def get_data_fetcher(fetcher_type: str = "mock", **kwargs) -> DataFetcher:
    """
    获取数据获取器实例

    Args:
        fetcher_type: 获取器类型
        **kwargs: 传递给获取器的参数

    Returns:
        DataFetcher: 数据获取器实例
    """
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = DataFetcherFactory.create_fetcher(fetcher_type, **kwargs)
    return _fetcher_instance