"""
信号管理器单元测试
"""
import pytest
from unittest.mock import Mock, patch


class TestSignalManager:
    """信号管理器测试"""

    def test_init(self):
        """测试初始化"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        assert manager._signal_handlers == {}

    def test_connect_signal(self):
        """测试连接信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler = Mock()
        handler.__name__ = "test_handler"
        manager.connect_signal("data_refreshed", handler)

        assert "data_refreshed" in manager._signal_handlers
        assert handler in manager._signal_handlers["data_refreshed"]

    def test_connect_invalid_signal(self):
        """测试连接不存在的信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler = Mock()
        handler.__name__ = "test_handler"

        # 不应抛出异常
        manager.connect_signal("invalid_signal", handler)

    def test_disconnect_signal(self):
        """测试断开信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler = Mock()
        handler.__name__ = "test_handler"
        manager.connect_signal("data_refreshed", handler)

        # 断开特定处理器
        manager.disconnect_signal("data_refreshed", handler)
        assert handler not in manager._signal_handlers.get("data_refreshed", [])

    def test_disconnect_all_handlers(self):
        """测试断开所有处理器"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler1 = Mock()
        handler1.__name__ = "handler1"
        handler2 = Mock()
        handler2.__name__ = "handler2"

        manager.connect_signal("data_refreshed", handler1)
        manager.connect_signal("data_refreshed", handler2)

        # 断开所有处理器
        manager.disconnect_signal("data_refreshed", None)
        assert len(manager._signal_handlers.get("data_refreshed", [])) == 0

    def test_disconnect_nonexistent_signal(self):
        """测试断开不存在的信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        # 不应抛出异常
        manager.disconnect_signal("nonexistent_signal")

    def test_emit_signal(self):
        """测试发射信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        # 不应抛出异常
        manager.emit_signal("data_refresh_started")

    def test_emit_invalid_signal(self):
        """测试发射不存在的信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        # 不应抛出异常
        manager.emit_signal("invalid_signal")

    def test_emit_data_refreshed(self):
        """测试发射数据刷新完成信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        result = {"success": True, "total_funds": 10}
        # 不应抛出异常
        manager.emit_data_refreshed(result)

    def test_emit_data_refresh_started(self):
        """测试发射数据刷新开始信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_data_refresh_started()

    def test_emit_data_refresh_failed(self):
        """测试发射数据刷新失败信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_data_refresh_failed("测试错误")

    def test_emit_fund_selected(self):
        """测试发射基金选中信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_fund_selected("510300")

    def test_emit_fund_double_clicked(self):
        """测试发射基金双击信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_fund_double_clicked("510300")

    def test_emit_fund_details_loaded(self):
        """测试发射基金详情加载完成信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_fund_details_loaded({"code": "510300", "name": "测试"})

    def test_emit_filter_applied(self):
        """测试发射筛选条件应用信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_filter_applied({"fund_type": "ETF"})

    def test_emit_filter_cleared(self):
        """测试发射筛选条件清除信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_filter_cleared()

    def test_emit_status_changed(self):
        """测试发射状态变化信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_status_changed("测试状态")

    def test_emit_progress_updated(self):
        """测试发射进度更新信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_progress_updated(50, "进度50%")

    def test_emit_error_occurred(self):
        """测试发射错误发生信号"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()
        manager.emit_error_occurred("test_error", "测试错误信息")

    def test_clear_all_connections(self):
        """测试清除所有连接"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler1 = Mock()
        handler1.__name__ = "handler1"
        handler2 = Mock()
        handler2.__name__ = "handler2"

        manager.connect_signal("data_refreshed", handler1)
        manager.connect_signal("status_changed", handler2)

        manager.clear_all_connections()

        assert len(manager._signal_handlers.get("data_refreshed", [])) == 0
        assert len(manager._signal_handlers.get("status_changed", [])) == 0

    def test_get_connection_count_specific(self):
        """测试获取特定信号连接数量"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler1 = Mock()
        handler1.__name__ = "handler1"
        handler2 = Mock()
        handler2.__name__ = "handler2"

        manager.connect_signal("data_refreshed", handler1)
        manager.connect_signal("data_refreshed", handler2)

        assert manager.get_connection_count("data_refreshed") == 2
        assert manager.get_connection_count("status_changed") == 0

    def test_get_connection_count_total(self):
        """测试获取总连接数量"""
        from src.controllers.signal_manager import SignalManager
        manager = SignalManager()

        handler1 = Mock()
        handler1.__name__ = "handler1"
        handler2 = Mock()
        handler2.__name__ = "handler2"

        manager.connect_signal("data_refreshed", handler1)
        manager.connect_signal("status_changed", handler2)

        assert manager.get_connection_count() == 2


class TestGetSignalManager:
    """获取信号管理器单例测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        import src.controllers.signal_manager as sm
        sm._signal_manager_instance = None

        manager1 = sm.get_signal_manager()
        manager2 = sm.get_signal_manager()

        assert manager1 is manager2

        # 清理
        sm._signal_manager_instance = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
