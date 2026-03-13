"""
套利机会计算器
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class ArbitrageCalculator:
    """套利机会计算器"""

    # 默认交易费用（百分比）
    DEFAULT_FEES = {
        "ETF": {
            "commission": Decimal("0.0003"),  # 佣金 0.03%
            "stamp_tax": Decimal("0.001"),    # 印花税 0.1%
            "total": Decimal("0.0013"),       # 总费用 0.13%
        },
        "LOF": {
            "subscription": Decimal("0.015"),  # 申购费 1.5%
            "redemption": Decimal("0.005"),    # 赎回费 0.5%
            "total": Decimal("0.02"),          # 总费用 2.0%
        }
    }

    def __init__(self, custom_fees: Optional[Dict[str, Dict[str, Decimal]]] = None):
        """
        初始化计算器

        Args:
            custom_fees: 自定义交易费用配置
        """
        self.fees = self.DEFAULT_FEES.copy()
        if custom_fees:
            for fund_type, fee_config in custom_fees.items():
                if fund_type in self.fees:
                    self.fees[fund_type].update(fee_config)

    def calculate_etf_arbitrage(
        self,
        nav: Decimal,
        price: Decimal,
        fund_code: str = ""
    ) -> Dict[str, Any]:
        """
        计算ETF套利机会

        Args:
            nav: 基金净值
            price: 市场价格
            fund_code: 基金代码（用于日志）

        Returns:
            Dict: 套利计算结果
        """
        try:
            if nav <= 0:
                logger.warning(f"基金 {fund_code} 净值无效: {nav}")
                return self._create_empty_result("ETF", nav, price)

            # 计算价差百分比
            spread = price - nav
            spread_pct = (spread / nav) * Decimal("100")

            # 计算净收益率（扣除交易费用）
            fee_rate = self.fees["ETF"]["total"]
            net_yield_pct = spread_pct - (fee_rate * Decimal("100"))

            # 判断套利机会
            opportunity_type = self._determine_opportunity_type(net_yield_pct)

            result = {
                "fund_code": fund_code,
                "opportunity_type": "ETF",
                "nav": float(nav),
                "price": float(price),
                "spread": float(spread),
                "spread_pct": float(spread_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "net_yield_pct": float(net_yield_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "fee_rate": float(fee_rate * Decimal("100")),
                "is_opportunity": opportunity_type != "none",
                "opportunity_level": opportunity_type,
                "description": self._get_opportunity_description(
                    opportunity_type, net_yield_pct, spread_pct, "ETF"
                )
            }

            logger.debug(f"ETF套利计算 - {fund_code}: 价差={result['spread_pct']}%, 净收益={result['net_yield_pct']}%")
            return result

        except Exception as e:
            logger.error(f"ETF套利计算失败 {fund_code}: {e}")
            return self._create_empty_result("ETF", nav, price)

    def calculate_lof_arbitrage(
        self,
        nav: Decimal,
        price: Decimal,
        fund_code: str = ""
    ) -> Dict[str, Any]:
        """
        计算LOF套利机会

        Args:
            nav: 场外净值
            price: 场内价格
            fund_code: 基金代码（用于日志）

        Returns:
            Dict: 套利计算结果
        """
        try:
            if nav <= 0:
                logger.warning(f"基金 {fund_code} 净值无效: {nav}")
                return self._create_empty_result("LOF", nav, price)

            # 计算价差百分比（场内价格相对于场外净值）
            spread = price - nav
            spread_pct = (spread / nav) * Decimal("100")

            # 计算净收益率（扣除申购赎回费用）
            fee_rate = self.fees["LOF"]["total"]
            net_yield_pct = spread_pct - (fee_rate * Decimal("100"))

            # 判断套利机会
            opportunity_type = self._determine_opportunity_type(net_yield_pct)

            result = {
                "fund_code": fund_code,
                "opportunity_type": "LOF",
                "nav": float(nav),
                "price": float(price),
                "spread": float(spread),
                "spread_pct": float(spread_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "net_yield_pct": float(net_yield_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "fee_rate": float(fee_rate * Decimal("100")),
                "is_opportunity": opportunity_type != "none",
                "opportunity_level": opportunity_type,
                "description": self._get_opportunity_description(
                    opportunity_type, net_yield_pct, spread_pct, "LOF"
                ),
                "direction": "场内溢价" if spread_pct > 0 else "场内折价"
            }

            logger.debug(f"LOF套利计算 - {fund_code}: 价差={result['spread_pct']}%, 净收益={result['net_yield_pct']}%")
            return result

        except Exception as e:
            logger.error(f"LOF套利计算失败 {fund_code}: {e}")
            return self._create_empty_result("LOF", nav, price)

    def calculate_arbitrage(
        self,
        fund_type: str,
        nav: float,
        price: float,
        fund_code: str = ""
    ) -> Dict[str, Any]:
        """
        通用套利计算接口

        Args:
            fund_type: 基金类型（ETF/LOF）
            nav: 净值
            price: 价格
            fund_code: 基金代码

        Returns:
            Dict: 套利计算结果
        """
        try:
            nav_decimal = Decimal(str(nav))
            price_decimal = Decimal(str(price))

            if fund_type.upper() == "ETF":
                return self.calculate_etf_arbitrage(nav_decimal, price_decimal, fund_code)
            elif fund_type.upper() == "LOF":
                return self.calculate_lof_arbitrage(nav_decimal, price_decimal, fund_code)
            else:
                logger.warning(f"不支持的基金类型: {fund_type}")
                return self._create_empty_result(fund_type, nav_decimal, price_decimal)
        except Exception as e:
            logger.error(f"通用套利计算失败 {fund_code}: {e}")
            return self._create_empty_result(fund_type, Decimal("0"), Decimal("0"))

    def _determine_opportunity_type(self, net_yield_pct: Decimal) -> str:
        """
        根据净收益率判断套利机会类型

        Args:
            net_yield_pct: 净收益率百分比

        Returns:
            str: 机会类型（excellent/good/weak/none）
        """
        if net_yield_pct >= Decimal("1.0"):  # 净收益 >= 1%
            return "excellent"
        elif net_yield_pct >= Decimal("0.5"):  # 净收益 >= 0.5%
            return "good"
        elif net_yield_pct >= Decimal("0.2"):  # 净收益 >= 0.2%
            return "weak"
        else:
            return "none"

    def _get_opportunity_description(
        self, 
        opportunity_type: str, 
        net_yield_pct: Decimal,
        spread_pct: Decimal = None,
        fund_type: str = "ETF",
        purchase_limit: float = None  # 申购限额（万元），None表示未知
    ) -> str:
        """
        获取套利操作建议描述
        
        Args:
            opportunity_type: 机会类型
            net_yield_pct: 净收益率
            spread_pct: 价差百分比（正=溢价，负=折价）
            fund_type: 基金类型
            purchase_limit: 申购限额（万元）
            
        Returns:
            str: 操作建议描述
        """
        if opportunity_type == "none":
            return "无套利机会"
        
        # 判断方向
        if spread_pct is None:
            spread_pct = net_yield_pct  # 兼容旧调用
            
        is_premium = float(spread_pct) > 0  # 溢价
        
        # 生成限购信息
        if purchase_limit is not None:
            if purchase_limit >= 100:
                limit_text = f"限购{int(purchase_limit)}万"
                tractor_text = "可拖拉机"
            elif purchase_limit >= 10:
                limit_text = f"限购{int(purchase_limit)}万"
                tractor_text = "可小拖"
            elif purchase_limit > 0:
                limit_text = f"限购{purchase_limit}万"
                tractor_text = "不可拖"
            else:
                limit_text = "暂停申购"
                tractor_text = ""
        else:
            limit_text = ""
            tractor_text = ""
        
        # 生成操作建议
        if fund_type.upper() == "ETF":
            if is_premium:
                # 溢价：申购→卖出
                action = "申购后场内卖出"
                direction = "↑溢价套利"
            else:
                # 折价：买入→赎回
                action = "场内买入后赎回"
                direction = "↓折价套利"
        else:  # LOF
            if is_premium:
                # 溢价：场外申购→转托管→场内卖出
                action = "申购转场内卖"
                direction = "↑溢价"
            else:
                # 折价：场内买入→赎回
                action = "场内买转赎回"
                direction = "↓折价"
        
        # 组合描述
        parts = [direction, action]
        if limit_text:
            parts.append(limit_text)
        if tractor_text:
            parts.append(tractor_text)
        parts.append(f"净收益{float(net_yield_pct):.2f}%")
        
        return " | ".join(parts)

    def _create_empty_result(self, fund_type: str, nav: Decimal, price: Decimal) -> Dict[str, Any]:
        """
        创建空的计算结果（用于错误情况）

        Args:
            fund_type: 基金类型
            nav: 净值
            price: 价格

        Returns:
            Dict: 空结果
        """
        return {
            "fund_code": "",
            "opportunity_type": fund_type,
            "nav": float(nav) if nav else 0.0,
            "price": float(price) if price else 0.0,
            "spread": 0.0,
            "spread_pct": 0.0,
            "net_yield_pct": 0.0,
            "fee_rate": 0.0,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "计算失败或无数据",
            "direction": "未知"
        }

    def update_fees(self, fund_type: str, fee_config: Dict[str, Decimal]):
        """
        更新交易费用配置

        Args:
            fund_type: 基金类型
            fee_config: 费用配置字典
        """
        if fund_type in self.fees:
            self.fees[fund_type].update(fee_config)
            # 重新计算总费用
            if "total" not in fee_config:
                total_fee = sum(v for k, v in self.fees[fund_type].items() if k != "total")
                self.fees[fund_type]["total"] = total_fee
            logger.info(f"更新{fund_type}交易费用配置: {self.fees[fund_type]}")
        else:
            logger.warning(f"不支持的基金类型: {fund_type}")

    def get_fee_summary(self) -> Dict[str, Dict[str, float]]:
        """
        获取费用汇总

        Returns:
            Dict: 费用汇总（转换为float便于显示）
        """
        summary = {}
        for fund_type, fees in self.fees.items():
            summary[fund_type] = {
                key: float(value * Decimal("100")) if isinstance(value, Decimal) else value
                for key, value in fees.items()
            }
        return summary


# 全局计算器实例
_calculator_instance: Optional[ArbitrageCalculator] = None


def get_calculator() -> ArbitrageCalculator:
    """
    获取计算器实例（单例模式）

    Returns:
        ArbitrageCalculator: 计算器实例
    """
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = ArbitrageCalculator()
    return _calculator_instance