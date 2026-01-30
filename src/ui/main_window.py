"""
主窗口
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QToolBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .dashboard_widget import DashboardWidget
from .fund_list_widget import FundListWidget
from .filters_widget import FiltersWidget
from ..controllers.main_controller import MainController
from ..controllers.signal_manager import get_signal_manager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""

    # 信号定义
    data_refreshed = pyqtSignal(dict)  # 数据刷新完成信号
    refresh_requested = pyqtSignal()   # 刷新数据请求信号

    def __init__(self):
        super().__init__()
        self.controller: Optional[MainController] = None
        self.signal_manager = get_signal_manager()
        self._init_ui()
        self._init_controller()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("基金套利监控")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 创建工具栏
        self._create_toolbar()

        # 创建分割器（左右布局）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：仪表盘
        self.dashboard_widget = DashboardWidget()
        splitter.addWidget(self.dashboard_widget)

        # 右侧：基金列表和筛选器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # 筛选器
        self.filters_widget = FiltersWidget()
        right_layout.addWidget(self.filters_widget)

        # 基金列表
        self.fund_list_widget = FundListWidget()
        right_layout.addWidget(self.fund_list_widget)

        splitter.addWidget(right_widget)

        # 设置分割器比例（左侧70%，右侧30%）
        splitter.setSizes([840, 360])

        main_layout.addWidget(splitter)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 创建定时器用于状态更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 刷新数据动作
        refresh_action = QAction("刷新数据", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self._on_refresh_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 导出数据动作
        export_action = QAction("导出CSV", self)
        export_action.triggered.connect(self._on_export_data)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # 设置动作
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        # 关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        toolbar.addAction(about_action)

    def _init_controller(self):
        """初始化控制器"""
        try:
            self.controller = MainController()
            logger.info("控制器初始化成功")
        except Exception as e:
            logger.error(f"控制器初始化失败: {e}")
            QMessageBox.critical(self, "错误", f"控制器初始化失败: {e}")

    def _connect_signals(self):
        """连接信号"""
        # 连接刷新信号
        self.refresh_requested.connect(self._refresh_data)

        # 连接筛选器信号
        self.filters_widget.filter_changed.connect(self._on_filter_changed)

        # 连接基金列表信号
        self.fund_list_widget.fund_selected.connect(self._on_fund_selected)

    def _refresh_data(self):
        """刷新数据"""
        if not self.controller:
            self.status_bar.showMessage("错误：控制器未初始化")
            return

        self.status_bar.showMessage("正在刷新数据...")
        self.setEnabled(False)  # 禁用界面防止重复操作

        try:
            # 异步刷新数据
            result = self.controller.refresh_all_data()

            if result.get("success"):
                # 更新UI
                self._update_ui_after_refresh(result)
                self.status_bar.showMessage(f"数据刷新完成，发现 {result.get('total_opportunities', 0)} 个套利机会")
            else:
                error_msg = result.get("error", "未知错误")
                self.status_bar.showMessage(f"数据刷新失败: {error_msg}")
                QMessageBox.warning(self, "刷新失败", f"数据刷新失败: {error_msg}")

        except Exception as e:
            logger.error(f"刷新数据异常: {e}")
            self.status_bar.showMessage(f"刷新数据异常: {e}")
            QMessageBox.critical(self, "错误", f"刷新数据异常: {e}")

        finally:
            self.setEnabled(True)

    def _update_ui_after_refresh(self, result: dict):
        """刷新后更新UI"""
        try:
            # 获取最新数据
            statistics = self.controller.get_statistics()
            fund_data = self.controller.get_filtered_funds()

            # 更新仪表盘
            self.dashboard_widget.update_statistics(statistics)

            # 更新基金列表
            self.fund_list_widget.update_fund_data(fund_data)

            # 发出数据刷新完成信号
            self.data_refreshed.emit(result)

        except Exception as e:
            logger.error(f"更新UI失败: {e}")

    def _on_refresh_data(self):
        """处理刷新数据动作"""
        self.refresh_requested.emit()

    def _on_export_data(self):
        """处理导出数据动作"""
        if not self.controller:
            QMessageBox.warning(self, "警告", "控制器未初始化")
            return

        try:
            # TODO: 实现导出文件对话框
            file_path = "fund_data_export.csv"
            success = self.controller.export_to_csv(file_path)

            if success:
                self.status_bar.showMessage(f"数据已导出到: {file_path}")
                QMessageBox.information(self, "导出成功", f"数据已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "数据导出失败")

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            QMessageBox.critical(self, "错误", f"导出数据失败: {e}")

    def _on_settings(self):
        """处理设置动作"""
        # TODO: 实现设置对话框
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def _on_about(self):
        """处理关于动作"""
        about_text = """
        <h3>基金套利监控 v0.1.0</h3>
        <p>一个用于监控ETF和LOF基金套利机会的桌面应用。</p>
        <p><b>功能特性：</b></p>
        <ul>
            <li>实时监控ETF基金净值与市场价格差异</li>
            <li>监控LOF基金场内场外套利机会</li>
            <li>手动数据更新和本地缓存</li>
            <li>可视化仪表盘和基金列表</li>
        </ul>
        <p><b>技术栈：</b></p>
        <ul>
            <li>Python 3.12 + PyQt6</li>
            <li>Pandas + SQLite</li>
            <li>模拟数据/东方财富API</li>
        </ul>
        <p>仅供学习和研究使用，不构成投资建议。</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def _on_filter_changed(self, filter_params: dict):
        """处理筛选器变化"""
        if not self.controller:
            return

        try:
            # 应用筛选条件
            filtered_data = self.controller.apply_filters(filter_params)
            self.fund_list_widget.update_fund_data(filtered_data)

            # 更新统计信息（基于筛选条件）
            statistics = self.controller.get_statistics()
            self.dashboard_widget.update_statistics(statistics)

            self.status_bar.showMessage(f"已应用筛选条件，显示 {len(filtered_data)} 条记录")

        except Exception as e:
            logger.error(f"应用筛选条件失败: {e}")

    def _on_fund_selected(self, fund_code: str):
        """处理基金选择"""
        if not self.controller:
            return

        try:
            # 获取基金详情
            fund_details = self.controller.get_fund_details(fund_code)

            # TODO: 显示基金详情对话框
            self.status_bar.showMessage(f"选中基金: {fund_code}")

        except Exception as e:
            logger.error(f"获取基金详情失败: {e}")

    def _update_status(self):
        """更新状态栏"""
        if not self.controller:
            return

        try:
            # 获取最后更新时间
            last_update = self.controller.get_last_update_time()
            if last_update:
                self.status_bar.showMessage(f"最后更新: {last_update} | 就绪")
        except Exception as e:
            logger.debug(f"更新状态失败: {e}")

    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            if self.controller:
                self.controller.cleanup()
            logger.info("应用关闭")
        except Exception as e:
            logger.error(f"关闭应用时出错: {e}")

        event.accept()