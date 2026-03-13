"""
主控制器单元测试 - 完整覆盖版本
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestMainController:
    """主控制器测试"""

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_init(self, mock_get_signal_manager, mock_data_controller_class):
        """测试初始化"""
        mock_data_controller = Mock()
        mock_signal_manager = Mock()

        mock_data_controller_class.return_value = mock_data_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()

        assert controller.data_controller == mock_data_controller
        assert controller.signal_manager == mock_signal_manager
        assert controller.current_filters == {}

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_connect_signals(self, mock_get_signal_manager, mock_data_controller_class):
        """测试连接信号"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()

        # _connect_signals 被调用（目前是空实现）
        # 不应抛出异常
        controller._connect_signals()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_refresh_all_data(self, mock_get_signal_manager, mock_data_controller_class):
        """测试刷新所有数据"""
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.refresh_all_data()

        assert result["success"] is True
        assert "message" in result
        mock_signal_manager.emit_data_refresh_started.assert_called_once()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_refresh_all_data_failure(self, mock_get_signal_manager, mock_data_controller_class):
        """测试刷新数据失败"""
        mock_signal_manager = Mock()
        mock_signal_manager.emit_data_refresh_started.side_effect = Exception("测试错误")
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.refresh_all_data()

        assert result["success"] is False
        assert "error" in result
        assert "测试错误" in result["error"]

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_refresh_selected_funds_success(self, mock_get_signal_manager, mock_data_controller_class):
        """测试刷新指定基金成功"""
        mock_data_controller = Mock()
        mock_data_controller.refresh_selected_funds_async.return_value = True
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.refresh_selected_funds(["510300", "161005"])

        assert result["success"] is True
        assert "message" in result
        mock_data_controller.refresh_selected_funds_async.assert_called_once_with(["510300", "161005"])

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_refresh_selected_funds_failure(self, mock_get_signal_manager, mock_data_controller_class):
        """测试刷新指定基金失败（返回False）"""
        mock_data_controller = Mock()
        mock_data_controller.refresh_selected_funds_async.return_value = False
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.refresh_selected_funds(["510300"])

        assert result["success"] is False
        assert "刷新启动失败" in result["message"]

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_refresh_selected_funds_exception(self, mock_get_signal_manager, mock_data_controller_class):
        """测试刷新指定基金异常"""
        mock_data_controller = Mock()
        mock_data_controller.refresh_selected_funds_async.side_effect = Exception("刷新错误")
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.refresh_selected_funds(["510300"])

        assert result["success"] is False
        assert "error" in result
        assert "刷新错误" in result["error"]

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_statistics(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取统计信息"""
        mock_data_controller = Mock()
        mock_stats = {"total_funds": 10, "etf_count": 6, "lof_count": 4}
        mock_data_controller.get_statistics.return_value = mock_stats
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        stats = controller.get_statistics()

        assert stats == mock_stats
        mock_data_controller.get_statistics.assert_called_once()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_all_funds(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取所有基金"""
        mock_data_controller = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF"},
            {"code": "161005", "name": "富国天惠LOF"}
        ]
        mock_data_controller.get_all_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        funds = controller.get_all_funds()

        assert funds == mock_funds
        mock_data_controller.get_all_funds.assert_called_once()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_filtered_funds_with_params(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取筛选后的基金（带参数）"""
        mock_data_controller = Mock()
        mock_funds = [{"code": "510300", "name": "沪深300ETF"}]
        mock_data_controller.get_filtered_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        filter_params = {"fund_type": "ETF"}
        funds = controller.get_filtered_funds(filter_params)

        assert funds == mock_funds
        assert controller.current_filters == filter_params
        mock_data_controller.get_filtered_funds.assert_called_with(filter_params)

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_filtered_funds_no_params(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取筛选后的基金（无参数，使用当前筛选条件）"""
        mock_data_controller = Mock()
        mock_funds = [{"code": "510300", "name": "沪深300ETF"}]
        mock_data_controller.get_filtered_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        controller.current_filters = {"fund_type": "LOF"}

        funds = controller.get_filtered_funds(None)

        assert funds == mock_funds
        assert controller.current_filters == {"fund_type": "LOF"}  # 保持不变
        mock_data_controller.get_filtered_funds.assert_called_with({"fund_type": "LOF"})

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_apply_filters(self, mock_get_signal_manager, mock_data_controller_class):
        """测试应用筛选条件"""
        mock_data_controller = Mock()
        mock_signal_manager = Mock()
        mock_funds = [{"code": "510300", "name": "沪深300ETF"}]
        mock_data_controller.get_filtered_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()
        filter_params = {"fund_type": "ETF", "min_spread": 0.5}
        funds = controller.apply_filters(filter_params)

        assert funds == mock_funds
        assert controller.current_filters == filter_params
        mock_signal_manager.emit_filter_applied.assert_called_with(filter_params)

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_fund_details(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取基金详情"""
        mock_data_controller = Mock()
        mock_details = {"code": "510300", "name": "沪深300ETF", "type": "ETF"}
        mock_data_controller.get_fund_details.return_value = mock_details
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        details = controller.get_fund_details("510300")

        assert details == mock_details
        mock_data_controller.get_fund_details.assert_called_with("510300")

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_search_funds_by_code(self, mock_get_signal_manager, mock_data_controller_class):
        """测试按代码搜索基金"""
        mock_data_controller = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF"},
            {"code": "510500", "name": "中证500ETF"},
            {"code": "161005", "name": "富国天惠LOF"}
        ]
        mock_data_controller.get_all_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()

        results = controller.search_funds("5103")
        assert len(results) == 1
        assert results[0]["code"] == "510300"

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_search_funds_by_name(self, mock_get_signal_manager, mock_data_controller_class):
        """测试按名称搜索基金"""
        mock_data_controller = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF"},
            {"code": "510500", "name": "中证500ETF"},
            {"code": "161005", "name": "富国天惠LOF"}
        ]
        mock_data_controller.get_all_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()

        results = controller.search_funds("富国")
        assert len(results) == 1
        assert "富国" in results[0]["name"]

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_search_funds_case_insensitive(self, mock_get_signal_manager, mock_data_controller_class):
        """测试搜索基金（不区分大小写）"""
        mock_data_controller = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF"},
        ]
        mock_data_controller.get_all_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()

        results = controller.search_funds("etf")
        assert len(results) == 1

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_search_funds_no_results(self, mock_get_signal_manager, mock_data_controller_class):
        """测试搜索基金无结果"""
        mock_data_controller = Mock()
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF"},
        ]
        mock_data_controller.get_all_funds.return_value = mock_funds
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()

        results = controller.search_funds("不存在")
        assert len(results) == 0

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_export_to_csv(self, mock_get_signal_manager, mock_data_controller_class):
        """测试导出CSV"""
        mock_data_controller = Mock()
        mock_data_controller.export_to_csv.return_value = True
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        result = controller.export_to_csv("/tmp/test.csv")

        assert result is True
        mock_data_controller.export_to_csv.assert_called_with("/tmp/test.csv")

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_last_update_time(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取最后更新时间"""
        mock_data_controller = Mock()
        mock_data_controller.get_statistics.return_value = {"last_update": "2026-01-30T12:00:00"}
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        last_update = controller.get_last_update_time()

        assert last_update == "2026-01-30T12:00:00"

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_get_last_update_time_none(self, mock_get_signal_manager, mock_data_controller_class):
        """测试获取最后更新时间（无更新时间）"""
        mock_data_controller = Mock()
        mock_data_controller.get_statistics.return_value = {}
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        last_update = controller.get_last_update_time()

        assert last_update is None

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_switch_data_source(self, mock_get_signal_manager, mock_data_controller_class):
        """测试切换数据源"""
        mock_data_controller = Mock()
        mock_signal_manager = Mock()
        mock_data_controller_class.return_value = mock_data_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()

        # 切换数据源
        controller.switch_data_source("eastmoney")

        # 应该发送状态变更信号
        mock_signal_manager.emit_status_changed.assert_called()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_switch_data_source_exception(self, mock_get_signal_manager, mock_data_controller_class):
        """测试切换数据源异常"""
        mock_data_controller = Mock()
        mock_signal_manager = Mock()
        mock_data_controller.cleanup.side_effect = Exception("清理失败")
        mock_data_controller_class.return_value = mock_data_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.controllers.main_controller import MainController
        controller = MainController()

        # 切换数据源（不应抛出异常）
        # 注意：cleanup异常会被cleanup方法内部捕获，不会触发emit_error_occurred
        controller.switch_data_source("eastmoney")

        # cleanup被调用
        mock_data_controller.cleanup.assert_called()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_cancel_refresh(self, mock_get_signal_manager, mock_data_controller_class):
        """测试取消刷新"""
        mock_data_controller = Mock()
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        controller.cancel_refresh()

        mock_data_controller.cancel_refresh.assert_called_once()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_cleanup(self, mock_get_signal_manager, mock_data_controller_class):
        """测试清理资源"""
        mock_data_controller = Mock()
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()
        controller.cleanup()

        mock_data_controller.cleanup.assert_called_once()

    @patch('src.controllers.main_controller.DataController')
    @patch('src.controllers.main_controller.get_signal_manager')
    def test_cleanup_exception(self, mock_get_signal_manager, mock_data_controller_class):
        """测试清理资源异常"""
        mock_data_controller = Mock()
        mock_data_controller.cleanup.side_effect = Exception("清理失败")
        mock_data_controller_class.return_value = mock_data_controller

        from src.controllers.main_controller import MainController
        controller = MainController()

        # 不应抛出异常
        controller.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
