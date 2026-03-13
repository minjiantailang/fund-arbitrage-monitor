"""
仪表盘组件
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from .chart_widget import ChartWidget

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """仪表盘组件"""

    # 信号定义
    statistic_clicked = pyqtSignal(str)  # 统计项被点击

    def __init__(self):
        super().__init__()
        self.chart_widget: Optional[ChartWidget] = None
        self._init_ui()
        self._init_data()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # 1. 统计概览卡片 (顶部区域)
        stats_frame = QFrame()
        stats_frame.setObjectName("DashboardCard")
        # 移除默认背景色，使用 stylesheet 中的设置
        
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 15, 20, 20)
        stats_layout.setSpacing(15)
        
        # 统计标题和元数据
        header_layout = QHBoxLayout()
        title_label = QLabel("实时概览")
        title_label.setObjectName("ChartTitle")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 元数据（更新时间和源）
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(2)
        meta_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.last_update_label = QLabel("更新于: --")
        self.last_update_label.setObjectName("StatLabel")
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.data_source_label = QLabel("数据源: --")
        self.data_source_label.setObjectName("StatLabel")
        self.data_source_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        meta_layout.addWidget(self.last_update_label)
        meta_layout.addWidget(self.data_source_label)
        
        header_layout.addLayout(meta_layout)
        stats_layout.addLayout(header_layout)
        
        # 统计网格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        self.stat_cards = {}
        # 简化统计项配置
        stat_configs = [
            ("total_funds", "监控基金", "只"),
            ("opportunity_count", "套利机会", "个"),
            ("avg_spread", "平均溢价", "%"),
            ("max_spread", "最大溢价", "%"),
        ]
        
        for i, (key, title, unit) in enumerate(stat_configs):
            widget = self._create_stat_item(key, title, unit)
            grid_layout.addWidget(widget, i // 4, i % 4) # 一行4个
            
        stats_layout.addLayout(grid_layout)
        main_layout.addWidget(stats_frame)

        # 2. 图表卡片 (主要区域)
        chart_frame = QFrame()
        chart_frame.setObjectName("ChartCard")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(1, 1, 1, 1) # 图表本身有边距
        
        self.chart_widget = ChartWidget()
        chart_layout.addWidget(self.chart_widget)
        
        main_layout.addWidget(chart_frame, 1) # 让图表区域自适应伸缩
        
        # 3. 加载遮罩
        self.loading_overlay = QLabel(self)
        self.loading_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_overlay.setStyleSheet("background-color: rgba(255, 255, 255, 180); color: #333; font-weight: bold;")
        self.loading_overlay.setText("加载中...")
        self.loading_overlay.hide()

    def _create_stat_item(self, key, title, unit):
        """创建单个统计项 (无边框样式)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("StatLabel")
        
        # 值容器
        value_container = QHBoxLayout()
        value_container.setSpacing(4)
        value_container.setContentsMargins(0, 0, 0, 0)
        
        value_label = QLabel("0")
        value_label.setObjectName("StatValue")
        
        unit_label = QLabel(unit)
        unit_label.setObjectName("StatLabel")
        
        value_container.addWidget(value_label)
        value_container.addWidget(unit_label, 0, Qt.AlignmentFlag.AlignBottom) # 单位底部对齐
        value_container.addStretch()
        
        layout.addWidget(title_label)
        layout.addLayout(value_container)
        
        # 保存引用以便后续更新
        self.stat_cards[key] = {
            "value_label": value_label,
            # 兼容旧代码结构，虽然这里不再是特定的 Card 类
            "widget": widget 
        }
        return widget
        
    def _create_stat_card(self, key, title, unit, color):
         # 兼容旧代码调用 (如果还有其他地方调用)
         return self._create_stat_item(key, title, unit)
         
    def _create_section_label(self, text):
        # 兼容旧代码
        return QLabel(text)

    def _init_data(self):
        """初始化数据"""
        self.statistics = {
            "total_funds": 0,
            "etf_count": 0,
            "lof_count": 0,
            "opportunity_count": 0,
            "avg_spread": 0.0,
            "max_spread": 0.0,
            "min_spread": 0.0,
            "last_update": None,
        }

        self.key_opportunities = []

    def update_statistics(self, statistics: Dict[str, Any]):
        """
        更新统计信息

        Args:
            statistics: 统计信息字典
        """
        self.statistics.update(statistics)

        # 更新统计卡片 (新结构: stat_cards[key] = {"value_label": QLabel, "widget": QWidget})
        for key, card_info in self.stat_cards.items():
            if key in statistics:
                value = statistics[key]
                if isinstance(value, float):
                    display_value = f"{value:.2f}"
                else:
                    display_value = str(value)

                # 直接使用存储的 value_label 引用
                value_label = card_info.get("value_label")
                if value_label:
                    value_label.setText(display_value)

        # 更新最后更新时间
        last_update = statistics.get("last_update")
        if last_update:
            self.last_update_label.setText(f"更新于: {last_update}")

    def _update_key_opportunities(self):
        """更新关键机会显示 (已移除关键机会区域，此方法保留空实现以兼容)"""
        pass

    def update_data_source(self, source_name: str):
        """
        更新数据源显示

        Args:
            source_name: 数据源名称
        """
        self.data_source_label.setText(f"数据源: {source_name}")

    def clear_data(self):
        """清空数据"""
        self._init_data()

        # 重置所有卡片
        for card in self.stat_cards.values():
            value_label = card.findChild(QLabel, card.objectName().replace("card_", "value_"))
            if value_label:
                value_label.setText("--")

        self.key_opportunities_label.setText("暂无关键套利机会")
        self.key_opportunities_label.setStyleSheet("color: #757575; font-style: italic;")
        self.last_update_label.setText("最后更新: --")

    def get_statistic_value(self, key: str) -> Any:
        """
        获取统计值

        Args:
            key: 统计键

        Returns:
            Any: 统计值
        """
        return self.statistics.get(key)

    def set_loading_state(self, loading: bool):
        """
        设置加载状态

        Args:
            loading: 是否正在加载
        """
        if loading:
            self.setEnabled(False)
            self.last_update_label.setText("正在更新数据...")
        else:
            self.setEnabled(True)

    def update_chart_data(self, chart_data: list):
        """
        更新图表数据

        Args:
            chart_data: 图表数据列表，格式应符合ChartWidget要求
        """
        if self.chart_widget:
            self.chart_widget.set_chart_data(chart_data)

    def update_data_source(self, source_name: str):
        """更新数据源显示"""
        display_name = "东方财富 (实时)" if source_name == "eastmoney" else "模拟数据"
        self.data_source_label.setText(f"数据源: {display_name}")