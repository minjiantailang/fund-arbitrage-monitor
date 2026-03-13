"""
数据控制器单元测试 - 完整覆盖版本
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime


class TestDataController:
    """数据控制器测试（不依赖Qt事件循环）"""

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_init(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试初始化"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        assert controller.fund_manager == mock_fund_manager
        assert controller.signal_manager == mock_signal_manager
        assert controller.refresh_worker is None
        assert controller.last_refresh_time is None
        assert controller.is_refreshing is False

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_statistics(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取统计信息"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.get_statistics.return_value = {
            "total_funds": 10,
            "etf_count": 6,
            "lof_count": 4,
            "opportunity_count": 3,
            "avg_spread": 0.5,
            "max_spread": 2.0,
            "min_spread": -1.0,
        }
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        stats = controller.get_statistics()

        assert stats["total_funds"] == 10
        assert stats["etf_count"] == 6
        assert stats["lof_count"] == 4
        assert "last_update" in stats
        assert stats["last_update"] == "从未更新"

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_statistics_with_last_refresh_time(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取统计信息（有最后刷新时间）"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_statistics.return_value = {"total_funds": 5}
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.last_refresh_time = datetime(2026, 1, 30, 12, 0, 0)
        stats = controller.get_statistics()

        assert stats["last_update"] == "2026-01-30 12:00:00"

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_statistics_failure(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取统计信息失败"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_statistics.side_effect = Exception("测试错误")
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        stats = controller.get_statistics()

        assert stats["total_funds"] == 0
        assert stats["last_update"] == "获取失败"

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_all_funds(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取所有基金"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "161005", "name": "富国天惠LOF", "type": "LOF"}
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        funds = controller.get_all_funds()

        assert len(funds) == 2
        mock_fund_manager.get_latest_prices.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_all_funds_failure(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取所有基金失败"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_latest_prices.side_effect = Exception("测试错误")
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        funds = controller.get_all_funds()

        assert funds == []

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_filtered_funds(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取筛选后的基金"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF", "spread_pct": 0.5, "volume": 1000, "price": 3.5},
            {"code": "510500", "name": "中证500ETF", "type": "ETF", "spread_pct": -0.3, "volume": 1000, "price": 5.5},
            {"code": "161005", "name": "富国天惠LOF", "type": "LOF", "spread_pct": 1.5, "volume": 1000, "price": 2.5},
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 测试类型筛选
        filtered = controller.get_filtered_funds({"fund_type": "ETF"})
        assert len(filtered) == 2
        assert all(f["type"] == "ETF" for f in filtered)

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_filtered_funds_empty(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取空的筛选结果"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_latest_prices.return_value = []
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        filtered = controller.get_filtered_funds({})

        assert filtered == []

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_filtered_funds_failure(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取筛选基金失败"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_latest_prices.side_effect = Exception("测试错误")
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        filtered = controller.get_filtered_funds({})

        assert filtered == []

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_apply_filters_spread_range(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试价差范围筛选"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "type": "ETF", "spread_pct": 0.5, "volume": 1000, "price": 3.5},
            {"code": "510500", "type": "ETF", "spread_pct": -0.3, "volume": 1000, "price": 5.5},
            {"code": "161005", "type": "LOF", "spread_pct": 1.5, "volume": 1000, "price": 2.5},
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 测试价差范围筛选
        filtered = controller.get_filtered_funds({"min_spread": 0.0, "max_spread": 1.0})
        assert len(filtered) == 1
        assert filtered[0]["code"] == "510300"

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_apply_filters_opportunity_levels(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试机会等级筛选"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "type": "ETF", "spread_pct": 0.5, "opportunity_level": "good", "volume": 1000, "price": 3.5},
            {"code": "510500", "type": "ETF", "spread_pct": -0.3, "opportunity_level": "none", "volume": 1000, "price": 5.5},
            {"code": "161005", "type": "LOF", "spread_pct": 1.5, "opportunity_level": "excellent", "volume": 1000, "price": 2.5},
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 测试机会等级筛选
        filtered = controller.get_filtered_funds({"opportunity_levels": ["good", "excellent"]})
        assert len(filtered) == 2

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_apply_filters_only_opportunities(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试只显示套利机会筛选"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "type": "ETF", "spread_pct": 0.5, "is_opportunity": True, "volume": 1000, "price": 3.5},
            {"code": "510500", "type": "ETF", "spread_pct": -0.3, "is_opportunity": False, "volume": 1000, "price": 5.5},
            {"code": "161005", "type": "LOF", "spread_pct": 1.5, "is_opportunity": True, "volume": 1000, "price": 2.5},
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 测试只显示套利机会
        filtered = controller.get_filtered_funds({"only_opportunities": True})
        assert len(filtered) == 2
        assert all(f["is_opportunity"] for f in filtered)

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_apply_sorting(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试排序功能"""
        mock_fund_manager = Mock()
        mock_funds = [
            {"code": "510300", "type": "ETF", "spread_pct": 0.5, "yield_pct": 0.3, "volume": 1000, "price": 3.5},
            {"code": "510500", "type": "ETF", "spread_pct": 1.5, "yield_pct": 1.2, "volume": 1000, "price": 5.5},
            {"code": "161005", "type": "LOF", "spread_pct": -0.3, "yield_pct": -0.5, "volume": 1000, "price": 2.5},
        ]
        mock_fund_manager.get_latest_prices.return_value = mock_funds
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 测试降序排序
        sorted_funds = controller.get_filtered_funds({"sort_by": "spread_pct_desc"})
        assert sorted_funds[0]["spread_pct"] == 1.5

        # 测试升序排序
        sorted_funds = controller.get_filtered_funds({"sort_by": "spread_pct_asc"})
        assert sorted_funds[0]["spread_pct"] == -0.3

        # 测试收益率降序
        sorted_funds = controller.get_filtered_funds({"sort_by": "yield_pct_desc"})
        assert sorted_funds[0]["yield_pct"] == 1.2

        # 测试收益率升序
        sorted_funds = controller.get_filtered_funds({"sort_by": "yield_pct_asc"})
        assert sorted_funds[0]["yield_pct"] == -0.5

        # 测试代码排序
        sorted_funds = controller.get_filtered_funds({"sort_by": "code_asc"})
        assert sorted_funds[0]["code"] == "161005"

        # 测试名称排序（无名称字段，应返回空字符串排序）
        sorted_funds = controller.get_filtered_funds({"sort_by": "name_asc"})
        assert len(sorted_funds) == 3

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_fund_details(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取基金详情"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_data = [{"code": "510300", "name": "沪深300ETF", "type": "ETF", "nav": 3.56, "price": 3.58}]
        mock_history = [{"nav": 3.55, "price": 3.57, "timestamp": "2026-01-29"}]

        mock_fund_manager.get_latest_prices.return_value = mock_fund_data
        mock_fund_manager.get_price_history.return_value = mock_history
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        details = controller.get_fund_details("510300")

        assert "basic_info" in details
        assert "current_data" in details
        assert "history_data" in details
        assert "timestamp" in details
        mock_signal_manager.emit_fund_details_loaded.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_fund_details_not_found(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取不存在的基金详情"""
        mock_fund_manager = Mock()
        mock_fund_manager.get_latest_prices.return_value = []
        mock_get_fund_manager.return_value = mock_fund_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        details = controller.get_fund_details("INVALID")

        assert "error" in details

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_get_fund_details_exception(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试获取基金详情异常"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.get_latest_prices.side_effect = Exception("测试错误")
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        details = controller.get_fund_details("510300")

        assert "error" in details
        mock_signal_manager.emit_error_occurred.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_export_to_csv(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试导出CSV"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.export_to_csv.return_value = True
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        result = controller.export_to_csv("/tmp/test.csv")

        assert result is True
        mock_signal_manager.emit_status_changed.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_export_to_csv_failure_from_manager(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试导出CSV（管理器返回失败）"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.export_to_csv.return_value = False
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        result = controller.export_to_csv("/tmp/test.csv")

        assert result is False
        # 应该发送失败状态
        mock_signal_manager.emit_status_changed.assert_called_with("数据导出失败")

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_export_to_csv_exception(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试导出CSV异常"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.export_to_csv.side_effect = Exception("导出错误")
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        result = controller.export_to_csv("/tmp/test.csv")

        assert result is False
        mock_signal_manager.emit_error_occurred.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_cancel_refresh_when_not_refreshing(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试取消刷新（未刷新时）"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = False
        controller.refresh_worker = None

        # 不应抛出异常
        controller.cancel_refresh()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_cancel_refresh_when_refreshing(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试取消刷新（刷新中）"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 模拟正在刷新的状态
        controller.is_refreshing = True
        mock_worker = Mock()
        controller.refresh_worker = mock_worker

        controller.cancel_refresh()

        mock_worker.cancel.assert_called_once()
        mock_signal_manager.emit_status_changed.assert_called_with("刷新已取消")

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_cleanup(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试清理资源"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.cleanup()

        mock_signal_manager.clear_all_connections.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_cleanup_exception(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试清理资源异常"""
        mock_signal_manager = Mock()
        mock_signal_manager.clear_all_connections.side_effect = Exception("清理错误")
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 不应抛出异常
        controller.cleanup()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_refresh_all_data_async_already_refreshing(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试重复刷新请求"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = True

        result = controller.refresh_all_data_async()

        assert result is False
        mock_signal_manager.emit_status_changed.assert_called_with("刷新正在进行中...")

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_refresh_selected_funds_async_already_refreshing(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试重复刷新指定基金请求"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = True

        result = controller.refresh_selected_funds_async(["510300"])

        assert result is False

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    @patch('src.controllers.data_controller.DataRefreshWorker')
    def test_refresh_all_data_async_success(self, mock_worker_class, mock_get_signal_manager, mock_get_fund_manager):
        """测试异步刷新所有数据"""
        mock_signal_manager = Mock()
        mock_worker = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager
        mock_worker_class.return_value = mock_worker

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = False

        result = controller.refresh_all_data_async()

        assert result is True
        assert controller.is_refreshing is True
        mock_worker.start.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    @patch('src.controllers.data_controller.DataRefreshWorker')
    def test_refresh_all_data_async_exception(self, mock_worker_class, mock_get_signal_manager, mock_get_fund_manager):
        """测试异步刷新异常"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager
        mock_worker_class.side_effect = Exception("创建工作线程失败")

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = False

        result = controller.refresh_all_data_async()

        assert result is False
        assert controller.is_refreshing is False
        mock_signal_manager.emit_error_occurred.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    @patch('src.controllers.data_controller.DataRefreshWorker')
    def test_refresh_selected_funds_async_success(self, mock_worker_class, mock_get_signal_manager, mock_get_fund_manager):
        """测试异步刷新指定基金"""
        mock_signal_manager = Mock()
        mock_worker = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager
        mock_worker_class.return_value = mock_worker

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = False

        result = controller.refresh_selected_funds_async(["510300", "161005"])

        assert result is True
        assert controller.is_refreshing is True
        mock_worker_class.assert_called_with(["510300", "161005"])
        mock_worker.start.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    @patch('src.controllers.data_controller.DataRefreshWorker')
    def test_refresh_selected_funds_async_exception(self, mock_worker_class, mock_get_signal_manager, mock_get_fund_manager):
        """测试异步刷新指定基金异常"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager
        mock_worker_class.side_effect = Exception("创建工作线程失败")

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = False

        result = controller.refresh_selected_funds_async(["510300"])

        assert result is False
        assert controller.is_refreshing is False
        mock_signal_manager.emit_error_occurred.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_refresh_complete(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试刷新完成处理"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.get_statistics.return_value = {"total_funds": 10}
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        result = {"success": True, "total_opportunities": 5}
        controller._on_refresh_complete(result)

        assert controller.last_refresh_time is not None
        mock_signal_manager.emit_data_refreshed.assert_called_with(result)
        mock_signal_manager.emit_status_changed.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_refresh_complete_exception(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试刷新完成处理异常"""
        mock_fund_manager = Mock()
        mock_signal_manager = Mock()
        mock_fund_manager.get_statistics.side_effect = Exception("统计错误")
        mock_get_fund_manager.return_value = mock_fund_manager
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 不应抛出异常
        controller._on_refresh_complete({"success": True})

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_refresh_progress(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试刷新进度处理"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        controller._on_refresh_progress(50, "进度50%")

        mock_signal_manager.emit_progress_updated.assert_called_with(50, "进度50%")
        mock_signal_manager.emit_status_changed.assert_called_with("进度50%")

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_refresh_error(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试刷新错误处理"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        controller._on_refresh_error("测试错误")

        mock_signal_manager.emit_data_refresh_failed.assert_called_with("测试错误")
        mock_signal_manager.emit_status_changed.assert_called()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_refresh_finished(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试刷新线程结束处理"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()
        controller.is_refreshing = True
        mock_worker = Mock()
        controller.refresh_worker = mock_worker

        controller._on_refresh_finished()

        assert controller.is_refreshing is False
        mock_worker.deleteLater.assert_called_once()
        assert controller.refresh_worker is None

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_data_refresh_started(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试数据刷新开始信号处理"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        with patch.object(controller, 'refresh_all_data_async') as mock_refresh:
            controller._on_data_refresh_started()
            mock_refresh.assert_called_once()

    @patch('src.controllers.data_controller.get_fund_manager')
    @patch('src.controllers.data_controller.get_signal_manager')
    def test_on_filter_applied(self, mock_get_signal_manager, mock_get_fund_manager):
        """测试筛选条件应用信号处理"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.data_controller import DataController
        controller = DataController()

        # 不应抛出异常
        controller._on_filter_applied({"fund_type": "ETF"})


class TestDataRefreshWorker:
    """数据刷新工作线程测试"""

    def test_init_no_codes(self):
        """测试无参数初始化"""
        from src.controllers.data_controller import DataRefreshWorker

        worker = DataRefreshWorker()
        assert worker.fund_codes is None
        assert worker.is_cancelled is False

    def test_init_with_codes(self):
        """测试带参数初始化"""
        from src.controllers.data_controller import DataRefreshWorker

        worker = DataRefreshWorker(["510300", "161005"])
        assert worker.fund_codes == ["510300", "161005"]

    def test_cancel(self):
        """测试取消功能"""
        from src.controllers.data_controller import DataRefreshWorker

        worker = DataRefreshWorker()
        assert worker.is_cancelled is False

        worker.cancel()
        assert worker.is_cancelled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
