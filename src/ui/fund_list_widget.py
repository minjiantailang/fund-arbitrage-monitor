"""
基金列表组件
"""

import logging
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QLineEdit, QPushButton,
    QMenu, QMessageBox, QApplication
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
        self.fund_data: List[Dict[str, Any]] = []
        self._init_ui()
        self._init_table()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 搜索栏
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入基金代码或名称...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self._on_clear_search)
        search_layout.addWidget(clear_button)

        main_layout.addWidget(search_container)

        # 基金表格
        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
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
            ("code", "代码", 80),
            ("name", "名称", 150),
            ("type", "类型", 60),
            ("nav", "净值", 80),
            ("price", "价格", 80),
            ("spread_pct", "价差%", 80),
            ("yield_pct", "收益率%", 80),
            ("opportunity_level", "机会等级", 100),
            ("description", "描述", 200),
        ]

        self.table_widget.setColumnCount(len(columns))
        for i, (key, header, width) in enumerate(columns):
            item = QTableWidgetItem(header)
            self.table_widget.setHorizontalHeaderItem(i, item)
            self.table_widget.setColumnWidth(i, width)

        # 设置表头可拉伸
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(len(columns) - 1, QHeaderView.ResizeMode.Stretch)

    def update_fund_data(self, fund_data: List[Dict[str, Any]]):
        """
        更新基金数据

        Args:
            fund_data: 基金数据列表
        """
        self.fund_data = fund_data
        self._populate_table()
        self._update_status()

    def _populate_table(self):
        """填充表格数据"""
        self.table_widget.setSortingEnabled(False)  # 禁用排序以免干扰
        self.table_widget.setRowCount(len(self.fund_data))

        for row, fund in enumerate(self.fund_data):
            # 代码
            code_item = QTableWidgetItem(fund.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, fund.get("code"))
            self.table_widget.setItem(row, 0, code_item)

            # 名称
            name_item = QTableWidgetItem(fund.get("name", ""))
            self.table_widget.setItem(row, 1, name_item)

            # 类型
            type_item = QTableWidgetItem(fund.get("type", ""))
            self.table_widget.setItem(row, 2, type_item)

            # 净值
            nav = fund.get("nav")
            nav_item = QTableWidgetItem(f"{nav:.3f}" if nav is not None else "--")
            nav_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(row, 3, nav_item)

            # 价格
            price = fund.get("price")
            price_item = QTableWidgetItem(f"{price:.3f}" if price is not None else "--")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(row, 4, price_item)

            # 价差%
            spread_pct = fund.get("spread_pct")
            spread_item = QTableWidgetItem(f"{spread_pct:.2f}%" if spread_pct is not None else "--")
            spread_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._colorize_spread_item(spread_item, spread_pct)
            self.table_widget.setItem(row, 5, spread_item)

            # 收益率%
            yield_pct = fund.get("yield_pct")
            yield_item = QTableWidgetItem(f"{yield_pct:.2f}%" if yield_pct is not None else "--")
            yield_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._colorize_yield_item(yield_item, yield_pct)
            self.table_widget.setItem(row, 6, yield_item)

            # 机会等级
            opportunity_level = fund.get("opportunity_level", "")
            level_item = QTableWidgetItem(self._get_opportunity_level_text(opportunity_level))
            self._colorize_opportunity_item(level_item, opportunity_level)
            self.table_widget.setItem(row, 7, level_item)

            # 描述
            description = fund.get("description", "")
            desc_item = QTableWidgetItem(description)
            self.table_widget.setItem(row, 8, desc_item)

        self.table_widget.setSortingEnabled(True)  # 重新启用排序
        self.table_widget.sortByColumn(5, Qt.SortOrder.DescendingOrder)  # 默认按价差降序排序

    def _colorize_spread_item(self, item: QTableWidgetItem, spread_pct: float):
        """根据价差着色"""
        if spread_pct is None:
            return

        if spread_pct > 1.0:
            item.setForeground(QBrush(QColor("#F44336")))  # 红色 - 高溢价
        elif spread_pct > 0.5:
            item.setForeground(QBrush(QColor("#FF9800")))  # 橙色 - 中等溢价
        elif spread_pct > 0:
            item.setForeground(QBrush(QColor("#4CAF50")))  # 绿色 - 低溢价
        elif spread_pct < -1.0:
            item.setForeground(QBrush(QColor("#2196F3")))  # 蓝色 - 高折价
        elif spread_pct < -0.5:
            item.setForeground(QBrush(QColor("#03A9F4")))  # 浅蓝 - 中等折价
        elif spread_pct < 0:
            item.setForeground(QBrush(QColor("#00BCD4")))  # 青色 - 低折价

    def _colorize_yield_item(self, item: QTableWidgetItem, yield_pct: float):
        """根据收益率着色"""
        if yield_pct is None:
            return

        if yield_pct > 1.0:
            item.setForeground(QBrush(QColor("#F44336")))  # 红色 - 高收益
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        elif yield_pct > 0.5:
            item.setForeground(QBrush(QColor("#FF9800")))  # 橙色 - 中等收益
        elif yield_pct > 0.2:
            item.setForeground(QBrush(QColor("#4CAF50")))  # 绿色 - 低收益
        else:
            item.setForeground(QBrush(QColor("#757575")))  # 灰色 - 无收益

    def _colorize_opportunity_item(self, item: QTableWidgetItem, opportunity_level: str):
        """根据机会等级着色"""
        colors = {
            "excellent": "#F44336",  # 红色 - 优秀
            "good": "#FF9800",       # 橙色 - 良好
            "weak": "#4CAF50",       # 绿色 - 一般
            "none": "#757575",       # 灰色 - 无
        }

        color = colors.get(opportunity_level, "#757575")
        item.setForeground(QBrush(QColor(color)))

        if opportunity_level in ["excellent", "good"]:
            font = QFont()
            font.setBold(True)
            item.setFont(font)

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
        total_count = len(self.fund_data)
        opportunity_count = sum(1 for f in self.fund_data if f.get("is_opportunity", False))

        self.count_label.setText(f"总计: {total_count} | 机会: {opportunity_count}")

        if opportunity_count > 0:
            self.status_label.setText(f"发现 {opportunity_count} 个套利机会")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.status_label.setText("未发现套利机会")
            self.status_label.setStyleSheet("color: #757575;")

    def _on_search_text_changed(self, text: str):
        """处理搜索文本变化"""
        if not text.strip():
            self._populate_table()
            return

        search_text = text.strip().lower()
        filtered_data = []

        for fund in self.fund_data:
            code = fund.get("code", "").lower()
            name = fund.get("name", "").lower()

            if search_text in code or search_text in name:
                filtered_data.append(fund)

        # 临时显示筛选结果
        self._display_filtered_data(filtered_data)

    def _display_filtered_data(self, filtered_data: List[Dict[str, Any]]):
        """显示筛选后的数据"""
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(len(filtered_data))

        for row, fund in enumerate(filtered_data):
            for col in range(self.table_widget.columnCount()):
                original_row = self.fund_data.index(fund)
                item = self.table_widget.item(original_row, col).clone()
                self.table_widget.setItem(row, col, item)

        self.table_widget.setSortingEnabled(True)
        self.count_label.setText(f"筛选: {len(filtered_data)} / {len(self.fund_data)}")

    def _on_clear_search(self):
        """清空搜索"""
        self.search_input.clear()
        self._populate_table()

    def _on_context_menu(self, position):
        """显示右键菜单"""
        item = self.table_widget.itemAt(position)
        if not item:
            return

        row = item.row()
        fund_code_item = self.table_widget.item(row, 0)
        if not fund_code_item:
            return

        fund_code = fund_code_item.data(Qt.ItemDataRole.UserRole)
        fund_name_item = self.table_widget.item(row, 1)
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
        fund_code_item = self.table_widget.item(row, 0)
        if fund_code_item:
            fund_code = fund_code_item.data(Qt.ItemDataRole.UserRole)
            self.fund_double_clicked.emit(fund_code)

    def _on_selection_changed(self):
        """处理选择变化"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        fund_code_item = self.table_widget.item(row, 0)
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
        fund_code_item = self.table_widget.item(row, 0)
        if fund_code_item:
            return fund_code_item.data(Qt.ItemDataRole.UserRole)
        return ""

    def refresh_display(self):
        """刷新显示"""
        self._populate_table()
        self._update_status()