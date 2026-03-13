"""
信号管理器 - 简化版，增强调试能力
"""

import logging
import threading
from typing import Callable, Any, Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SignalRecord:
    """信号发射记录（用于调试）"""
    signal_name: str
    timestamp: datetime
    args: tuple
    handlers_count: int


class SignalManager(QObject):
    """
    信号管理器 - 简化版
    
    特性：
    - 集中管理所有信号
    - 信号发射追踪（调试模式）
    - 清晰的连接/断开 API
    - 线程安全
    """

    # 数据相关信号
    data_refreshed = pyqtSignal(dict)       # 数据刷新完成
    data_refresh_started = pyqtSignal()     # 数据刷新开始
    data_refresh_failed = pyqtSignal(str)   # 数据刷新失败

    # 基金相关信号
    fund_selected = pyqtSignal(str)         # 基金被选中
    fund_double_clicked = pyqtSignal(str)   # 基金被双击
    fund_details_loaded = pyqtSignal(dict)  # 基金详情加载完成

    # 筛选相关信号
    filter_applied = pyqtSignal(dict)       # 筛选条件应用
    filter_cleared = pyqtSignal()           # 筛选条件清除

    # 状态相关信号
    status_changed = pyqtSignal(str)        # 状态变化
    progress_updated = pyqtSignal(int, str) # 进度更新

    # 错误相关信号
    error_occurred = pyqtSignal(str, str)   # 错误发生

    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()
        self._handlers: Dict[str, List[Callable]] = {}
        self._debug_mode = False
        self._history: List[SignalRecord] = []
        self._max_history = 100
        
        logger.info("信号管理器初始化完成")

    def enable_debug(self, enabled: bool = True):
        """启用/禁用调试模式"""
        self._debug_mode = enabled
        logger.info(f"信号管理器调试模式: {'开启' if enabled else '关闭'}")

    def connect_signal(self, signal_name: str, handler: Callable) -> bool:
        """
        连接信号处理器
        
        Args:
            signal_name: 信号名称
            handler: 处理器函数
            
        Returns:
            bool: 是否成功
        """
        signal = getattr(self, signal_name, None)
        if signal is None:
            logger.warning(f"信号不存在: {signal_name}")
            return False
        
        with self._lock:
            if signal_name not in self._handlers:
                self._handlers[signal_name] = []
            
            # 避免重复连接
            if handler in self._handlers[signal_name]:
                logger.debug(f"处理器已连接，跳过: {signal_name} -> {handler.__name__}")
                return True
            
            try:
                signal.connect(handler)
                self._handlers[signal_name].append(handler)
                logger.debug(f"连接信号: {signal_name} -> {handler.__name__}")
                return True
            except Exception as e:
                logger.error(f"连接信号失败: {e}")
                return False

    def disconnect_signal(self, signal_name: str, handler: Callable = None):
        """
        断开信号处理器

        Args:
            signal_name: 信号名称
            handler: 处理器函数，如果为None则断开所有处理器
        """
        signal = getattr(self, signal_name, None)
        if not signal:
            return

        with self._lock:
            if signal_name not in self._handlers:
                return

            if handler is None:
                # 断开所有处理器
                for h in self._handlers[signal_name]:
                    try:
                        signal.disconnect(h)
                    except Exception:
                        pass
                self._handlers[signal_name].clear()
                logger.debug(f"断开所有信号处理器: {signal_name}")
            else:
                # 断开指定处理器
                if handler in self._handlers[signal_name]:
                    try:
                        signal.disconnect(handler)
                        self._handlers[signal_name].remove(handler)
                        logger.debug(f"断开信号处理器: {signal_name} -> {handler.__name__}")
                    except Exception as e:
                        logger.warning(f"断开信号处理器失败: {e}")

    def emit_signal(self, signal_name: str, *args, **kwargs):
        """
        发射信号

        Args:
            signal_name: 信号名称
            *args: 位置参数
            **kwargs: 关键字参数
        """
        signal = getattr(self, signal_name, None)
        if signal:
            try:
                signal.emit(*args, **kwargs)
                logger.debug(f"发射信号: {signal_name} {args} {kwargs}")
            except Exception as e:
                logger.error(f"发射信号失败 {signal_name}: {e}")
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def emit_data_refreshed(self, result: Dict[str, Any]):
        """发射数据刷新完成信号"""
        self.emit_signal("data_refreshed", result)

    def emit_data_refresh_started(self):
        """发射数据刷新开始信号"""
        self.emit_signal("data_refresh_started")

    def emit_data_refresh_failed(self, error_message: str):
        """发射数据刷新失败信号"""
        self.emit_signal("data_refresh_failed", error_message)

    def emit_fund_selected(self, fund_code: str):
        """发射基金选中信号"""
        self.emit_signal("fund_selected", fund_code)

    def emit_fund_double_clicked(self, fund_code: str):
        """发射基金双击信号"""
        self.emit_signal("fund_double_clicked", fund_code)

    def emit_fund_details_loaded(self, fund_details: Dict[str, Any]):
        """发射基金详情加载完成信号"""
        self.emit_signal("fund_details_loaded", fund_details)

    def emit_filter_applied(self, filter_params: Dict[str, Any]):
        """发射筛选条件应用信号"""
        self.emit_signal("filter_applied", filter_params)

    def emit_filter_cleared(self):
        """发射筛选条件清除信号"""
        self.emit_signal("filter_cleared")

    def emit_status_changed(self, status: str):
        """发射状态变化信号"""
        self.emit_signal("status_changed", status)

    def emit_progress_updated(self, progress: int, message: str):
        """发射进度更新信号"""
        self.emit_signal("progress_updated", progress, message)

    def emit_error_occurred(self, error_type: str, error_message: str):
        """发射错误发生信号"""
        self.emit_signal("error_occurred", error_type, error_message)

    def clear_all_connections(self):
        """清除所有连接"""
        for signal_name in list(self._signal_handlers.keys()):
            self.disconnect_signal(signal_name, None)
        logger.info("已清除所有信号连接")

    def get_connection_count(self, signal_name: str = None) -> int:
        """
        获取连接数量

        Args:
            signal_name: 信号名称，如果为None则返回总连接数

        Returns:
            int: 连接数量
        """
        if signal_name:
            return len(self._signal_handlers.get(signal_name, []))
        else:
            total = 0
            for handlers in self._signal_handlers.values():
                total += len(handlers)
            return total


# 全局信号管理器实例
_signal_manager_instance: SignalManager = None


def get_signal_manager() -> SignalManager:
    """
    获取信号管理器实例（单例模式）

    Returns:
        SignalManager: 信号管理器实例
    """
    global _signal_manager_instance
    if _signal_manager_instance is None:
        _signal_manager_instance = SignalManager()
    return _signal_manager_instance