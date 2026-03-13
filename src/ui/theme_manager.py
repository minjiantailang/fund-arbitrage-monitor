"""
主题管理器 - 支持亮色/暗色主题切换
"""
import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """主题管理器 - 支持亮色和暗色主题切换"""

    # 信号
    theme_changed = pyqtSignal(str)  # 主题变化信号

    # 主题定义
    THEMES = {
        "modern": {
            "name": "现代极简 (Modern)",
            "stylesheet": """
                /* 全局设置 */
                QMainWindow {
                    background-color: #F5F7FA;
                }
                QWidget {
                    font-family: -apple-system, "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", "Microsoft YaHei", sans-serif;
                    font-size: 13px;
                    color: #2C3E50;
                }
                
                /* 卡片容器 - 增加阴影感(通过边框模拟)和圆角 */
                QFrame#DashboardCard, QFrame#ChartCard, QFrame#ListCard, QFrame#FilterContainer {
                    background-color: #FFFFFF;
                    border: 1px solid #E1E4E8;
                    border-radius: 12px;
                }

                /* 标签系统 */
                QLabel {
                    color: #4A5568;
                }
                QLabel#StatValue {
                    color: #2D3748;
                    font-size: 28px;
                    font-weight: 700;
                    font-family: "SF Pro Display", -apple-system, sans-serif;
                    qproperty-alignment: AlignCenter;
                }
                QLabel#StatLabel {
                    color: #718096;
                    font-size: 13px;
                    font-weight: 500;
                    qproperty-alignment: AlignCenter;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QLabel#ChartTitle {
                    color: #2D3748;
                    font-size: 16px;
                    font-weight: 700;
                    padding-bottom: 8px;
                }

                /* 表格 - 现代化重设计 */
                QTableWidget {
                    background-color: #FFFFFF;
                    alternate-background-color: #FAFCFE; /* 斑马纹 */
                    gridline-color: transparent; /* 隐藏网格线 */
                    border: none;
                    selection-background-color: #EBF8FF;
                    selection-color: #2B6CB0;
                    outline: none;
                }
                QTableWidget::item {
                    padding: 12px 16px; /* 更多呼吸空间 */
                    border-bottom: 1px solid #F0F4F8;
                    color: #2D3748;
                }
                QTableWidget::item:selected {
                    background-color: #EBF8FF;
                    color: #2B6CB0;
                    font-weight: 600;
                }
                QHeaderView::section {
                    background-color: #FFFFFF;
                    color: #718096;
                    border: none;
                    border-bottom: 2px solid #E2E8F0;
                    padding: 12px 16px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                /* 按钮系统 */
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #CBD5E0;
                    border-radius: 6px;
                    color: #4A5568;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    color: #3182CE;
                    border-color: #3182CE;
                    background-color: #F7FAFC;
                }
                QPushButton:pressed {
                    color: #2C5282;
                    border-color: #2C5282;
                    background-color: #EBF8FF;
                }
                /* 主按钮 */
                QPushButton[primary="true"] {
                    background-color: #3182CE;
                    border: 1px solid #3182CE;
                    color: #FFFFFF;
                    font-weight: 600;
                }
                QPushButton[primary="true"]:hover {
                    background-color: #4299E1;
                    border-color: #4299E1;
                }
                QPushButton[primary="true"]:pressed {
                    background-color: #2B6CB0;
                    border-color: #2B6CB0;
                }

                /* 输入控件 */
                QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background-color: #FFFFFF;
                    selection-background-color: #3182CE;
                    font-size: 13px;
                }
                QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                    border-color: #3182CE;
                    background-color: #FFFFFF;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }

                /* 滚动条 - 极简风格 */
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 10px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background: #CBD5E0;
                    border-radius: 5px;
                    min-height: 40px;
                    margin: 0 2px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #A0AEC0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0; 
                }
                
                /* 工具栏 */
                QToolBar {
                    background-color: #FFFFFF;
                    border-bottom: 1px solid #E2E8F0;
                    spacing: 16px;
                    padding: 8px 16px;
                }
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 6px;
                    color: #4A5568;
                }
                QToolButton:hover {
                    background-color: #EDF2F7;
                    color: #2D3748;
                }
                
                /* 状态栏 */
                QStatusBar {
                    background-color: #FFFFFF;
                    border-top: 1px solid #E2E8F0;
                    color: #718096;
                    font-size: 12px;
                }

                /* Splitter */
                QSplitter::handle {
                    background-color: #E2E8F0;
                    width: 1px;
                }
            """
        },
        "dark": {
            "name": "专业暗色 (Dark Pro)",
            "stylesheet": """
                /* 全局设置 */
                QMainWindow {
                    background-color: #141414;
                }
                QWidget {
                    font-family: -apple-system, "SF Pro Text", "Segoe UI", "Roboto", "Helvetica Neue", "Microsoft YaHei", sans-serif;
                    font-size: 13px;
                    color: #E6F7FF;
                }
                
                /* 卡片容器 */
                QFrame#DashboardCard, QFrame#ChartCard, QFrame#ListCard, QFrame#FilterContainer {
                    background-color: #1F1F1F;
                    border: 1px solid #303030;
                    border-radius: 12px;
                }

                /* 标签 */
                QLabel {
                    color: #A6A6A6;
                }
                QLabel#StatValue {
                    color: #FFFFFF;
                    font-size: 28px;
                    font-weight: 700;
                    font-family: "SF Pro Display", -apple-system, sans-serif;
                    qproperty-alignment: AlignCenter;
                }
                QLabel#StatLabel {
                    color: #8C8C8C;
                    font-size: 13px;
                    font-weight: 500;
                    qproperty-alignment: AlignCenter;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QLabel#ChartTitle {
                    color: #FFFFFF;
                    font-size: 16px;
                    font-weight: 700;
                    padding-bottom: 8px;
                }

                /* 表格 */
                QTableWidget {
                    background-color: #1F1F1F;
                    alternate-background-color: #262626;
                    gridline-color: transparent;
                    border: none;
                    selection-background-color: #177DDC;
                    selection-color: #FFFFFF;
                    outline: none;
                }
                QTableWidget::item {
                    padding: 12px 16px;
                    border-bottom: 1px solid #303030;
                    color: #E6F7FF;
                }
                QTableWidget::item:selected {
                    background-color: #114674;
                    color: #FFFFFF;
                    font-weight: 600;
                }
                QHeaderView::section {
                    background-color: #1F1F1F;
                    color: #8C8C8C;
                    border: none;
                    border-bottom: 2px solid #303030;
                    padding: 12px 16px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                /* 按钮 */
                QPushButton {
                    background-color: #262626;
                    border: 1px solid #434343;
                    border-radius: 6px;
                    color: #E6F7FF;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    color: #40A9FF;
                    border-color: #40A9FF;
                    background-color: #1F1F1F;
                }
                QPushButton:pressed {
                    color: #096DD9;
                    border-color: #096DD9;
                    background-color: #114674;
                }
                
                QPushButton[primary="true"] {
                    background-color: #177DDC;
                    border: 1px solid #177DDC;
                    color: #FFFFFF;
                    font-weight: 600;
                }
                QPushButton[primary="true"]:hover {
                    background-color: #40A9FF;
                    border-color: #40A9FF;
                }

                /* 输入控件 */
                QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
                    border: 1px solid #434343;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background-color: #262626;
                    selection-background-color: #177DDC;
                    color: #E6F7FF;
                }
                QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                    border-color: #177DDC;
                    background-color: #262626;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }

                /* 滚动条 */
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 10px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background: #434343;
                    border-radius: 5px;
                    min-height: 40px;
                    margin: 0 2px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #595959;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0; 
                }
                
                /* 工具栏 */
                QToolBar {
                    background-color: #1F1F1F;
                    border-bottom: 1px solid #303030;
                    spacing: 16px;
                    padding: 8px 16px;
                }
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 6px;
                    color: #A6A6A6;
                }
                QToolButton:hover {
                    background-color: #262626;
                    color: #FFFFFF;
                }
                
                /* 状态栏 */
                QStatusBar {
                    background-color: #1F1F1F;
                    border-top: 1px solid #303030;
                    color: #8C8C8C;
                }

                /* Splitter */
                QSplitter::handle {
                    background-color: #303030;
                    width: 1px;
                }
            """
        }
    }

    def __init__(self, app: Optional[QApplication] = None):
        super().__init__()
        self._app = app or QApplication.instance()
        self._current_theme = "modern"  # 默认使用现代主题

    @property
    def current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme

    def set_theme(self, theme_name: str):
        """
        设置主题
        
        Args:
            theme_name: 主题名称 (modern)
        """
        if theme_name not in self.THEMES:
            logger.warning(f"未知主题: {theme_name}")
            return
            
        if theme_name == self._current_theme and self._app and not self._app.styleSheet():
             # 如果是相同主题但app没有样式表，仍需设置
             pass
        elif theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        theme = self.THEMES[theme_name]
        
        if self._app:
            self._app.setStyleSheet(theme["stylesheet"])
            logger.info(f"应用主题: {theme['name']}")
        
        self.theme_changed.emit(theme_name)
    
    # 移除 toggle_theme 方法

    def get_theme_names(self) -> Dict[str, str]:
        """
        获取所有可用主题

        Returns:
            Dict: {主题ID: 主题名称}
        """
        return {key: value["name"] for key, value in self.THEMES.items()}

    def get_current_theme_info(self) -> Dict[str, Any]:
        """
        获取当前主题信息

        Returns:
            Dict: 当前主题信息
        """
        return {
            "id": self._current_theme,
            "name": self.THEMES[self._current_theme]["name"],
        }


# 全局主题管理器实例
_theme_manager_instance: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """
    获取主题管理器实例

    Returns:
        ThemeManager: 主题管理器实例
    """
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance
