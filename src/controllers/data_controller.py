"""
数据控制器
"""

import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot

from ..models.fund_manager import get_fund_manager
from .signal_manager import get_signal_manager

logger = logging.getLogger(__name__)


class DataRefreshWorker(QThread):
    """数据刷新工作线程"""

    refresh_complete = pyqtSignal(dict)  # 刷新完成信号
    refresh_progress = pyqtSignal(int, str)  # 刷新进度信号（进度，消息）
    refresh_error = pyqtSignal(str)  # 刷新错误信号

    def __init__(self, fund_codes: Optional[List[str]] = None):
        super().__init__()
        self.fund_codes = fund_codes
        self.is_cancelled = False

    def run(self):
        """线程运行函数"""
        try:
            manager = get_fund_manager()

            if self.fund_codes:
                # 刷新指定基金
                self.refresh_progress.emit(10, f"开始刷新 {len(self.fund_codes)} 只基金...")
                result = manager.refresh_fund_data(self.fund_codes)
            else:
                # 刷新所有基金
                self.refresh_progress.emit(10, "开始刷新所有基金数据...")
                result = manager.refresh_all_data()

            if self.is_cancelled:
                self.refresh_progress.emit(0, "刷新已取消")
                return

            if result.get("success"):
                self.refresh_progress.emit(100, "数据刷新完成")
                self.refresh_complete.emit(result)
            else:
                error_msg = result.get("error", "未知错误")
                self.refresh_error.emit(f"数据刷新失败: {error_msg}")

        except Exception as e:
            logger.error(f"数据刷新线程异常: {e}")
            self.refresh_error.emit(f"数据刷新异常: {e}")

    def cancel(self):
        """取消刷新"""
        self.is_cancelled = True


