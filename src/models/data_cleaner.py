"""
数据清洗模块 - 统一管理数据过滤和清洗规则
"""
import logging
from typing import Dict, List, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilterRule:
    """筛选规则"""
    name: str
    description: str
    filter_func: Callable[[Dict[str, Any]], bool]
    enabled: bool = True


class DataCleaner:
    """
    数据清洗器 - 集中管理所有数据清洗规则
    
    规则分为两类：
    1. 系统规则：始终启用，清洗无效/脏数据
    2. 用户规则：可配置的筛选条件
    """
    
    def __init__(self):
        self._system_rules: List[FilterRule] = []
        self._user_rules: List[FilterRule] = []
        self._init_system_rules()
    
    def _init_system_rules(self):
        """初始化系统清洗规则"""
        
        # 规则1: 排除联接基金（非真正的场内基金）
        self._system_rules.append(FilterRule(
            name="exclude_feeder_funds",
            description="排除联接基金",
            filter_func=lambda f: "联接" not in str(f.get("name", "")),
        ))
        
        # 规则2: 排除无效价格
        from src.ui.styles import Thresholds
        
        self._system_rules.append(FilterRule(
            name="exclude_invalid_price",
            description="排除价格无效的基金",
            filter_func=lambda f: f.get("price", 0) > Thresholds.PRICE_INVALID_MIN,
        ))
        
        # 规则3: 排除僵尸基金（无成交且价格异常）
        def is_not_zombie(fund: Dict[str, Any]) -> bool:
            volume = fund.get("volume", 0)
            price = fund.get("price", 0)
            # 仅当成交量为0且价格是占位符(0或1.0)时排除
            if volume == 0:
                if price <= Thresholds.PRICE_INVALID_MIN:
                    return False
                if abs(price - Thresholds.PRICE_PLACEHOLDER) < Thresholds.PRICE_PLACEHOLDER_TOLERANCE:
                    return False
            return True
        
        self._system_rules.append(FilterRule(
            name="exclude_zombie_funds",
            description="排除僵尸基金（无成交且价格异常）",
            filter_func=is_not_zombie,
        ))
        
        # 规则4: 排除货币基金代码
        def is_not_money_fund(fund: Dict[str, Any]) -> bool:
            code = fund.get("code", "")
            money_prefixes = ("511", "159001", "159003", "159005")
            return not code.startswith(money_prefixes)
        
        self._system_rules.append(FilterRule(
            name="exclude_money_funds",
            description="排除货币基金",
            filter_func=is_not_money_fund,
        ))
    
    def clean(self, funds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用系统清洗规则
        
        Args:
            funds: 原始基金数据列表
            
        Returns:
            List: 清洗后的数据
        """
        result = funds
        
        for rule in self._system_rules:
            if rule.enabled:
                before_count = len(result)
                result = [f for f in result if rule.filter_func(f)]
                filtered_count = before_count - len(result)
                if filtered_count > 0:
                    logger.debug(f"规则 [{rule.name}] 过滤了 {filtered_count} 条数据")
        
        return result
    
    def apply_user_filters(
        self,
        funds: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        应用用户筛选条件
        
        Args:
            funds: 基金数据列表
            filters: 用户筛选参数
            
        Returns:
            List: 筛选后的数据
        """
        result = []
        from src.ui.styles import Thresholds
        
        for fund in funds:
            # 基金类型筛选
            fund_type = filters.get("fund_type", "all")
            if fund_type != "all" and fund.get("type") != fund_type:
                continue
            
            # 价差范围筛选
            min_spread = filters.get("min_spread", Thresholds.DEFAULT_MIN_SPREAD)
            max_spread = filters.get("max_spread", Thresholds.DEFAULT_MAX_SPREAD)
            spread_pct = fund.get("spread_pct", 0)
            
            if not (min_spread <= spread_pct <= max_spread):
                continue
            
            # 机会等级筛选
            opportunity_levels = filters.get("opportunity_levels", [])
            opportunity_level = fund.get("opportunity_level", "none")
            
            if opportunity_levels and opportunity_level not in opportunity_levels:
                continue
            
            # 只显示套利机会
            only_opportunities = filters.get("only_opportunities", False)
            if only_opportunities and not fund.get("is_opportunity", False):
                continue
            
            result.append(fund)
        
        return result
    
    def get_rule_status(self) -> List[Dict[str, Any]]:
        """获取所有规则的状态"""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "type": "system",
            }
            for rule in self._system_rules
        ]
    
    def set_rule_enabled(self, rule_name: str, enabled: bool):
        """启用/禁用规则"""
        for rule in self._system_rules:
            if rule.name == rule_name:
                rule.enabled = enabled
                logger.info(f"规则 [{rule_name}] 已{'启用' if enabled else '禁用'}")
                return
        logger.warning(f"未找到规则: {rule_name}")


# 单例
_cleaner_instance = None

def get_data_cleaner() -> DataCleaner:
    """获取数据清洗器单例"""
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = DataCleaner()
    return _cleaner_instance
