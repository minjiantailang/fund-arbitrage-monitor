"""
主题管理器单元测试
"""
import pytest
from unittest.mock import Mock, patch

from src.ui.theme_manager import ThemeManager, get_theme_manager


class TestThemeManager:
    """主题管理器测试"""

    def test_init_default_theme(self):
        """测试默认主题初始化"""
        manager = ThemeManager()
        assert manager.current_theme == "modern"

    def test_set_theme_to_dark(self):
        """测试设置暗色主题"""
        manager = ThemeManager()
        manager.set_theme("dark")
        assert manager.current_theme == "dark"

    def test_set_theme_to_modern(self):
        """测试设置现代主题"""
        manager = ThemeManager()
        manager.set_theme("dark")  # 先设置为暗色
        manager.set_theme("modern")  # 再设置回现代
        assert manager.current_theme == "modern"

    def test_set_invalid_theme(self):
        """测试设置无效主题"""
        manager = ThemeManager()
        original_theme = manager.current_theme
        manager.set_theme("invalid_theme")
        # 主题不应该被更改
        assert manager.current_theme == original_theme

    def test_get_theme_names(self):
        """测试获取主题名称"""
        manager = ThemeManager()
        names = manager.get_theme_names()

        assert "modern" in names
        assert "dark" in names
        assert "现代极简" in names["modern"]
        assert "专业暗色" in names["dark"]

    def test_get_current_theme_info(self):
        """测试获取当前主题信息"""
        manager = ThemeManager()

        info = manager.get_current_theme_info()
        assert info["id"] == "modern"
        assert "现代极简" in info["name"]

        manager.set_theme("dark")
        info = manager.get_current_theme_info()
        assert info["id"] == "dark"
        assert "专业暗色" in info["name"]

    def test_theme_changed_signal(self):
        """测试主题变化信号"""
        manager = ThemeManager()

        # 创建信号接收器
        signal_received = []
        manager.theme_changed.connect(lambda theme: signal_received.append(theme))

        manager.set_theme("dark")
        assert "dark" in signal_received

    def test_set_same_theme_no_signal(self):
        """测试设置相同主题不触发信号"""
        manager = ThemeManager()

        signal_received = []
        manager.theme_changed.connect(lambda theme: signal_received.append(theme))

        manager.set_theme("light")  # 已经是light，不应触发
        assert len(signal_received) == 0

    def test_themes_have_stylesheets(self):
        """测试主题包含样式表"""
        for theme_id, theme in ThemeManager.THEMES.items():
            assert "name" in theme
            assert "stylesheet" in theme
            assert isinstance(theme["stylesheet"], str)
            assert len(theme["stylesheet"]) > 0


class TestGetThemeManager:
    """测试get_theme_manager函数"""

    def test_returns_theme_manager(self):
        """测试返回主题管理器实例"""
        manager = get_theme_manager()
        assert isinstance(manager, ThemeManager)

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_theme_manager()
        manager2 = get_theme_manager()
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
