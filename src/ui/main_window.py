"""
主窗口
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QToolBar, QMessageBox, QApplication, QStyle, QComboBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QActionGroup

from .dashboard_widget import DashboardWidget
from .fund_list_widget import FundListWidget
from .filters_widget import FiltersWidget
from .theme_manager import get_theme_manager
from ..controllers.main_controller import MainController
from ..controllers.signal_manager import get_signal_manager
from ..utils.error_handler import catch_exception  # 新增

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
        self.theme_manager = get_theme_manager()
        self._selected_fund_code: Optional[str] = None  # 跟踪当前选中的基金
        
        # 强制应用现代主题
        self.theme_manager.set_theme("modern")
        
        self._init_ui()
        self._init_controller()
        self._connect_signals()
        self._setup_shortcuts()

    def _init_ui(self):
        """初始化UI"""
        self._setup_window_properties()

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self._create_menubar()
        self._create_toolbar()
        self._setup_layout(main_layout)
        self._setup_status_bar()
        self._setup_timers()
        
        # 初始化 Dashboard 数据源显示
        self.dashboard_widget.update_data_source("eastmoney")

    def _setup_window_properties(self):
        """设置窗口属性"""
        self.setWindowTitle("基金套利监控")
        self.setGeometry(100, 100, 1200, 800)

    def _setup_layout(self, main_layout):
        """设置主布局"""
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
        right_layout.addWidget(self.fund_list_widget, 1) # 让列表占据剩余空间

        splitter.addWidget(right_widget)

        # 设置分割器比例（左侧30%，右侧70%）
        splitter.setSizes([360, 840])
        
        # 设置伸缩因子，使右侧（列表）在窗口缩放时获得更多空间
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _setup_timers(self):
        """设置定时器"""
        # 创建定时器用于状态更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次
        
        # 自动刷新定时器 (每5分钟 = 300秒 = 300000毫秒)
        self.auto_refresh_interval = 5 * 60 * 1000  # 5分钟
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        self.auto_refresh_timer.start(self.auto_refresh_interval)
        
        # 倒计时追踪
        self._last_refresh_time = None

    def _create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 数据源菜单 - 仅保留东方财富
        source_menu = menubar.addMenu("数据源")
        
        eastmoney_action = QAction("东方财富 (实时)", self)
        eastmoney_action.setCheckable(True)
        eastmoney_action.setChecked(True)
        source_menu.addAction(eastmoney_action)

        # 主题菜单
        theme_menu = menubar.addMenu("主题")
        theme_group = QActionGroup(self)
        
        # 现代极简 (Modern)
        modern_action = QAction("现代极简", self)
        modern_action.setCheckable(True)
        modern_action.setChecked(True)
        modern_action.triggered.connect(lambda: self._change_theme("modern"))
        theme_menu.addAction(modern_action)
        theme_group.addAction(modern_action)
        
        # 专业暗色 (Dark Pro)
        dark_action = QAction("专业暗色", self)
        dark_action.setCheckable(True)
        dark_action.triggered.connect(lambda: self._change_theme("dark"))
        theme_menu.addAction(dark_action)
        theme_group.addAction(dark_action)

    def _change_theme(self, theme_name: str):
        """切换主题"""
        self.theme_manager.set_theme(theme_name)
        self.status_bar.showMessage(f"已切换主题: {theme_name}")

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 刷新动作
        refresh_action = QAction("刷新数据", self)
        refresh_action.setStatusTip("刷新当前基金数据")
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self._on_refresh_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 数据源标签（仅显示，不可切换）
        from PyQt6.QtWidgets import QLabel
        source_label = QLabel("数据源: 东方财富")
        source_label.setStyleSheet("padding: 0 10px;")
        toolbar.addWidget(source_label)

        toolbar.addSeparator()

        # 导出动作
        export_action = QAction("导出数据", self)
        export_action.setStatusTip("导出当前数据到文件")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export_data)
        toolbar.addAction(export_action)
        


        # 关于
        about_action = QAction("关于", self)
        about_action.setStatusTip("关于本应用")
        about_action.triggered.connect(self._on_about)
        toolbar.addAction(about_action)
        

    def _init_controller(self):
        """初始化控制器"""
        try:
            # 默认使用东方财富数据源
            self.controller = MainController("eastmoney")
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
        
        # 连接数据控制器信号
        self.signal_manager.data_refresh_started.connect(self._on_data_refresh_started)
        self.signal_manager.data_refreshed.connect(self._on_data_refresh_finished)

    def _refresh_data(self):
        """刷新数据"""
        if not self.controller:
            self.status_bar.showMessage("错误：控制器未初始化")
            return

        self.status_bar.showMessage("正在发起刷新请求...")
        
        # 注意：这里只负责发起请求，实际的UI更新由 _on_data_refresh_finished 处理
        result = self.controller.refresh_all_data()
        
        if not result.get("success"):
            error_msg = result.get("error", "未知错误")
            self.status_bar.showMessage(f"刷新启动失败: {error_msg}")
            QMessageBox.warning(self, "刷新失败", f"刷新启动失败: {error_msg}")
            self.setEnabled(True)

    def _on_data_refresh_started(self):
        """数据刷新开始"""
        self.status_bar.showMessage("正在获取最新数据...")
        self.setEnabled(False)  # 禁用界面
        # 通知 Dashbaord 进入加载状态
        self.dashboard_widget.set_loading_state(True)

    def _on_data_refresh_finished(self, result: dict):
        """数据刷新完成"""
        self.setEnabled(True)
        self.dashboard_widget.set_loading_state(False)
        
        success = result.get("success", False)
        message = result.get("message", "")
        
        if success:
            self.status_bar.showMessage(message)
            
            # 1. 立即获取最新的统计数据并更新 Dashboard
            statistics = self.controller.get_statistics()
            self.dashboard_widget.update_statistics(statistics)
            
            # 2. 重新应用当前的筛选器！这会更新 FundListWidget
            current_filters = self.filters_widget.get_filter_params()
            self._on_filter_changed(current_filters)
            
            # 3. 如果有选中的基金，更新其溢价率图表
            if self._selected_fund_code:
                self._update_spread_chart(self._selected_fund_code)
            
        else:
            self.status_bar.showMessage(f"刷新失败: {message}")
            QMessageBox.warning(self, "刷新失败", message)



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

            # 优化：刷新后不直接更新图表为所有数据（因为会只显示前5个）
            # 而是尝试自动选中第一只基金，或者保持当前选中
            # chart_data = self._prepare_chart_data(fund_data)
            # self.dashboard_widget.update_chart_data(chart_data)
            
            # 如果有数据，且当前没有显示特定的图表数据（或者想自动刷新当前选中的）
            if fund_data:
                # 这里简单处理：默认选中第一只，触发 _on_fund_selected 来更新图表
                # 实际应用中可能需要保持之前的选中状态，这里先默认选中第一个
                first_fund = fund_data[0]
                self._on_fund_selected(first_fund.get("code") or first_fund.get("fund_code"))

            # 发出数据刷新完成信号
            self.data_refreshed.emit(result)

        except Exception as e:
            logger.error(f"更新UI失败: {e}")

    def _on_refresh_data(self):
        """处理刷新数据动作"""
        self.refresh_requested.emit()

    def _prepare_chart_data(self, fund_data: list) -> list:
        """
        准备图表数据，转换数据格式以匹配ChartWidget要求

        Args:
            fund_data: 原始基金数据列表

        Returns:
            list: 转换后的图表数据
        """
        chart_data = []
        for fund in fund_data:
            # 转换字段名以匹配ChartWidget期望的格式
            chart_item = {
                "code": fund.get("fund_code") or fund.get("code", ""),
                "name": fund.get("name", ""),
                "timestamp": fund.get("timestamp", ""),
                "nav": fund.get("nav"),
                "price": fund.get("price"),
                "yield_pct": fund.get("yield_pct"),
                "spread_pct": fund.get("spread_pct"),
                "type": fund.get("type", ""),
                "volume": fund.get("volume"),
                "amount": fund.get("amount"),
            }
            # 移除None值
            chart_item = {k: v for k, v in chart_item.items() if v is not None}
            chart_data.append(chart_item)
        return chart_data

    def _on_export_data(self):
        """处理导出数据动作 - 支持选择保存位置、文件名和文件类型"""
        if not self.controller:
            QMessageBox.warning(self, "警告", "控制器未初始化")
            return

        try:
            from PyQt6.QtWidgets import QFileDialog
            from datetime import datetime
            
            # 默认文件名（带时间戳）
            default_name = f"基金套利数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 支持的文件类型
            file_filters = (
                "CSV 文件 (*.csv);;"
                "Excel 文件 (*.xlsx);;"
                "JSON 文件 (*.json);;"
                "所有文件 (*)"
            )
            
            # 打开文件保存对话框
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "导出数据",
                default_name,
                file_filters
            )
            
            if not file_path:
                # 用户取消了
                return
            
            # 根据选择的筛选器确定文件类型
            if 'xlsx' in selected_filter.lower():
                export_type = 'xlsx'
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
            elif 'json' in selected_filter.lower():
                export_type = 'json'
                if not file_path.endswith('.json'):
                    file_path += '.json'
            else:
                export_type = 'csv'
                if not file_path.endswith('.csv'):
                    file_path += '.csv'
            
            # 执行导出
            success = self._do_export(file_path, export_type)
            
            if success:
                self.status_bar.showMessage(f"数据已导出到: {file_path}")
                QMessageBox.information(self, "导出成功", f"数据已导出到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "数据导出失败，请检查日志")

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            QMessageBox.critical(self, "错误", f"导出数据失败: {e}")

    def _do_export(self, file_path: str, export_type: str) -> bool:
        """
        执行实际的导出操作
        
        Args:
            file_path: 文件路径
            export_type: 导出类型 (csv/xlsx/json)
            
        Returns:
            bool: 是否成功
        """
        try:

            # 获取当前 UI 显示的筛选后数据
            if hasattr(self, 'fund_list_widget') and hasattr(self.fund_list_widget, 'fund_data'):
                funds = self.fund_list_widget.fund_data
            else:
                funds = self.controller.get_all_funds()
            
            if not funds:
                QMessageBox.warning(self, "警告", "当前列表为空，无法导出")
                return False
            
            import pandas as pd
            df = pd.DataFrame(funds)
            
            # 重命名列为中文
            column_names = {
                'code': '基金代码',
                'name': '基金名称',
                'type': '类型',
                'nav': '净值',
                'price': '价格',
                'spread_pct': '价差%',
                'yield_pct': '收益率%',
                'is_opportunity': '有套利机会',
                'opportunity_level': '机会等级',
                'description': '描述',
                'volume': '成交量',
                'amount': '成交额',
                'timestamp': '时间戳',
            }
            df = df.rename(columns={k: v for k, v in column_names.items() if k in df.columns})
            
            # 根据类型导出
            if export_type == 'xlsx':
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif export_type == 'json':
                df.to_json(file_path, orient='records', force_ascii=False, indent=2)
            else:  # csv
                df.to_csv(file_path, index=False, encoding='utf-8-sig')  # utf-8-sig 以支持 Excel 打开
            
            logger.info(f"数据已导出到 {file_path}，共 {len(funds)} 条记录")
            return True
            
        except ImportError as e:
            if 'openpyxl' in str(e):
                QMessageBox.warning(self, "缺少依赖", "导出 Excel 需要安装 openpyxl：\npip install openpyxl")
            else:
                raise
            return False
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False

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

    @catch_exception(context="应用筛选条件")
    def _on_filter_changed(self, filter_params: dict):
        """处理筛选器变化"""
        if not self.controller:
            return

        # 应用筛选条件
        filtered_data = self.controller.apply_filters(filter_params)
        self.fund_list_widget.update_fund_data(filtered_data)

        # 更新统计信息（基于筛选条件）
        statistics = self.controller.get_statistics()
        self.dashboard_widget.update_statistics(statistics)

        # 更新图表数据
        chart_data = self._prepare_chart_data(filtered_data)
        self.dashboard_widget.update_chart_data(chart_data)

        self.status_bar.showMessage(f"已应用筛选条件，显示 {len(filtered_data)} 条记录")

    @catch_exception(context="处理基金选择")
    def _on_fund_selected(self, fund_code: str):
        """处理基金选择"""
        if not self.controller:
            return

        # 保存当前选中的基金代码
        self._selected_fund_code = fund_code
        
        # 更新图表
        self._update_spread_chart(fund_code)

    @catch_exception(context="更新溢价率图表")
    def _update_spread_chart(self, fund_code: str):
        """
        更新溢价率图表
        
        Args:
            fund_code: 基金代码
        """
        if not self.controller:
            return
            
        # 1. 获取基金基本信息
        all_data = self.controller.get_monitor_data()
        if not all_data:
            return
            
        selected_funds = [f for f in all_data if f["code"] == fund_code]
        if not selected_funds:
            return
        
        fund = selected_funds[0]

        # 2. 获取历史溢价率数据（2天）
        history_data = self.controller.get_price_history(fund_code, days=2)
        
        if history_data:
            # 历史数据已经包含 spread_pct，直接使用
            chart_data = []
            for item in history_data:
                chart_data.append({
                    "code": fund_code,
                    "name": fund.get("name", fund_code),
                    "timestamp": item.get("timestamp"),
                    "spread_pct": item.get("spread_pct"),
                })
            
            # 更新图表标题
            self.dashboard_widget.chart_widget.chart_title_label.setText(
                f"溢价率走势: {fund.get('name', fund_code)}"
            )
        else:
            # 没有历史数据，显示当前点
            chart_data = [{
                "code": fund_code,
                "name": fund.get("name", fund_code),
                "timestamp": fund.get("timestamp"),
                "spread_pct": fund.get("spread_pct", fund.get("premium_rate", 0)),
            }]
            self.dashboard_widget.chart_widget.chart_title_label.setText(
                f"溢价率: {fund.get('name', fund_code)} (暂无历史数据)"
            )
        
        # 3. 更新图表
        self.dashboard_widget.update_chart_data(chart_data)

        # 4. 更新状态栏
        spread = fund.get("spread_pct", fund.get("premium_rate", 0))
        info_text = f"选中: {fund.get('name')} ({fund_code}) | 当前溢价率: {spread:.2f}%"
        if len(chart_data) > 1:
            info_text += f" | 已加载 {len(chart_data)} 条历史记录 (近2天)"
        self.status_bar.showMessage(info_text)

    def _update_status(self):
        """更新状态栏"""
        if not self.controller:
            return

        try:
            # 计算自动刷新倒计时
            remaining_ms = self.auto_refresh_timer.remainingTime()
            if remaining_ms > 0:
                remaining_sec = remaining_ms // 1000
                minutes = remaining_sec // 60
                seconds = remaining_sec % 60
                countdown_text = f"自动刷新: {minutes:02d}:{seconds:02d}"
            else:
                countdown_text = "刷新中..."
            
            # 获取最后更新时间
            last_update = self.controller.get_last_update_time()
            if last_update:
                self.status_bar.showMessage(f"最后更新: {last_update} | {countdown_text}")
            else:
                self.status_bar.showMessage(f"等待首次刷新 | {countdown_text}")
        except Exception as e:
            logger.debug(f"更新状态失败: {e}")

    @catch_exception(context="自动刷新")
    def _on_auto_refresh(self):
        """自动刷新回调"""
        logger.info("执行自动刷新...")
        self._on_refresh_data()

    def _setup_shortcuts(self):
        """设置快捷键"""
        from PyQt6.QtGui import QShortcut

        # Ctrl+R: 刷新数据
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._on_refresh_data)

        # Ctrl+E: 导出数据
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self._on_export_data)

        # Ctrl+F: 聚焦搜索框
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._on_focus_search)

        # F5: 刷新数据
        f5_shortcut = QShortcut(QKeySequence("F5"), self)
        f5_shortcut.activated.connect(self._on_refresh_data)

        # Escape: 清除选择
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self._on_clear_selection)

        logger.info("快捷键已设置")

    def _on_focus_search(self):
        """聚焦到搜索框"""
        if hasattr(self.fund_list_widget, 'search_input'):
            self.fund_list_widget.search_input.setFocus()
            self.fund_list_widget.search_input.selectAll()
            self.status_bar.showMessage("搜索模式")

    def _on_clear_selection(self):
        """清除选择"""
        if hasattr(self.fund_list_widget, 'table_widget'):
            self.fund_list_widget.table_widget.clearSelection()
            self.status_bar.showMessage("已清除选择")



    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            if self.controller:
                self.controller.cleanup()
            logger.info("应用关闭")
        except Exception as e:
            logger.error(f"关闭应用时出错: {e}")

        event.accept()