"""
筛选器组件
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QSlider, QCheckBox, QPushButton,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)


class FiltersWidget(QWidget):
    """筛选器组件"""

    # 信号定义
    filter_changed = pyqtSignal(dict)  # 筛选条件变化

    def __init__(self):
        super().__init__()
        self.filter_params: Dict[str, Any] = {}
        self._init_ui()
        self._init_filters()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 标题
        title_label = QLabel("基金筛选器")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #424242;")
        main_layout.addWidget(title_label)

        # 基金类型筛选
        type_group = QGroupBox("基金类型")
        type_layout = QHBoxLayout(type_group)

        self.type_combo = QComboBox()
        self.type_combo.addItem("全部", "all")
        self.type_combo.addItem("ETF", "ETF")
        self.type_combo.addItem("LOF", "LOF")
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        type_layout.addWidget(self.type_combo)

        main_layout.addWidget(type_group)

        # 价差范围筛选
        spread_group = QGroupBox("价差范围 (%)")
        spread_layout = QVBoxLayout(spread_group)

        # 最小价差
        min_spread_layout = QHBoxLayout()
        min_spread_layout.addWidget(QLabel("最小:"))

        self.min_spread_spin = QDoubleSpinBox()
        self.min_spread_spin.setRange(-20.0, 20.0)
        self.min_spread_spin.setSingleStep(0.1)
        self.min_spread_spin.setValue(-5.0)
        self.min_spread_spin.valueChanged.connect(self._on_filter_changed)
        min_spread_layout.addWidget(self.min_spread_spin)

        min_spread_layout.addWidget(QLabel("%"))
        spread_layout.addLayout(min_spread_layout)

        # 最大价差
        max_spread_layout = QHBoxLayout()
        max_spread_layout.addWidget(QLabel("最大:"))

        self.max_spread_spin = QDoubleSpinBox()
        self.max_spread_spin.setRange(-20.0, 20.0)
        self.max_spread_spin.setSingleStep(0.1)
        self.max_spread_spin.setValue(5.0)
        self.max_spread_spin.valueChanged.connect(self._on_filter_changed)
        max_spread_layout.addWidget(self.max_spread_spin)

        max_spread_layout.addWidget(QLabel("%"))
        spread_layout.addLayout(max_spread_layout)

        main_layout.addWidget(spread_group)

        # 机会等级筛选
        opportunity_group = QGroupBox("机会等级")
        opportunity_layout = QVBoxLayout(opportunity_group)

        self.opportunity_checkboxes = {}
        opportunities = [
            ("excellent", "优秀机会", True),
            ("good", "良好机会", True),
            ("weak", "一般机会", True),
            ("none", "无机会", False),
        ]

        for key, text, default in opportunities:
            checkbox = QCheckBox(text)
            checkbox.setChecked(default)
            checkbox.stateChanged.connect(self._on_filter_changed)
            opportunity_layout.addWidget(checkbox)
            self.opportunity_checkboxes[key] = checkbox

        main_layout.addWidget(opportunity_group)

        # 排序选项
        sort_group = QGroupBox("排序")
        sort_layout = QVBoxLayout(sort_group)

        sort_criteria_layout = QHBoxLayout()
        sort_criteria_layout.addWidget(QLabel("排序依据:"))

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("价差% (降序)", "spread_pct_desc")
        self.sort_combo.addItem("价差% (升序)", "spread_pct_asc")
        self.sort_combo.addItem("收益率% (降序)", "yield_pct_desc")
        self.sort_combo.addItem("收益率% (升序)", "yield_pct_asc")
        self.sort_combo.addItem("基金代码", "code_asc")
        self.sort_combo.addItem("基金名称", "name_asc")
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        sort_criteria_layout.addWidget(self.sort_combo)

        sort_layout.addLayout(sort_criteria_layout)

        # 只显示机会
        self.only_opportunities_check = QCheckBox("只显示套利机会")
        self.only_opportunities_check.stateChanged.connect(self._on_filter_changed)
        sort_layout.addWidget(self.only_opportunities_check)

        main_layout.addWidget(sort_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.apply_button = QPushButton("应用筛选")
        self.apply_button.clicked.connect(self._on_apply_filters)
        button_layout.addWidget(self.apply_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self._on_reset_filters)
        button_layout.addWidget(self.reset_button)

        main_layout.addLayout(button_layout)

        main_layout.addStretch()

    def _init_filters(self):
        """初始化筛选参数"""
        self.filter_params = {
            "fund_type": "all",
            "min_spread": -5.0,
            "max_spread": 5.0,
            "opportunity_levels": ["excellent", "good", "weak"],
            "sort_by": "spread_pct_desc",
            "only_opportunities": False,
        }

    def _on_filter_changed(self):
        """处理筛选条件变化"""
        # 更新筛选参数
        self.filter_params.update({
            "fund_type": self.type_combo.currentData(),
            "min_spread": self.min_spread_spin.value(),
            "max_spread": self.max_spread_spin.value(),
            "opportunity_levels": [
                key for key, checkbox in self.opportunity_checkboxes.items()
                if checkbox.isChecked()
            ],
            "sort_by": self.sort_combo.currentData(),
            "only_opportunities": self.only_opportunities_check.isChecked(),
        })

        # 自动应用筛选（可以改为手动应用）
        # self._emit_filter_changed()

    def _on_apply_filters(self):
        """应用筛选"""
        self._emit_filter_changed()

    def _on_reset_filters(self):
        """重置筛选"""
        # 重置UI控件
        self.type_combo.setCurrentIndex(0)  # 全部
        self.min_spread_spin.setValue(-5.0)
        self.max_spread_spin.setValue(5.0)

        for key, checkbox in self.opportunity_checkboxes.items():
            default_checked = key != "none"
            checkbox.setChecked(default_checked)

        self.sort_combo.setCurrentIndex(0)  # 价差%降序
        self.only_opportunities_check.setChecked(False)

        # 重置筛选参数
        self._init_filters()

        # 发出重置信号
        self._emit_filter_changed()

    def _emit_filter_changed(self):
        """发出筛选变化信号"""
        logger.debug(f"筛选条件变化: {self.filter_params}")
        self.filter_changed.emit(self.filter_params.copy())

    def get_filter_params(self) -> Dict[str, Any]:
        """
        获取当前筛选参数

        Returns:
            Dict: 筛选参数
        """
        return self.filter_params.copy()

    def set_filter_params(self, params: Dict[str, Any]):
        """
        设置筛选参数

        Args:
            params: 筛选参数
        """
        self.filter_params.update(params)

        # 更新UI控件
        if "fund_type" in params:
            index = self.type_combo.findData(params["fund_type"])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        if "min_spread" in params:
            self.min_spread_spin.setValue(params["min_spread"])

        if "max_spread" in params:
            self.max_spread_spin.setValue(params["max_spread"])

        if "opportunity_levels" in params:
            for key, checkbox in self.opportunity_checkboxes.items():
                checkbox.setChecked(key in params["opportunity_levels"])

        if "sort_by" in params:
            index = self.sort_combo.findData(params["sort_by"])
            if index >= 0:
                self.sort_combo.setCurrentIndex(index)

        if "only_opportunities" in params:
            self.only_opportunities_check.setChecked(params["only_opportunities"])

    def clear_filters(self):
        """清空筛选器"""
        self._on_reset_filters()

    def enable_filters(self, enabled: bool):
        """
        启用/禁用筛选器

        Args:
            enabled: 是否启用
        """
        self.type_combo.setEnabled(enabled)
        self.min_spread_spin.setEnabled(enabled)
        self.max_spread_spin.setEnabled(enabled)

        for checkbox in self.opportunity_checkboxes.values():
            checkbox.setEnabled(enabled)

        self.sort_combo.setEnabled(enabled)
        self.only_opportunities_check.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)