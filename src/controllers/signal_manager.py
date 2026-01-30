"""
信号管理器
"""

import logging
from typing import Callable, Any, Dict
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class SignalManager(QObject):
    """信号管理器"""

    # 数据相关信号
    data_refreshed = pyqtSignal(dict)  # 数据刷新完成
    data_refresh_started = pyqtSignal()  # 数据刷新开始
    data_refresh_failed = pyqtSignal(str)  # 数据刷新失败（错误信息）

    # 基金相关信号
    fund_selected = pyqtSignal(str)  # 基金被选中
    fund_double_clicked = pyqtSignal(str)  # 基金被双击
    fund_details_loaded = pyqtSignal(dict)  # 基金详情加载完成

    # 筛选相关信号
    filter_applied = pyqtSignal(dict)  # 筛选条件应用
    filter_cleared = pyqtSignal()  # 筛选条件清除

    # 状态相关信号
    status_changed = pyqtSignal(str)  # 状态变化
    progress_updated = pyqtSignal(int, str)  # 进度更新（进度百分比，消息）

    # 错误相关信号
    error_occurred = pyqtSignal(str, str)  # 错误发生（错误类型，错误信息）

    def __init__(self):
        super().__init__()
        self._signal_handlers: Dict[str, list] = {}
        logger.info("信号管理器初始化完成")

    def connect_signal(self, signal_name: str, handler: Callable):
        """
        连接信号处理器

        Args:
            signal_name: 信号名称
            handler: 处理器函数
        """
        if signal_name not in self._signal_handlers:
            self._signal_handlers[signal_name] = []

        self._signal_handlers[signal_name].append(handler)

        # 连接到实际的Qt信号
        signal = getattr(self, signal_name, None)
        if signal:
            signal.connect(handler)
            logger.debug(f"连接信号: {signal_name} -> {handler.__name__}")
        else:
            logger.warning(f"信号不存在: {signal_name}")

    def disconnect_signal(self, signal_name: str, handler: Callable = None):
        """
        断开信号处理器

        Args:
            signal_name: 信号名称
            handler: 处理器函数，如果为None则断开所有处理器
        """
        if signal_name not in self._signal_handlers:
            return

        signal = getattr(self, signal_name, None)
        if not signal:
            return

        if handler is None:
            # 断开所有处理器
            for h in self._signal_handlers[signal_name]:
                try:
                    signal.disconnect(h)
                except Exception:
                    pass
            self._signal_handlers[signal_name].clear()
            logger.debug(f"断开所有信号处理器: {signal_name}")
        else:
            # 断开指定处理器
            if handler in self._signal_handlers[signal_name]:
                try:
                    signal.disconnect(handler)
                    self._signal_handlers[signal_name].remove(handler)
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