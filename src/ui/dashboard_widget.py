"""
仪表盘组件
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """仪表盘组件"""

    # 信号定义
    statistic_clicked = pyqtSignal(str)  # 统计项被点击

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._init_data()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 标题
        title_label = QLabel("套利机会监控仪表盘")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 统计卡片区域
        self.stats_container = QWidget()
        stats_layout = QGridLayout(self.stats_container)
        stats_layout.setSpacing(10)

        # 创建统计卡片
        self.stat_cards = {}
        stat_configs = [
            ("total_funds", "总基金数", "只", "#4CAF50"),
            ("etf_count", "ETF基金", "只", "#2196F3"),
            ("lof_count", "LOF基金", "只", "#FF9800"),
            ("opportunity_count", "套利机会", "个", "#F44336"),
            ("avg_spread", "平均价差", "%", "#9C27B0"),
            ("max_spread", "最大价差", "%", "#FF5722"),
        ]

        for i, (key, title, unit, color) in enumerate(stat_configs):
            row = i // 3
            col = i % 3
            card = self._create_stat_card(key, title, unit, color)
            self.stat_cards[key] = card
            stats_layout.addWidget(card, row, col)

        main_layout.addWidget(self.stats_container)

        # 关键机会区域
        main_layout.addWidget(self._create_section_label("关键套利机会"))

        self.key_opportunities_container = QWidget()
        key_opp_layout = QVBoxLayout(self.key_opportunities_container)
        key_opp_layout.setContentsMargins(0, 0, 0, 0)

        # 关键机会列表（占位符）
        self.key_opportunities_label = QLabel("暂无关键套利机会")
        self.key_opportunities_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_opportunities_label.setStyleSheet("color: #757575; font-style: italic;")
        key_opp_layout.addWidget(self.key_opportunities_label)

        main_layout.addWidget(self.key_opportunities_container)

        # 底部状态区域
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 最后更新时间
        self.last_update_label = QLabel("最后更新: --")
        self.last_update_label.setStyleSheet("color: #616161; font-size: 12px;")
        bottom_layout.addWidget(self.last_update_label)

        bottom_layout.addStretch()

        # 数据源状态
        self.data_source_label = QLabel("数据源: 模拟数据")
        self.data_source_label.setStyleSheet("color: #616161; font-size: 12px;")
        bottom_layout.addWidget(self.data_source_label)

        main_layout.addWidget(bottom_container)

    def _create_stat_card(self, key: str, title: str, unit: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }}
            QFrame:hover {{
                border: 2px solid {color};
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(5)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)

        # 数值
        value_label = QLabel("--")
        value_label.setObjectName(f"value_{key}")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)

        # 单位
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #757575; font-size: 12px;")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(unit_label)

        # 点击事件
        def on_card_clicked():
            self.statistic_clicked.emit(key)

        card.mousePressEvent = lambda e: on_card_clicked()

        return card

    def _create_section_label(self, text: str) -> QLabel:
        """创建分区标签"""
        label = QLabel(text)
        label_font = QFont()
        label_font.setPointSize(14)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet("color: #424242; margin-top: 10px; margin-bottom: 5px;")
        return label

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

        # 更新统计卡片
        for key, card in self.stat_cards.items():
            if key in statistics:
                value = statistics[key]
                if isinstance(value, float):
                    display_value = f"{value:.2f}"
                else:
                    display_value = str(value)

                # 查找并更新数值标签
                value_label = card.findChild(QLabel, f"value_{key}")
                if value_label:
                    value_label.setText(display_value)

        # 更新最后更新时间
        last_update = statistics.get("last_update")
        if last_update:
            self.last_update_label.setText(f"最后更新: {last_update}")

        # 更新关键机会
        self._update_key_opportunities()

    def _update_key_opportunities(self):
        """更新关键机会显示"""
        opportunity_count = self.statistics.get("opportunity_count", 0)

        if opportunity_count > 0:
            # TODO: 从控制器获取真实的关键机会数据
            self.key_opportunities_label.setText(
                f"发现 {opportunity_count} 个套利机会，请查看右侧基金列表"
            )
            self.key_opportunities_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.key_opportunities_label.setText("暂无关键套利机会")
            self.key_opportunities_label.setStyleSheet("color: #757575; font-style: italic;")

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