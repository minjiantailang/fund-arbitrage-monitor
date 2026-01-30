"""
基金数据管理器
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from .database import get_database
from .data_fetcher import get_data_fetcher
from .arbitrage_calculator import get_calculator

logger = logging.getLogger(__name__)


class FundManager:
    """基金数据管理器"""

    def __init__(self, fetcher_type: str = "mock"):
        """
        初始化基金管理器

        Args:
            fetcher_type: 数据获取器类型（mock/eastmoney）
        """
        self.db = get_database()
        self.fetcher = get_data_fetcher(fetcher_type)
        self.calculator = get_calculator()
        self._fund_cache: Dict[str, Dict[str, Any]] = {}  # code -> fund_data
        self._price_cache: Dict[str, Dict[str, Any]] = {}  # code -> latest_price

    def refresh_all_data(self) -> Dict[str, Any]:
        """
        刷新所有基金数据

        Returns:
            Dict: 刷新结果统计
        """
        logger.info("开始刷新所有基金数据")
        start_time = datetime.now()

        try:
            # 获取ETF数据
            etf_data = self.fetcher.fetch_etf_data([])
            etf_results = self._process_fund_data(etf_data, "ETF")

            # 获取LOF数据
            lof_data = self.fetcher.fetch_lof_data([])
            lof_results = self._process_fund_data(lof_data, "LOF")

            # 合并结果
            total_funds = len(etf_data) + len(lof_data)
            total_opportunities = etf_results["opportunities"] + lof_results["opportunities"]

            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "elapsed_seconds": round(elapsed, 2),
                "total_funds": total_funds,
                "etf_funds": len(etf_data),
                "lof_funds": len(lof_data),
                "total_opportunities": total_opportunities,
                "etf_opportunities": etf_results["opportunities"],
                "lof_opportunities": lof_results["opportunities"],
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"数据刷新完成: {result}")
            return result

        except Exception as e:
            logger.error(f"刷新数据失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def refresh_fund_data(self, fund_codes: List[str]) -> Dict[str, Any]:
        """
        刷新指定基金数据

        Args:
            fund_codes: 基金代码列表

        Returns:
            Dict: 刷新结果
        """
        logger.info(f"刷新指定基金数据: {fund_codes}")
        start_time = datetime.now()

        try:
            # 分组获取数据
            etf_codes = [code for code in fund_codes if code.startswith(("51", "15"))]
            lof_codes = [code for code in fund_codes if code.startswith("16")]

            total_opportunities = 0
            processed_funds = 0

            if etf_codes:
                etf_data = self.fetcher.fetch_etf_data(etf_codes)
                etf_results = self._process_fund_data(etf_data, "ETF")
                total_opportunities += etf_results["opportunities"]
                processed_funds += len(etf_data)

            if lof_codes:
                lof_data = self.fetcher.fetch_lof_data(lof_codes)
                lof_results = self._process_fund_data(lof_data, "LOF")
                total_opportunities += lof_results["opportunities"]
                processed_funds += len(lof_data)

            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "elapsed_seconds": round(elapsed, 2),
                "processed_funds": processed_funds,
                "total_opportunities": total_opportunities,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"指定基金数据刷新完成: {result}")
            return result

        except Exception as e:
            logger.error(f"刷新指定基金数据失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _process_fund_data(self, fund_data_list: List[Dict[str, Any]], fund_type: str) -> Dict[str, Any]:
        """
        处理基金数据

        Args:
            fund_data_list: 基金数据列表
            fund_type: 基金类型

        Returns:
            Dict: 处理结果
        """
        opportunities = 0

        for fund_data in fund_data_list:
            try:
                # 保存基金基本信息
                fund_info = {
                    "code": fund_data["code"],
                    "name": fund_data["name"],
                    "type": fund_type,
                    "exchange": "SZ" if fund_data["code"].startswith("15") else "SH",
                    "currency": "CNY",
                    "management_fee": 0.5 if fund_type == "ETF" else 1.5,
                }
                self.db.save_fund(fund_info)

                # 计算套利机会
                nav = Decimal(str(fund_data.get("nav", 0)))
                price = Decimal(str(fund_data.get("price", 0)))

                if nav > 0 and price > 0:
                    arbitrage_result = self.calculator.calculate_arbitrage(
                        fund_type, float(nav), float(price), fund_data["code"]
                    )

                    # 保存价格数据
                    price_record = {
                        "fund_code": fund_data["code"],
                        "nav": float(nav),
                        "price": float(price),
                        "spread_pct": arbitrage_result["spread_pct"],
                        "yield_pct": arbitrage_result["net_yield_pct"],
                        "volume": fund_data.get("volume"),
                        "amount": fund_data.get("amount"),
                        "timestamp": fund_data.get("timestamp", datetime.now().isoformat()),
                    }
                    self.db.save_fund_price(price_record)

                    # 如果有套利机会，保存记录
                    if arbitrage_result["is_opportunity"]:
                        opportunity_record = {
                            "fund_code": fund_data["code"],
                            "opportunity_type": fund_type,
                            "nav": float(nav),
                            "price": float(price),
                            "spread_pct": arbitrage_result["spread_pct"],
                            "yield_pct": arbitrage_result["net_yield_pct"],
                            "timestamp": fund_data.get("timestamp", datetime.now().isoformat()),
                        }
                        self.db.save_arbitrage_opportunity(opportunity_record)
                        opportunities += 1

                    # 更新缓存
                    self._fund_cache[fund_data["code"]] = fund_info
                    self._price_cache[fund_data["code"]] = price_record

            except Exception as e:
                logger.error(f"处理基金数据失败 {fund_data.get('code', 'unknown')}: {e}")

        return {"opportunities": opportunities}

    def get_funds(self, fund_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            List[Dict]: 基金列表
        """
        return self.db.get_funds(fund_type)

    def get_latest_prices(self, fund_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取最新价格数据

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[Dict]: 价格数据列表
        """
        prices = self.db.get_latest_prices(fund_codes)

        # 为每个价格数据添加套利计算结果
        for price_data in prices:
            fund_code = price_data["fund_code"]
            fund_type = price_data["type"]

            arbitrage_result = self.calculator.calculate_arbitrage(
                fund_type,
                price_data.get("nav", 0),
                price_data.get("price", 0),
                fund_code
            )

            # 合并套利计算结果
            price_data.update({
                "spread_pct": arbitrage_result["spread_pct"],
                "yield_pct": arbitrage_result["net_yield_pct"],
                "is_opportunity": arbitrage_result["is_opportunity"],
                "opportunity_level": arbitrage_result["opportunity_level"],
                "description": arbitrage_result["description"],
            })

        return prices

    def get_price_history(self, fund_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取价格历史数据

        Args:
            fund_code: 基金代码
            days: 天数

        Returns:
            List[Dict]: 历史价格数据
        """
        return self.db.get_price_history(fund_code, days)

    def search_funds(self, keyword: str, fund_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索基金

        Args:
            keyword: 搜索关键词（代码或名称）
            fund_type: 基金类型筛选

        Returns:
            List[Dict]: 搜索结果
        """
        all_funds = self.get_funds(fund_type)
        keyword_lower = keyword.lower()

        results = []
        for fund in all_funds:
            if (keyword_lower in fund["code"].lower() or
                keyword_lower in fund["name"].lower()):
                results.append(fund)

        return results

    def filter_funds_by_spread(
        self,
        min_spread: float = -10.0,
        max_spread: float = 10.0,
        fund_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        按价差范围筛选基金

        Args:
            min_spread: 最小价差百分比
            max_spread: 最大价差百分比
            fund_type: 基金类型筛选

        Returns:
            List[Dict]: 筛选结果
        """
        all_prices = self.get_latest_prices()
        filtered = []

        for price_data in all_prices:
            if fund_type and price_data.get("type") != fund_type:
                continue

            spread = price_data.get("spread_pct", 0)
            if min_spread <= spread <= max_spread:
                filtered.append(price_data)

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        all_prices = self.get_latest_prices()

        if not all_prices:
            return {
                "total_funds": 0,
                "etf_count": 0,
                "lof_count": 0,
                "opportunity_count": 0,
                "avg_spread": 0.0,
                "max_spread": 0.0,
                "min_spread": 0.0,
            }

        etf_count = sum(1 for p in all_prices if p.get("type") == "ETF")
        lof_count = sum(1 for p in all_prices if p.get("type") == "LOF")
        opportunity_count = sum(1 for p in all_prices if p.get("is_opportunity", False))

        spreads = [p.get("spread_pct", 0) for p in all_prices if p.get("spread_pct") is not None]
        avg_spread = sum(spreads) / len(spreads) if spreads else 0.0
        max_spread = max(spreads) if spreads else 0.0
        min_spread = min(spreads) if spreads else 0.0

        return {
            "total_funds": len(all_prices),
            "etf_count": etf_count,
            "lof_count": lof_count,
            "opportunity_count": opportunity_count,
            "avg_spread": round(avg_spread, 2),
            "max_spread": round(max_spread, 2),
            "min_spread": round(min_spread, 2),
            "last_update": all_prices[0].get("timestamp") if all_prices else None,
        }

    def export_to_csv(self, file_path: str) -> bool:
        """
        导出数据到CSV文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            import csv
            prices = self.get_latest_prices()

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                if prices:
                    fieldnames = list(prices[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(prices)

            logger.info(f"数据导出成功: {file_path}, {len(prices)} 条记录")
            return True

        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            return False

    def close(self):
        """关闭资源"""
        self.fetcher.close()
        self.db.close()


# 全局基金管理器实例
_manager_instance: Optional[FundManager] = None


def get_fund_manager(fetcher_type: str = "mock") -> FundManager:
    """
    获取基金管理器实例

    Args:
        fetcher_type: 数据获取器类型

    Returns:
        FundManager: 基金管理器实例
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = FundManager(fetcher_type)
    return _manager_instance