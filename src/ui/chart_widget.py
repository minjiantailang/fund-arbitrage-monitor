"""
图表组件 - 显示基金价格和套利机会图表
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QPainter, QPen, QColor

from .theme_manager import get_theme_manager

logger = logging.getLogger(__name__)


class ChartWidget(QWidget):
    """图表组件"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.chart_data: List[Dict[str, Any]] = []

        self._init_ui()
        self._setup_chart()
        
        # 连接主题管理器
        self.theme_manager = get_theme_manager()
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        # 初始化当前主题
        self._on_theme_changed(self.theme_manager.current_theme)

    def _on_theme_changed(self, theme_name: str):
        """处理主题变化"""
        if theme_name == "dark":
            self.chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        else:
            self.chart.setTheme(QChart.ChartTheme.ChartThemeLight)
            
        self._apply_theme_styles()
        
        # 重新绘制现有数据
        if self.chart_data:
            self.update_chart()

    def _apply_theme_styles(self):
        """应用当前主题样式到图表元素"""
        current_theme = self.theme_manager.current_theme
        is_dark = current_theme == "dark"
        
        if is_dark:
            bg_color = QColor("#1F1F1F")
            text_color = QColor("#A6A6A6")
            grid_color = QColor("#303030")
            title_style = "color: #FFFFFF; font-weight: bold; font-size: 14px;"
            legend_color = QColor("#A6A6A6")
        else:
            bg_color = QColor("#FFFFFF")
            text_color = QColor("#595959")
            grid_color = QColor("#E8E8E8")
            title_style = "color: #262626; font-weight: bold; font-size: 14px;"
            legend_color = QColor("#595959")
            
        # 应用背景
        self.chart.setBackgroundBrush(bg_color)
        self.chart_view.setBackgroundBrush(bg_color)
        
        # 应用标题样式
        self.chart_title_label.setStyleSheet(title_style)
        
        # 应用图例颜色
        self.chart.legend().setLabelColor(legend_color)
        
        # 应用坐标轴样式
        for axis in self.chart.axes():
            axis.setLabelsColor(text_color)
            axis.setGridLineColor(grid_color)
            axis.setLinePenColor(grid_color)
            axis.setTitleBrush(text_color)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)

        # 图表类型标签（简化为单一类型）
        control_layout = QHBoxLayout()
        self.chart_title_label = QLabel("分时走势")
        self.chart_title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        control_layout.addWidget(self.chart_title_label)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # 图表视图
        self.chart = QChart()
        # self.chart.setTitle("基金数据图表") # 移除内部标题，节省空间
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # 优化布局：图例放到底部
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart.legend().setBackgroundVisible(False)
        
        # 极致空间利用：左右边距为0，底部留出空间给坐标轴
        from PyQt6.QtCore import QMargins
        # 底部留 25px 给 X 轴标签，右侧留 10px 缓冲
        self.chart.setMargins(QMargins(0, 5, 10, 25))
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundRoundness(0)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 使用更紧凑的布局
        main_layout.addWidget(self.chart_view, 1) 
        main_layout.setContentsMargins(0, 0, 0, 0) # 容器也无边距
        
    def _setup_chart(self, use_datetime_x=True):
        """设置图表坐标轴"""
        # Y轴是通用的
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("价格")
        self.axis_y.setLabelFormat("%.2f")
        self.axis_y.setTickCount(8)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        if use_datetime_x:
            self.axis_x = QDateTimeAxis()
            self.axis_x.setTitleText("时间")
            self.axis_x.setFormat("MM-dd HH:mm")
            self.axis_x.setTickCount(6)
            self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        else:
            self.axis_x = QValueAxis()
            self.axis_x.setTitleText("基金序号")
            self.axis_x.setLabelFormat("%d")
            self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)

    def set_chart_data(self, data: List[Dict[str, Any]]):
        """设置图表数据

        Args:
            data: 图表数据列表，每个元素应包含：
                - code: 基金代码
                - name: 基金名称
                - timestamp: 时间戳 (ISO格式)
                - spread_pct: 溢价率百分比
        """
        self.chart_data = data
        self.update_chart()

    def update_chart(self):
        """更新图表"""
        # 1. 清除现有系列
        self.chart.removeAllSeries()
        
        # 2. 清除旧坐标轴并按需创建
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        
        self._setup_chart(use_datetime_x=True)

        if not self.chart_data:
            self._show_empty_chart()
            return

        # 显示溢价率走势
        self._update_spread_trend_chart()
        
        # 更新 X 轴范围
        self.axis_x.setRange(self._get_min_timestamp(), self._get_max_timestamp())
        
        # 最后应用主题样式 (因为重新创建了轴)
        self._apply_theme_styles()

    def _show_empty_chart(self):
        """显示空图表"""
        self.chart.setTitle("暂无历史数据")
        self.axis_y.setTitleText("溢价率 (%)")
        self.axis_y.setRange(-5, 5)

        # 设置默认时间范围（最近3天）
        now = QDateTime.currentDateTime()
        days_ago = now.addDays(-3)
        self.axis_x.setRange(days_ago, now)

    def _update_spread_trend_chart(self):
        """更新溢价率走势图表"""
        self.chart.setTitle("")  # 标题已在外部 label 显示

        # 按基金代码分组数据
        funds_data = {}
        for item in self.chart_data:
            code = item.get("code") or item.get("fund_code")
            if code not in funds_data:
                funds_data[code] = {
                    "name": item.get("name", code),
                    "points": []  # (timestamp, spread_pct)
                }

            timestamp = self._parse_timestamp(item.get("timestamp"))
            spread_pct = item.get("spread_pct")
            
            if timestamp and spread_pct is not None:
                funds_data[code]["points"].append((timestamp, float(spread_pct)))

        # 添加数据点
        all_y_values = []
        
        # 预定义颜色
        colors = [
            QColor(0, 120, 215),   # 蓝色
            QColor(216, 59, 1),    # 橙红
            QColor(16, 124, 16),   # 绿色
            QColor(180, 0, 158),   # 紫色
            QColor(0, 153, 153)    # 青色
        ]
        
        visible_count = 0
        for code, data in funds_data.items():
            if not data["points"]:
                continue
                
            # 按时间排序
            data["points"].sort(key=lambda x: x[0].toMSecsSinceEpoch())
            
            # 创建溢价率系列
            series = QLineSeries()
            series.setName(f"{data['name']}")
            color = colors[visible_count % len(colors)]
            series.setPen(QPen(color, 2, Qt.PenStyle.SolidLine))
            
            for timestamp, spread in data["points"]:
                series.append(timestamp.toMSecsSinceEpoch(), spread)
                all_y_values.append(spread)
            
            self.chart.addSeries(series)
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)
            visible_count += 1

        # 添加零轴参考线（区分溢价和折价）
        if all_y_values:
            zero_line = QLineSeries()
            zero_line.setName("零轴")
            zero_line.setPen(QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine))
            
            min_time = self._get_min_timestamp()
            max_time = self._get_max_timestamp()
            zero_line.append(min_time.toMSecsSinceEpoch(), 0)
            zero_line.append(max_time.toMSecsSinceEpoch(), 0)
            
            self.chart.addSeries(zero_line)
            zero_line.attachAxis(self.axis_x)
            zero_line.attachAxis(self.axis_y)

        # 更新Y轴范围
        if all_y_values:
            min_val = min(all_y_values)
            max_val = max(all_y_values)
            # 确保零轴在视图中
            min_val = min(min_val, -1)
            max_val = max(max_val, 1)
            padding = max((max_val - min_val) * 0.1, 0.5)
            self.axis_y.setRange(min_val - padding, max_val + padding)
            self.axis_y.setTitleText("溢价率 (%)")

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[QDateTime]:
        """解析时间戳字符串为QDateTime"""
        if not timestamp_str:
            return None

        try:
            # 尝试ISO格式
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        except (ValueError, AttributeError):
            try:
                # 尝试其他格式
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            except ValueError:
                logger.warning(f"无法解析时间戳: {timestamp_str}")
                return None

    def _get_min_timestamp(self) -> QDateTime:
        """获取最小时间戳"""
        timestamps = []
        for item in self.chart_data:
            dt = self._parse_timestamp(item.get("timestamp"))
            if dt:
                timestamps.append(dt)

        if timestamps:
            return min(timestamps)
        else:
            # 默认返回一周前
            return QDateTime.currentDateTime().addDays(-7)

    def _get_max_timestamp(self) -> QDateTime:
        """获取最大时间戳"""
        timestamps = []
        for item in self.chart_data:
            dt = self._parse_timestamp(item.get("timestamp"))
            if dt:
                timestamps.append(dt)

        if timestamps:
            return max(timestamps)
        else:
            # 默认返回当前时间
            return QDateTime.currentDateTime()

    def clear_chart(self):
        """清除图表数据"""
        self.chart_data = []
        self.update_chart()

    def get_chart_image(self) -> Optional[bytes]:
        """获取图表图像（用于导出）"""
        try:
            # 保存图表为图像
            import io
            from PyQt6.QtGui import QImage

            image = QImage(self.chart_view.size(), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)

            painter = QPainter(image)
            self.chart_view.render(painter)
            painter.end()

            # 转换为字节
            byte_array = io.BytesIO()
            image.save(byte_array, "PNG")
            return byte_array.getvalue()

        except Exception as e:
            logger.error(f"获取图表图像失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 创建测试数据
    test_data = [
        {
            "code": "510300",
            "name": "沪深300ETF",
            "timestamp": "2026-01-30T10:00:00",
            "nav": 3.56,
            "price": 3.58,
            "yield_pct": 0.43,
            "spread_pct": 0.56
        },
        {
            "code": "510300",
            "name": "沪深300ETF",
            "timestamp": "2026-01-30T11:00:00",
            "nav": 3.57,
            "price": 3.59,
            "yield_pct": 0.45,
            "spread_pct": 0.56
        },
        {
            "code": "161005",
            "name": "富国天惠LOF",
            "timestamp": "2026-01-30T10:00:00",
            "nav": 1.56,
            "price": 1.58,
            "yield_pct": 1.28,
            "spread_pct": 1.28
        }
    ]

    window = ChartWidget()
    window.set_chart_data(test_data)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())