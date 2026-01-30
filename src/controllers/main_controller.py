"""
主控制器
"""

import logging
from typing import Dict, List, Any, Optional

from .data_controller import DataController
from .signal_manager import get_signal_manager

logger = logging.getLogger(__name__)


class MainController:
    """主控制器"""

    def __init__(self, fetcher_type: str = "mock"):
        """
        初始化主控制器

        Args:
            fetcher_type: 数据获取器类型
        """
        self.data_controller = DataController()
        self.signal_manager = get_signal_manager()
        self.current_filters: Dict[str, Any] = {}

        # 连接信号
        self._connect_signals()

        logger.info("主控制器初始化完成")

    def _connect_signals(self):
        """连接信号"""
        # 连接数据控制器的信号到信号管理器
        pass  # 数据控制器已经通过信号管理器转发信号

    def refresh_all_data(self) -> Dict[str, Any]:
        """
        刷新所有基金数据

        Returns:
            Dict: 刷新结果
        """
        try:
            # 通过信号管理器触发异步刷新
            self.signal_manager.emit_data_refresh_started()
            return {"success": True, "message": "数据刷新已启动"}

        except Exception as e:
            logger.error(f"启动数据刷新失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def refresh_selected_funds(self, fund_codes: List[str]) -> Dict[str, Any]:
        """
        刷新指定基金数据

        Args:
            fund_codes: 基金代码列表

        Returns:
            Dict: 刷新结果
        """
        try:
            success = self.data_controller.refresh_selected_funds_async(fund_codes)
            return {
                "success": success,
                "message": "指定基金刷新已启动" if success else "刷新启动失败"
            }

        except Exception as e:
            logger.error(f"启动指定基金刷新失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        return self.data_controller.get_statistics()

    def get_all_funds(self) -> List[Dict[str, Any]]:
        """
        获取所有基金数据

        Returns:
            List[Dict]: 基金数据列表
        """
        return self.data_controller.get_all_funds()

    def get_filtered_funds(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        获取筛选后的基金数据

        Args:
            filter_params: 筛选参数，如果为None则使用当前筛选条件

        Returns:
            List[Dict]: 筛选后的基金数据
        """
        if filter_params is not None:
            self.current_filters = filter_params

        return self.data_controller.get_filtered_funds(self.current_filters)

    def apply_filters(self, filter_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        应用筛选条件并返回结果

        Args:
            filter_params: 筛选参数

        Returns:
            List[Dict]: 筛选后的基金数据
        """
        # 更新当前筛选条件
        self.current_filters = filter_params

        # 获取筛选后的数据
        filtered_data = self.data_controller.get_filtered_funds(filter_params)

        # 发射筛选应用信号
        self.signal_manager.emit_filter_applied(filter_params)

        return filtered_data

    def get_fund_details(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金详情

        Args:
            fund_code: 基金代码

        Returns:
            Dict: 基金详情
        """
        return self.data_controller.get_fund_details(fund_code)

    def search_funds(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索基金

        Args:
            keyword: 搜索关键词

        Returns:
            List[Dict]: 搜索结果
        """
        # 简单的本地搜索实现
        all_funds = self.get_all_funds()
        keyword_lower = keyword.lower()

        results = []
        for fund in all_funds:
            if (keyword_lower in fund.get("code", "").lower() or
                keyword_lower in fund.get("name", "").lower()):
                results.append(fund)

        return results

    def export_to_csv(self, file_path: str) -> bool:
        """
        导出数据到CSV

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        return self.data_controller.export_to_csv(file_path)

    def get_last_update_time(self) -> Optional[str]:
        """
        获取最后更新时间

        Returns:
            Optional[str]: 最后更新时间字符串
        """
        stats = self.get_statistics()
        return stats.get("last_update")

    def switch_data_source(self, fetcher_type: str):
        """
        切换数据源

        Args:
            fetcher_type: 数据获取器类型
        """
        try:
            # 清理当前控制器
            self.cleanup()

            # 重新初始化（简化实现）
            from ..models.fund_manager import _manager_instance
            global _manager_instance
            if _manager_instance:
                _manager_instance.close()
                _manager_instance = None

            # 重新创建数据控制器
            self.data_controller = DataController()

            logger.info(f"已切换到数据源: {fetcher_type}")
            self.signal_manager.emit_status_changed(f"已切换到数据源: {fetcher_type}")

        except Exception as e:
            logger.error(f"切换数据源失败: {e}")
            self.signal_manager.emit_error_occurred("switch_source_error", str(e))

    def cancel_refresh(self):
        """取消当前刷新"""
        self.data_controller.cancel_refresh()

    def cleanup(self):
        """清理资源"""
        try:
            self.data_controller.cleanup()
            logger.info("主控制器资源清理完成")
        except Exception as e:
            logger.error(f"清理主控制器资源失败: {e}")