"""
UI 样式工具类 - 统一管理界面样式常量和工具函数
"""
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class Colors:
    """颜色常量"""
    # 主色系
    PRIMARY = "#1890FF"
    PRIMARY_HOVER = "#40A9FF"
    PRIMARY_PRESSED = "#096DD9"
    
    # 语义色
    SUCCESS = "#52C41A"
    WARNING = "#FAAD14"
    ERROR = "#FF4D4F"
    INFO = "#1890FF"
    
    # 中性色
    BACKGROUND = "#F0F2F5"
    CARD_BG = "#FFFFFF"
    BORDER = "#E8E8E8"
    BORDER_LIGHT = "#F0F0F0"
    
    # 文字色
    TEXT_PRIMARY = "#262626"
    TEXT_SECONDARY = "#595959"
    TEXT_TERTIARY = "#8C8C8C"
    TEXT_DISABLED = "#BFBFBF"
    
    # 特殊
    SELECTION_BG = "#E6F7FF"
    HOVER_BG = "#F5F5F5"
    
    # 表格数据着色（统一管理）
    PREMIUM_HIGH = "#F44336"      # 红色 - 高溢价/高收益
    PREMIUM_MEDIUM = "#FF9800"    # 橙色 - 中等溢价
    PREMIUM_LOW = "#4CAF50"       # 绿色 - 低溢价
    DISCOUNT_HIGH = "#2196F3"     # 蓝色 - 高折价
    DISCOUNT_MEDIUM = "#03A9F4"   # 浅蓝 - 中等折价
    DISCOUNT_LOW = "#00BCD4"      # 青色 - 低折价
    NEUTRAL = "#757575"           # 灰色 - 无/中性


@dataclass(frozen=True)
class Thresholds:
    """业务阈值常量 - 消除魔法数字"""
    # 价格有效性判断
    PRICE_INVALID_MIN = 0.001         # 低于此值视为无效价格
    PRICE_PLACEHOLDER = 1.0           # 占位符价格
    PRICE_PLACEHOLDER_TOLERANCE = 0.001  # 占位符价格容差
    
    # 溢价率阈值
    SPREAD_HIGH_PREMIUM = 1.0         # 高溢价阈值
    SPREAD_MEDIUM_PREMIUM = 0.5       # 中等溢价阈值
    SPREAD_HIGH_DISCOUNT = -1.0       # 高折价阈值
    SPREAD_MEDIUM_DISCOUNT = -0.5     # 中等折价阈值
    
    # 收益率阈值
    YIELD_HIGH = 1.0                  # 高收益阈值
    YIELD_MEDIUM = 0.5                # 中等收益阈值
    YIELD_LOW = 0.2                   # 低收益阈值
    
    # 筛选默认值
    DEFAULT_MIN_SPREAD = -100.0
    DEFAULT_MAX_SPREAD = 100.0

@dataclass(frozen=True)
class Fonts:
    """字体常量"""
    FAMILY = '-apple-system, "SF Pro Text", "Helvetica Neue", "Microsoft YaHei", "PingFang SC", sans-serif'
    FAMILY_MONO = '"SF Mono", "Monaco", "Consolas", "Liberation Mono", monospace'
    
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_BASE = 13
    SIZE_LG = 16
    SIZE_XL = 20
    SIZE_2XL = 24

@dataclass(frozen=True)
class Spacing:
    """间距常量"""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32

class StyleUtils:
    """样式工具函数"""
    
    @staticmethod
    def card_style(object_name: str = None) -> str:
        """生成卡片样式"""
        selector = f"QFrame#{object_name}" if object_name else "QFrame"
        return f"""
            {selector} {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """
    
    @staticmethod
    def button_primary_style() -> str:
        """生成主要按钮样式"""
        return f"""
            QPushButton[primary="true"] {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                color: #FFFFFF;
            }}
            QPushButton[primary="true"]:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton[primary="true"]:pressed {{
                background-color: {Colors.PRIMARY_PRESSED};
                border-color: {Colors.PRIMARY_PRESSED};
            }}
        """
    
    @staticmethod
    def input_style() -> str:
        """生成输入框样式"""
        return f"""
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {Colors.CARD_BG};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def table_style() -> str:
        """生成表格样式"""
        return f"""
            QTableWidget {{
                background-color: {Colors.CARD_BG};
                gridline-color: {Colors.BORDER_LIGHT};
                border: none;
                selection-background-color: {Colors.SELECTION_BG};
                selection-color: {Colors.PRIMARY};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
            QHeaderView::section {{
                background-color: #FAFAFA;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                padding: 8px;
                font-weight: 600;
            }}
        """
    
    @staticmethod
    def stat_value_style() -> str:
        """统计数值样式"""
        return f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.SIZE_2XL}px;
            font-weight: bold;
        """
    
    @staticmethod
    def stat_label_style() -> str:
        """统计标签样式"""
        return f"""
            color: {Colors.TEXT_TERTIARY};
            font-size: {Fonts.SIZE_SM}px;
        """

    @staticmethod
    def get_opportunity_color(level: str) -> str:
        """根据机会等级返回对应颜色"""
        color_map = {
            "excellent": Colors.SUCCESS,
            "good": Colors.PRIMARY,
            "weak": Colors.WARNING,
            "none": Colors.TEXT_TERTIARY,
        }
        return color_map.get(level, Colors.TEXT_TERTIARY)
    
    @staticmethod
    def get_spread_color(spread_pct: float) -> str:
        """根据溢价率返回颜色"""
        if spread_pct > 2.0:
            return Colors.ERROR
        elif spread_pct > 0.5:
            return Colors.WARNING
        elif spread_pct < -2.0:
            return Colors.SUCCESS
        elif spread_pct < -0.5:
            return Colors.INFO
        else:
            return Colors.TEXT_PRIMARY