class DataController(QObject):
    """数据控制器"""

    def __init__(self, fetcher_type: str = "mock"):
        super().__init__()
        self.fetcher_type = fetcher_type
        self.fund_manager = get_fund_manager(fetcher_type)
        self.signal_manager = get_signal_manager()
        self.refresh_worker: Optional[DataRefreshWorker] = None
        self.last_refresh_time: Optional[datetime] = None
        self.is_refreshing = False

        # 连接信号
        self._connect_signals()

        logger.info("数据控制器初始化完成")

    def _connect_signals(self):
        """连接信号"""
        # 连接信号管理器的信号
        self.signal_manager.data_refresh_started.connect(self._on_data_refresh_started)
        self.signal_manager.filter_applied.connect(self._on_filter_applied)

    @pyqtSlot()
    def _on_data_refresh_started(self):
        """处理数据刷新开始信号"""
        self.refresh_all_data_async()

    @pyqtSlot(dict)
    def _on_filter_applied(self, filter_params: Dict[str, Any]):
        """处理筛选条件应用信号"""
        # 可以在这里添加筛选相关的数据处理逻辑
        pass

    def refresh_all_data_async(self):
        """
        异步刷新所有数据

        Returns:
            bool: 是否成功启动刷新
        """
        if self.is_refreshing:
            logger.warning("数据刷新正在进行中，忽略重复请求")
            self.signal_manager.emit_status_changed("刷新正在进行中...")
            return False

        try:
            self.is_refreshing = True
            self.signal_manager.emit_status_changed("开始刷新数据...")

            # 创建工作线程
            self.refresh_worker = DataRefreshWorker()

            # 连接工作线程信号
            self.refresh_worker.refresh_complete.connect(self._on_refresh_complete)
            self.refresh_worker.refresh_progress.connect(self._on_refresh_progress)
            self.refresh_worker.refresh_error.connect(self._on_refresh_error)
            self.refresh_worker.finished.connect(self._on_refresh_finished)

            # 启动线程
            self.refresh_worker.start()

            logger.info("启动异步数据刷新")
            return True

        except Exception as e:
            logger.error(f"启动异步数据刷新失败: {e}")
            self.signal_manager.emit_error_occurred("refresh_error", f"启动刷新失败: {e}")
            self.is_refreshing = False
            return False

    def refresh_selected_funds_async(self, fund_codes: List[str]):
        """
        异步刷新指定基金数据

        Args:
            fund_codes: 基金代码列表

        Returns:
            bool: 是否成功启动刷新
        """
        if self.is_refreshing:
            logger.warning("数据刷新正在进行中，忽略重复请求")
            return False

        try:
            self.is_refreshing = True
            self.signal_manager.emit_status_changed(f"开始刷新 {len(fund_codes)} 只基金...")

            # 创建工作线程
            self.refresh_worker = DataRefreshWorker(fund_codes)

            # 连接工作线程信号
            self.refresh_worker.refresh_complete.connect(self._on_refresh_complete)
            self.refresh_worker.refresh_progress.connect(self._on_refresh_progress)
            self.refresh_worker.refresh_error.connect(self._on_refresh_error)
            self.refresh_worker.finished.connect(self._on_refresh_finished)

            # 启动线程
            self.refresh_worker.start()

            logger.info(f"启动异步刷新指定基金: {fund_codes}")
            return True

        except Exception as e:
            logger.error(f"启动异步刷新指定基金失败: {e}")
            self.signal_manager.emit_error_occurred("refresh_error", f"启动刷新失败: {e}")
            self.is_refreshing = False
            return False

    @pyqtSlot(dict)
    def _on_refresh_complete(self, result: Dict[str, Any]):
        """处理刷新完成"""
        try:
            self.last_refresh_time = datetime.now()

            # 更新统计信息
            statistics = self.get_statistics()
            self.signal_manager.emit_data_refreshed(result)

            # 发送状态更新
            opportunity_count = result.get("total_opportunities", 0)
            status_msg = f"刷新完成，发现 {opportunity_count} 个套利机会"
            self.signal_manager.emit_status_changed(status_msg)

            logger.info(f"数据刷新完成: {result}")

        except Exception as e:
            logger.error(f"处理刷新完成失败: {e}")

    @pyqtSlot(int, str)
    def _on_refresh_progress(self, progress: int, message: str):
        """处理刷新进度"""
        self.signal_manager.emit_progress_updated(progress, message)
        self.signal_manager.emit_status_changed(message)

    @pyqtSlot(str)
    def _on_refresh_error(self, error_message: str):
        """处理刷新错误"""
        self.signal_manager.emit_data_refresh_failed(error_message)
        self.signal_manager.emit_status_changed(f"刷新失败: {error_message}")
        logger.error(f"数据刷新错误: {error_message}")

    @pyqtSlot()
    def _on_refresh_finished(self):
        """处理刷新线程结束"""
        self.is_refreshing = False

        # 清理工作线程
        if self.refresh_worker:
            self.refresh_worker.deleteLater()
            self.refresh_worker = None

        logger.debug("数据刷新线程结束")

    def cancel_refresh(self):
        """取消当前刷新"""
        if self.refresh_worker and self.is_refreshing:
            self.refresh_worker.cancel()
            self.signal_manager.emit_status_changed("刷新已取消")
            logger.info("数据刷新已取消")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            statistics = self.fund_manager.get_statistics()

            # 添加最后更新时间
            if self.last_refresh_time:
                statistics["last_update"] = self.last_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                statistics["last_update"] = "从未更新"

            return statistics

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_funds": 0,
                "etf_count": 0,
                "lof_count": 0,
                "opportunity_count": 0,
                "avg_spread": 0.0,
                "max_spread": 0.0,
                "min_spread": 0.0,
                "last_update": "获取失败",
            }

    def get_all_funds(self) -> List[Dict[str, Any]]:
        """
        获取所有基金数据

        Returns:
            List[Dict]: 基金数据列表
        """
        try:
            return self.fund_manager.get_latest_prices()
        except Exception as e:
            logger.error(f"获取所有基金数据失败: {e}")
            return []

    def get_price_history(self, fund_code: str, days: int = 3) -> List[Dict[str, Any]]:
        """
        获取基金历史价格数据（包含溢价率）
        
        Args:
            fund_code: 基金代码
            days: 获取最近多少天的数据
            
        Returns:
            List[Dict]: 历史价格数据
        """
        try:
            return self.fund_manager.get_price_history(fund_code, days)
        except Exception as e:
            logger.error(f"获取历史价格数据失败: {e}")
            return []

    def get_filtered_funds(self, filter_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取筛选后的基金数据

        Args:
            filter_params: 筛选参数

        Returns:
            List[Dict]: 筛选后的基金数据
        """
        try:
            all_funds = self.get_all_funds()
            if not all_funds:
                return []

            # 应用筛选条件
            filtered_funds = self._apply_filters(all_funds, filter_params)

            # 应用排序
            sorted_funds = self._apply_sorting(filtered_funds, filter_params)

            return sorted_funds

        except Exception as e:
            logger.error(f"获取筛选后基金数据失败: {e}")
            return []

    def _apply_filters(self, funds: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用筛选条件"""
        from src.models.data_cleaner import get_data_cleaner
        
        cleaner = get_data_cleaner()
        
        # 1. 首先应用系统清洗规则（排除脏数据）
        cleaned_funds = cleaner.clean(funds)
        
        # 2. 然后应用用户筛选条件
        filtered_funds = cleaner.apply_user_filters(cleaned_funds, filters)
        
        return filtered_funds

    def _apply_sorting(self, funds: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用排序"""
        sort_by = filters.get("sort_by", "spread_pct_desc")

        if not funds:
            return funds

        # 定义排序键函数
        sort_keys = {
            "spread_pct_desc": lambda f: (-(f.get("spread_pct") or 0), f.get("code", "")),
            "spread_pct_asc": lambda f: (f.get("spread_pct") or 0, f.get("code", "")),
            "yield_pct_desc": lambda f: (-(f.get("yield_pct") or 0), f.get("code", "")),
            "yield_pct_asc": lambda f: (f.get("yield_pct") or 0, f.get("code", "")),
            "code_asc": lambda f: f.get("code", ""),
            "name_asc": lambda f: f.get("name", ""),
        }

        sort_key = sort_keys.get(sort_by, sort_keys["spread_pct_desc"])

        try:
            return sorted(funds, key=sort_key)
        except Exception as e:
            logger.error(f"排序失败: {e}")
            return funds

    def get_fund_details(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金详情

        Args:
            fund_code: 基金代码

        Returns:
            Dict: 基金详情
        """
        try:
            # 获取最新价格数据
            prices = self.fund_manager.get_latest_prices([fund_code])
            if not prices:
                return {"error": "基金未找到"}

            fund_data = prices[0]

            # 获取历史数据
            history = self.fund_manager.get_price_history(fund_code, days=30)

            result = {
                "basic_info": {
                    "code": fund_data.get("code", fund_code),
                    "name": fund_data.get("name", ""),
                    "type": fund_data.get("type", ""),
                },
                "current_data": fund_data,
                "history_data": history,
                "timestamp": datetime.now().isoformat(),
            }

            # 发射基金详情加载完成信号
            self.signal_manager.emit_fund_details_loaded(result)

            return result

        except Exception as e:
            logger.error(f"获取基金详情失败 {fund_code}: {e}")
            error_result = {"error": str(e)}
            self.signal_manager.emit_error_occurred("fund_detail_error", str(e))
            return error_result

    def get_fund_trends(self, fund_code: str) -> List[Dict[str, Any]]:
        """
        获取基金分时走势
        
        Args:
            fund_code: 基金代码
            
        Returns:
            List[Dict]: 分时数据列表
        """
        if self.fund_manager and hasattr(self.fund_manager, "fetcher"):
            if hasattr(self.fund_manager.fetcher, "fetch_fund_trends"):
                # 注意：这是个网络请求，可能会阻塞 UI 一小会儿
                return self.fund_manager.fetcher.fetch_fund_trends(fund_code)
        return []

    def export_to_csv(self, file_path: str) -> bool:
        """
        导出数据到CSV

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            success = self.fund_manager.export_to_csv(file_path)
            if success:
                self.signal_manager.emit_status_changed(f"数据已导出到: {file_path}")
            else:
                self.signal_manager.emit_status_changed("数据导出失败")
            return success
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            self.signal_manager.emit_error_occurred("export_error", str(e))
            return False

    def cleanup(self):
        """清理资源"""
        try:
            self.cancel_refresh()
            self.signal_manager.clear_all_connections()
            logger.info("数据控制器资源清理完成")
        except Exception as e:
            logger.error(f"清理数据控制器资源失败: {e}")