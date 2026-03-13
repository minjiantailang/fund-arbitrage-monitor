"""
筛选器组件 - 紧凑型设计
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox, QPushButton,
    QDoubleSpinBox, QFrame, QSizePolicy
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
        """初始化UI - 紧凑布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 给筛选器一个容器背景，使其与表格区分
        container = QFrame()
        container.setObjectName("FilterContainer")
        # 移除硬编码样式，由 ThemeManager 统一管理
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 8, 10, 8)
        container_layout.setSpacing(15)

        # 1. 价差范围
        spread_layout = QHBoxLayout()
        spread_layout.setSpacing(5)
        spread_layout.addWidget(QLabel("价差(%):"))
        
        self.min_spread_spin = QDoubleSpinBox()
        self.min_spread_spin.setRange(-1000.0, 1000.0)
        self.min_spread_spin.setSingleStep(0.1)
        self.min_spread_spin.setDecimals(1)
        self.min_spread_spin.setFixedWidth(70)
        self.min_spread_spin.setValue(-100.0)
        self.min_spread_spin.valueChanged.connect(self._on_filter_changed)
        
        self.max_spread_spin = QDoubleSpinBox()
        self.max_spread_spin.setRange(-1000.0, 1000.0)
        self.max_spread_spin.setSingleStep(0.1)
        self.max_spread_spin.setDecimals(1)
        self.max_spread_spin.setFixedWidth(70)
        self.max_spread_spin.setValue(100.0)
        self.max_spread_spin.valueChanged.connect(self._on_filter_changed)
        
        spread_layout.addWidget(self.min_spread_spin)
        spread_layout.addWidget(QLabel("-"))
        spread_layout.addWidget(self.max_spread_spin)
        container_layout.addLayout(spread_layout)

        # 2. 排序
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(5)
        sort_layout.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.addItem("价差% (降序)", "spread_pct_desc")
        self.sort_combo.addItem("价差% (升序)", "spread_pct_asc")
        self.sort_combo.addItem("收益率% (降序)", "yield_pct_desc")
        self.sort_combo.addItem("代码 (升序)", "code_asc")
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        sort_layout.addWidget(self.sort_combo)
        container_layout.addLayout(sort_layout)
        
        # 3. 仅显示机会
        self.only_opportunities_check = QCheckBox("仅看有机会")
        self.only_opportunities_check.stateChanged.connect(self._on_filter_changed)
        container_layout.addWidget(self.only_opportunities_check)

        # 弹簧
        container_layout.addStretch()
        
        # 4. 操作按钮
        self.apply_button = QPushButton("立即筛选")
        self.apply_button.setFixedWidth(80)
        self.apply_button.clicked.connect(self._on_apply_filters)
        
        self.reset_button = QPushButton("重置")
        self.reset_button.setFixedWidth(60)
        self.reset_button.clicked.connect(self._on_reset_filters)
        
        container_layout.addWidget(self.apply_button)
        container_layout.addWidget(self.reset_button)
        
        main_layout.addWidget(container)
        
        # 使用固定高度
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _init_filters(self):
        """初始化筛选参数"""
        self.filter_params = {
            "fund_type": "all",  # 固定为全部
            "min_spread": -100.0,
            "max_spread": 100.0,
            "opportunity_levels": ["excellent", "good", "weak", "none"],  # 固定为全选
            "sort_by": "spread_pct_desc",
            "only_opportunities": False,
        }

    def _on_filter_changed(self):
        """处理筛选条件变化"""
        # 更新筛选参数
        self.filter_params.update({
            "min_spread": self.min_spread_spin.value(),
            "max_spread": self.max_spread_spin.value(),
            "sort_by": self.sort_combo.currentData(),
            "only_opportunities": self.only_opportunities_check.isChecked(),
        })

    def _on_apply_filters(self):
        """应用筛选"""
        self._emit_filter_changed()

    def _on_reset_filters(self):
        """重置筛选"""
        # 重置UI控件
        self.min_spread_spin.setValue(-100.0)
        self.max_spread_spin.setValue(100.0)
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
        """获取当前筛选参数"""
        return self.filter_params.copy()

    def set_filter_params(self, params: Dict[str, Any]):
        """设置筛选参数"""
        self.filter_params.update(params)

        # 更新UI控件
        if "min_spread" in params:
            self.min_spread_spin.setValue(params["min_spread"])

        if "max_spread" in params:
            self.max_spread_spin.setValue(params["max_spread"])

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
        """启用/禁用筛选器"""
        self.min_spread_spin.setEnabled(enabled)
        self.max_spread_spin.setEnabled(enabled)
        self.sort_combo.setEnabled(enabled)
        self.only_opportunities_check.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)