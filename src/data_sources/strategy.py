"""
数据源策略模式 - 统一数据源接口和切换机制
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataSourceStrategy(ABC):
    """数据源策略抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """数据源描述"""
        pass
    
    @abstractmethod
    def fetch_etf_data(self, fund_codes: List[str] = None) -> List[Dict[str, Any]]:
        """
        获取ETF数据
        
        Args:
            fund_codes: 指定基金代码列表，为空则获取全部
            
        Returns:
            List[Dict]: ETF数据列表
        """
        pass
    
    @abstractmethod
    def fetch_lof_data(self, fund_codes: List[str] = None) -> List[Dict[str, Any]]:
        """
        获取LOF数据
        
        Args:
            fund_codes: 指定基金代码列表，为空则获取全部
            
        Returns:
            List[Dict]: LOF数据列表
        """
        pass
    
    @abstractmethod
    def get_realtime_quote(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        pass
    
    @abstractmethod
    def get_price_history(self, fund_code: str, days: int = 7) -> List[Dict[str, Any]]:
        """获取历史价格"""
        pass
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return True


class DataSourceContext:
    """数据源上下文 - 管理策略切换"""
    
    _instance = None
    _strategies: Dict[str, DataSourceStrategy] = {}
    _current_strategy: Optional[DataSourceStrategy] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_strategy(self, key: str, strategy: DataSourceStrategy):
        """注册数据源策略"""
        self._strategies[key] = strategy
        logger.info(f"注册数据源策略: {key} -> {strategy.name}")
        
    def set_strategy(self, key: str) -> bool:
        """
        设置当前使用的策略
        
        Returns:
            bool: 是否设置成功
        """
        if key not in self._strategies:
            logger.error(f"未知的数据源策略: {key}")
            return False
            
        strategy = self._strategies[key]
        if not strategy.is_available():
            logger.warning(f"数据源 {key} 当前不可用")
            return False
            
        self._current_strategy = strategy
        logger.info(f"切换数据源策略: {strategy.name}")
        return True
    
    @property
    def current_strategy(self) -> Optional[DataSourceStrategy]:
        """获取当前策略"""
        return self._current_strategy
    
    @property
    def available_strategies(self) -> List[str]:
        """获取所有可用策略的 key 列表"""
        return [k for k, v in self._strategies.items() if v.is_available()]
    
    def get_strategy_info(self) -> List[Dict[str, str]]:
        """获取所有策略信息"""
        return [
            {
                "key": key,
                "name": strategy.name,
                "description": strategy.description,
                "available": strategy.is_available(),
            }
            for key, strategy in self._strategies.items()
        ]
    
    # 代理方法 - 转发到当前策略
    def fetch_etf_data(self, fund_codes: List[str] = None) -> List[Dict[str, Any]]:
        if not self._current_strategy:
            raise RuntimeError("未设置数据源策略")
        return self._current_strategy.fetch_etf_data(fund_codes)
    
    def fetch_lof_data(self, fund_codes: List[str] = None) -> List[Dict[str, Any]]:
        if not self._current_strategy:
            raise RuntimeError("未设置数据源策略")
        return self._current_strategy.fetch_lof_data(fund_codes)
    
    def get_realtime_quote(self, fund_code: str) -> Optional[Dict[str, Any]]:
        if not self._current_strategy:
            raise RuntimeError("未设置数据源策略")
        return self._current_strategy.get_realtime_quote(fund_code)
    
    def get_price_history(self, fund_code: str, days: int = 7) -> List[Dict[str, Any]]:
        if not self._current_strategy:
            raise RuntimeError("未设置数据源策略")
        return self._current_strategy.get_price_history(fund_code, days)


# 单例获取器
def get_data_source_context() -> DataSourceContext:
    """获取数据源上下文单例"""
    return DataSourceContext()
