"""
基金列表组件
"""

import logging
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QLineEdit, QPushButton,
    QMenu, QMessageBox, QApplication, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor, QBrush, QFont

logger = logging.getLogger(__name__)


class FundListWidget(QWidget):
    """基金列表组件"""

    # 信号定义
    fund_selected = pyqtSignal(str)  # 基金被选中（双击或选择）
    fund_double_clicked = pyqtSignal(str)  # 基金被双击
    context_menu_requested = pyqtSignal(str, str)  # 右键菜单请求（基金代码，动作）

    def __init__(self):
        super().__init__()
        self.fund_data: List[Dict[str, Any]] = []      # 当前显示的数据
        self.all_fund_data: List[Dict[str, Any]] = []  # 所有数据缓存
        self._init_ui()
        self._init_table()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 外层卡片容器
        card_frame = QFrame()
        card_frame.setObjectName("ListCard")
        inside_layout = QVBoxLayout(card_frame)
        inside_layout.setContentsMargins(0, 0, 0, 0)
        inside_layout.setSpacing(0)
        
        # 1. 搜索栏 (放在表格上方，或者作为卡片头部)
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 12, 15, 12)
        
        search_label = QLabel("基金列表")
        search_label.setObjectName("ChartTitle") 
        search_layout.addWidget(search_label)
        
        search_layout.addStretch()
        
        # 搜索框美化
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索代码或名称")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)
        
        inside_layout.addWidget(search_container)
        
        # 2. 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: #E8E8E8; border: none; min-height: 1px; max-height: 1px;")
        inside_layout.addWidget(line)
        
        # 3. 基金表格
        self.table_widget = QTableWidget()
        self.table_widget.setFrameShape(QFrame.Shape.NoFrame) # 去除表格自带边框
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        inside_layout.addWidget(self.table_widget)
        
        main_layout.addWidget(card_frame)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.verticalHeader().hide()
        self.table_widget.setSortingEnabled(False)  # 禁用前端自动排序，完全依赖后端排序
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._on_context_menu)
        self.table_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table_widget.itemSelectionChanged.connect(self._on_selection_changed)

        main_layout.addWidget(self.table_widget)

        # 状态栏
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.count_label = QLabel("总计: 0")
        status_layout.addWidget(self.count_label)

        main_layout.addWidget(status_container)

    def _init_table(self):
        """初始化表格"""
        columns = [
            ("index", "序号", 60),
            ("code", "代码", 110),     # 增加宽度
            ("name", "名称", 160),     # 设为互动调整，给一个合理初始值
            ("nav", "净值", 100),      # 增加宽度
            ("price", "价格", 100),    # 增加宽度
            ("spread_pct", "价差%", 120), # 增加宽度
        ]

        self.table_widget.setColumnCount(len(columns))
        for i, (key, header, width) in enumerate(columns):
            item = QTableWidgetItem(header)
            self.table_widget.setHorizontalHeaderItem(i, item)
            self.table_widget.setColumnWidth(i, width)

        # 设置表头
        header = self.table_widget.horizontalHeader()
        
        # 1. 允许用户自由调整所有列宽 (关键修改)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # 2. 允许用户拖动列顺序 (满足"易于操作")
        header.setSectionsMovable(True)
        
        # 3. 最后一列自动拉伸填充剩余空间 (防止右侧留白)
        header.setStretchLastSection(True)
        
        # 4. 设置最小列宽，防止误操作缩得太小
        header.setMinimumSectionSize(60)
        
        # 5. 增加表头高度和样式，使其更明显
        header.setDefaultSectionSize(40)
        header.setMinimumHeight(40)
        
        # 显式设置表头样式，增加边框和背景，使其看起来"可操作"
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #F5F7FA;
                color: #333333;
                padding: 4px;
                border: 1px solid #DCDCDC;
                border-bottom: 2px solid #C0C0C0;
                font-weight: bold;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background-color: #E6E8EB;
            }
        """)
        
        header.setSortIndicatorShown(False)

    def update_fund_data(self, fund_data: List[Dict[str, Any]]):
        """
        更新基金数据

        Args:
            fund_data: 基金数据列表
        """
        self.all_fund_data = fund_data
        # 自动应用当前筛选
        self._apply_filter()
        # 应用当前的搜索过滤
        self._apply_filter()

    def _populate_table(self):
        """填充表格数据"""
        self.table_widget.setSortingEnabled(False)  # 禁用排序以免干扰
        self.table_widget.setRowCount(len(self.fund_data))

        for row, fund in enumerate(self.fund_data):
            # 序号 (index: 0)
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 0, index_item)

            # 代码 (index: 1)
            code_val = fund.get("code")
            code_str = str(code_val) if code_val is not None else ""
            code_item = QTableWidgetItem(code_str)
            code_item.setData(Qt.ItemDataRole.UserRole, code_val)
            code_item.setToolTip(code_str)
            self.table_widget.setItem(row, 1, code_item)

            # 名称 (index: 2)
            name_val = fund.get("name")
            name_str = str(name_val) if name_val is not None else ""
            name_item = QTableWidgetItem(name_str)
            name_item.setToolTip(name_str)
            self.table_widget.setItem(row, 2, name_item)

            # 净值 (index: 3)
            nav = fund.get("nav")
            nav_str = f"{nav:.3f}" if nav is not None else "--"
            nav_item = QTableWidgetItem(nav_str)
            nav_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            nav_item.setToolTip(nav_str)
            self.table_widget.setItem(row, 3, nav_item)

            # 价格 (index: 4)
            price = fund.get("price")
            price_str = f"{price:.3f}" if price is not None else "--"
            price_item = QTableWidgetItem(price_str)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_item.setToolTip(price_str)
            self.table_widget.setItem(row, 4, price_item)

            # 价差% (index: 5)
            spread_pct = fund.get("spread_pct")
            spread_str = f"{spread_pct:.2f}%" if spread_pct is not None else "--"
            spread_item = QTableWidgetItem(spread_str)
            spread_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._colorize_spread_item(spread_item, spread_pct)
            spread_item.setToolTip(spread_str)
            self.table_widget.setItem(row, 5, spread_item)

    def _colorize_spread_item(self, item: QTableWidgetItem, spread_pct: float):
        """根据价差着色"""
        if spread_pct is None:
            return
        
        from src.ui.styles import Colors, Thresholds

        if spread_pct > Thresholds.SPREAD_HIGH_PREMIUM:
            item.setForeground(QBrush(QColor(Colors.PREMIUM_HIGH)))
        elif spread_pct > Thresholds.SPREAD_MEDIUM_PREMIUM:
            item.setForeground(QBrush(QColor(Colors.PREMIUM_MEDIUM)))
        elif spread_pct > 0:
            item.setForeground(QBrush(QColor(Colors.PREMIUM_LOW)))
        elif spread_pct < Thresholds.SPREAD_HIGH_DISCOUNT:
            item.setForeground(QBrush(QColor(Colors.DISCOUNT_HIGH)))
        elif spread_pct < Thresholds.SPREAD_MEDIUM_DISCOUNT:
            item.setForeground(QBrush(QColor(Colors.DISCOUNT_MEDIUM)))
        elif spread_pct < 0:
            item.setForeground(QBrush(QColor(Colors.DISCOUNT_LOW)))

    def _colorize_yield_item(self, item: QTableWidgetItem, yield_pct: float):
        """根据收益率着色"""
        # 已移除收益率列，保留方法以防未来恢复，或可删除
        pass

    def _colorize_opportunity_item(self, item: QTableWidgetItem, opportunity_level: str):
        """根据机会等级着色"""
        pass

    def _get_opportunity_level_text(self, level: str) -> str:
        """获取机会等级文本"""
        texts = {
            "excellent": "优秀",
            "good": "良好",
            "weak": "一般",
            "none": "无",
        }
        return texts.get(level, "未知")

    def _update_status(self):
        """更新状态"""
        from src.ui.styles import Colors
        
        total_count = len(self.fund_data)
        opportunity_count = sum(1 for f in self.fund_data if f.get("is_opportunity", False))

        self.count_label.setText(f"总计: {total_count} | 机会: {opportunity_count}")

        if opportunity_count > 0:
            self.status_label.setText(f"发现 {opportunity_count} 个套利机会")
            self.status_label.setStyleSheet(f"color: {Colors.PREMIUM_HIGH}; font-weight: bold;")
        else:
            self.status_label.setText("未发现套利机会")
            self.status_label.setStyleSheet(f"color: {Colors.NEUTRAL};")

    def _apply_filter(self):
        """应用筛选"""
        text = self.search_input.text().strip().lower()
        
        if not text:
            self.fund_data = self.all_fund_data
        else:
            filtered = []
            for fund in self.all_fund_data:
                code = str(fund.get("code", "")).lower()
                name = str(fund.get("name", "")).lower()
                if text in code or text in name:
                    filtered.append(fund)
            self.fund_data = filtered
            
        self._populate_table()
        self._update_status()

    def _on_search_text_changed(self, text: str):
        """处理搜索文本变化"""
        self._apply_filter()

    def _on_clear_search(self):
        """清空搜索"""
        self.search_input.clear()
        # textChanged 信号会触发筛选

    def _on_context_menu(self, position):
        """显示右键菜单"""
        item = self.table_widget.itemAt(position)
        if not item:
            return

        row = item.row()
        # 注意：代码现在是第1列 (index 1)
        fund_code_item = self.table_widget.item(row, 1)
        if not fund_code_item:
            return

        fund_code = fund_code_item.data(Qt.ItemDataRole.UserRole)
        # 名称是第2列 (index 2)
        fund_name_item = self.table_widget.item(row, 2)
        fund_name = fund_name_item.text() if fund_name_item else ""

        menu = QMenu(self)

        # 查看详情
        detail_action = QAction(f"查看详情: {fund_code}", self)
        detail_action.triggered.connect(lambda: self._on_view_detail(fund_code))
        menu.addAction(detail_action)

        # 加入观察列表
        watch_action = QAction("加入观察列表", self)
        watch_action.triggered.connect(lambda: self._on_add_to_watchlist(fund_code))
        menu.addAction(watch_action)

        menu.addSeparator()

        # 复制代码
        copy_code_action = QAction("复制基金代码", self)
        copy_code_action.triggered.connect(lambda: self._on_copy_code(fund_code))
        menu.addAction(copy_code_action)

        # 复制名称
        copy_name_action = QAction("复制基金名称", self)
        copy_name_action.triggered.connect(lambda: self._on_copy_name(fund_name))
        menu.addAction(copy_name_action)

        menu.exec(self.table_widget.viewport().mapToGlobal(position))

    def _on_view_detail(self, fund_code: str):
        """查看基金详情"""
        self.fund_selected.emit(fund_code)
        # TODO: 打开详情对话框

    def _on_add_to_watchlist(self, fund_code: str):
        """加入观察列表"""
        QMessageBox.information(self, "提示", f"已将 {fund_code} 加入观察列表")
        self.context_menu_requested.emit(fund_code, "add_to_watchlist")

    def _on_copy_code(self, fund_code: str):
        """复制基金代码"""
        clipboard = QApplication.clipboard()
        clipboard.setText(fund_code)
        self.status_label.setText(f"已复制基金代码: {fund_code}")

    def _on_copy_name(self, fund_name: str):
        """复制基金名称"""
        clipboard = QApplication.clipboard()
        clipboard.setText(fund_name)
        self.status_label.setText(f"已复制基金名称: {fund_name}")

    def _on_item_double_clicked(self, item):
        """处理双击事件"""
        row = item.row()
        # 代码在第1列
        fund_code_item = self.table_widget.item(row, 1)
        if fund_code_item:
            fund_code = fund_code_item.data(Qt.ItemDataRole.UserRole)
            self.fund_double_clicked.emit(fund_code)

    def _on_selection_changed(self):
        """处理选择变化"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        # 代码在第1列
        fund_code_item = self.table_widget.item(row, 1)
        if fund_code_item:
            fund_code = fund_code_item.data(Qt.ItemDataRole.UserRole)
            self.fund_selected.emit(fund_code)

    def clear_data(self):
        """清空数据"""
        self.fund_data = []
        self.table_widget.setRowCount(0)
        self.search_input.clear()
        self.status_label.setText("就绪")
        self.count_label.setText("总计: 0")

    def get_selected_fund_code(self) -> str:
        """获取选中的基金代码"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return ""

        row = selected_items[0].row()
        # 代码在第1列
        fund_code_item = self.table_widget.item(row, 1)
        if fund_code_item:
            return fund_code_item.data(Qt.ItemDataRole.UserRole)
        return ""

    def refresh_display(self):
        """刷新显示"""
        self._populate_table()
        self._update_status()