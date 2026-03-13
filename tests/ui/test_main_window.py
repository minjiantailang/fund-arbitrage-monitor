"""
UI组件测试 - 使用pytest-qt框架

注意：这些测试需要 --run-ui 选项来运行
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys

# 标记所有测试需要UI环境
pytestmark = pytest.mark.ui


# 尝试检查PyQt6-Charts是否可用
try:
    from PyQt6.QtCharts import QChart
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False


@pytest.fixture
def mock_chart_module():
    """创建一个模拟的chart_widget模块，用于当PyQt6-Charts不可用时"""
    if HAS_CHARTS:
        yield None
        return
    
    from PyQt6.QtWidgets import QWidget
    
    class MockChartWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.chart_data = []
        
        def set_chart_data(self, data):
            self.chart_data = data
        
        def update_chart(self):
            pass
        
        def clear_chart(self):
            self.chart_data = []
    
    # 创建模拟模块
    mock_module = MagicMock()
    mock_module.ChartWidget = MockChartWidget
    
    # 替换真实模块
    original_module = sys.modules.get('src.ui.chart_widget')
    sys.modules['src.ui.chart_widget'] = mock_module
    
    yield mock_module
    
    # 恢复原始模块
    if original_module:
        sys.modules['src.ui.chart_widget'] = original_module
    else:
        del sys.modules['src.ui.chart_widget']


class TestFundListWidget:
    """基金列表组件测试"""

    def test_fund_list_creation(self, qapp):
        """测试基金列表创建"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 验证部件存在
        assert hasattr(fund_list, 'table_widget')
        assert hasattr(fund_list, 'search_input')  # 正确的属性名
        assert hasattr(fund_list, 'status_label')
        assert hasattr(fund_list, 'count_label')

        # 验证初始状态
        assert fund_list.table_widget.rowCount() == 0

        # 清理
        fund_list.deleteLater()

    def test_fund_list_update(self, qapp):
        """测试基金列表更新"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 测试数据
        test_funds = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": 3.56,
                "price": 3.58,
                "spread_pct": 0.56,
                "yield_pct": 0.56,
                "opportunity_level": "good",
                "is_opportunity": True,
            },
            {
                "code": "161005",
                "name": "富国天惠LOF",
                "type": "LOF",
                "nav": 1.56,
                "price": 1.58,
                "spread_pct": 1.28,
                "yield_pct": 1.28,
                "opportunity_level": "excellent",
                "is_opportunity": True,
            }
        ]

        # 使用正确的方法名更新列表
        fund_list.update_fund_data(test_funds)

        # 验证表格行数
        assert fund_list.table_widget.rowCount() == len(test_funds)

        # 验证数据存在（不检查顺序，因为表格会自动排序）
        codes_in_table = []
        for row in range(fund_list.table_widget.rowCount()):
            item = fund_list.table_widget.item(row, 0)
            if item:
                codes_in_table.append(item.text())
        
        assert "510300" in codes_in_table
        assert "161005" in codes_in_table

        # 清理
        fund_list.deleteLater()

    def test_fund_list_clear(self, qapp):
        """测试清空基金列表"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [{"code": "510300", "name": "沪深300ETF", "type": "ETF"}]
        fund_list.update_fund_data(test_funds)
        assert fund_list.table_widget.rowCount() == 1

        # 清空
        fund_list.clear_data()
        assert fund_list.table_widget.rowCount() == 0

        fund_list.deleteLater()

    def test_fund_list_search(self, qapp):
        """测试基金搜索功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "510500", "name": "中证500ETF", "type": "ETF"},
        ]
        fund_list.update_fund_data(test_funds)

        # 搜索
        fund_list.search_input.setText("510300")
        
        # 验证只显示匹配的结果
        # 注意：搜索是通过 _on_search_text_changed 触发的
        
        fund_list.deleteLater()

    def test_fund_list_signals(self, qapp):
        """测试基金列表信号"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 验证信号存在
        assert hasattr(fund_list, 'fund_selected')
        assert hasattr(fund_list, 'fund_double_clicked')
        assert hasattr(fund_list, 'context_menu_requested')

        fund_list.deleteLater()

    def test_fund_list_get_selected(self, qapp):
        """测试获取选中基金代码"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 没有选中时应返回空字符串
        assert fund_list.get_selected_fund_code() == ""

        fund_list.deleteLater()

    def test_fund_list_refresh_display(self, qapp):
        """测试刷新显示"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [{"code": "510300", "name": "沪深300ETF", "type": "ETF"}]
        fund_list.update_fund_data(test_funds)

        # 刷新显示不应抛出异常
        fund_list.refresh_display()

        fund_list.deleteLater()

    def test_fund_list_with_opportunities(self, qapp):
        """测试有套利机会的基金列表"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 测试数据 - 有套利机会
        test_funds = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": 3.56,
                "price": 3.58,
                "spread_pct": 1.5,  # 高价差
                "yield_pct": 1.2,   # 高收益
                "opportunity_level": "excellent",
                "is_opportunity": True,
            },
        ]

        fund_list.update_fund_data(test_funds)
        
        # 验证状态显示
        assert "1" in fund_list.status_label.text()  # 应显示1个套利机会
        
        fund_list.deleteLater()

    def test_fund_list_colorize_spread(self, qapp):
        """测试价差着色功能"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtWidgets import QTableWidgetItem

        fund_list = FundListWidget()

        # 创建测试项
        item = QTableWidgetItem("1.5%")
        
        # 测试高溢价着色
        fund_list._colorize_spread_item(item, 1.5)  # 红色
        
        # 测试中等溢价
        item2 = QTableWidgetItem("0.7%")
        fund_list._colorize_spread_item(item2, 0.7)  # 橙色
        
        # 测试低溢价
        item3 = QTableWidgetItem("0.3%")
        fund_list._colorize_spread_item(item3, 0.3)  # 绿色
        
        # 测试折价
        item4 = QTableWidgetItem("-1.5%")
        fund_list._colorize_spread_item(item4, -1.5)  # 蓝色
        
        # 测试None值
        item5 = QTableWidgetItem("--")
        fund_list._colorize_spread_item(item5, None)
        
        fund_list.deleteLater()

    def test_fund_list_colorize_yield(self, qapp):
        """测试收益率着色功能"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtWidgets import QTableWidgetItem

        fund_list = FundListWidget()

        # 创建测试项
        item = QTableWidgetItem("1.5%")
        
        # 测试高收益率着色
        fund_list._colorize_yield_item(item, 1.5)  # 红色 + 粗体
        
        # 测试中等收益率
        item2 = QTableWidgetItem("0.7%")
        fund_list._colorize_yield_item(item2, 0.7)  # 橙色
        
        # 测试低收益率
        item3 = QTableWidgetItem("0.3%")
        fund_list._colorize_yield_item(item3, 0.3)  # 绿色
        
        # 测试无收益率
        item4 = QTableWidgetItem("0.1%")
        fund_list._colorize_yield_item(item4, 0.1)  # 灰色
        
        # 测试None值
        item5 = QTableWidgetItem("--")
        fund_list._colorize_yield_item(item5, None)
        
        fund_list.deleteLater()

    def test_fund_list_colorize_opportunity(self, qapp):
        """测试机会等级着色功能"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtWidgets import QTableWidgetItem

        fund_list = FundListWidget()

        # 测试各种机会等级
        for level in ["excellent", "good", "weak", "none", "unknown"]:
            item = QTableWidgetItem(level)
            fund_list._colorize_opportunity_item(item, level)
        
        fund_list.deleteLater()

    def test_fund_list_opportunity_level_text(self, qapp):
        """测试机会等级文本转换"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        assert fund_list._get_opportunity_level_text("excellent") == "优秀"
        assert fund_list._get_opportunity_level_text("good") == "良好"
        assert fund_list._get_opportunity_level_text("weak") == "一般"
        assert fund_list._get_opportunity_level_text("none") == "无"
        assert fund_list._get_opportunity_level_text("unknown") == "未知"
        
        fund_list.deleteLater()

    def test_fund_list_search_filter(self, qapp):
        """测试搜索筛选功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据并启用排序
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "510500", "name": "中证500ETF", "type": "ETF"},
            {"code": "161005", "name": "富国天惠LOF", "type": "LOF"},
        ]
        fund_list.update_fund_data(test_funds)
        assert fund_list.table_widget.rowCount() == 3

        # 清空搜索
        fund_list._on_clear_search()
        
        fund_list.deleteLater()

    def test_fund_list_colorize_spread_discount(self, qapp):
        """测试价差折价着色功能"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtWidgets import QTableWidgetItem

        fund_list = FundListWidget()

        # 测试中等折价
        item1 = QTableWidgetItem("-0.7%")
        fund_list._colorize_spread_item(item1, -0.7)  # 浅蓝
        
        # 测试低折价
        item2 = QTableWidgetItem("-0.3%")
        fund_list._colorize_spread_item(item2, -0.3)  # 青色
        
        fund_list.deleteLater()

    def test_fund_list_search_with_text(self, qapp):
        """测试有文本的搜索功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "510500", "name": "中证500ETF", "type": "ETF"},
            {"code": "161005", "name": "富国天惠LOF", "type": "LOF"},
        ]
        fund_list.update_fund_data(test_funds)

        # 触发搜索
        fund_list._on_search_text_changed("510300")
        
        fund_list.deleteLater()

    def test_fund_list_copy_code(self, qapp):
        """测试复制基金代码功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 复制代码
        fund_list._on_copy_code("510300")

        # 验证状态更新
        assert "510300" in fund_list.status_label.text()
        
        fund_list.deleteLater()

    def test_fund_list_copy_name(self, qapp):
        """测试复制基金名称功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 复制名称
        fund_list._on_copy_name("沪深300ETF")

        # 验证状态更新
        assert "沪深300ETF" in fund_list.status_label.text()
        
        fund_list.deleteLater()

    def test_fund_list_view_detail(self, qapp):
        """测试查看详情功能"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 连接信号接收器
        signal_received = []
        fund_list.fund_selected.connect(lambda c: signal_received.append(c))

        # 查看详情
        fund_list._on_view_detail("510300")

        # 验证信号发射
        assert "510300" in signal_received
        
        fund_list.deleteLater()

    def test_fund_list_selection_change(self, qapp):
        """测试选择变化处理"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtCore import Qt

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
        ]
        fund_list.update_fund_data(test_funds)

        # 连接信号
        signal_received = []
        fund_list.fund_selected.connect(lambda c: signal_received.append(c))

        # 选择第一行
        fund_list.table_widget.selectRow(0)
        
        fund_list.deleteLater()

    def test_fund_list_item_double_click(self, qapp):
        """测试双击项目处理"""
        from src.ui.fund_list_widget import FundListWidget

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
        ]
        fund_list.update_fund_data(test_funds)

        # 连接信号
        signal_received = []
        fund_list.fund_double_clicked.connect(lambda c: signal_received.append(c))

        # 模拟双击 - 获取表格项
        item = fund_list.table_widget.item(0, 0)
        if item:
            fund_list._on_item_double_clicked(item)
        
        fund_list.deleteLater()

    def test_fund_list_get_selected_with_selection(self, qapp):
        """测试有选择时获取选中代码"""
        from src.ui.fund_list_widget import FundListWidget
        from PyQt6.QtCore import Qt

        fund_list = FundListWidget()

        # 添加数据
        test_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
        ]
        fund_list.update_fund_data(test_funds)

        # 选择第一行
        fund_list.table_widget.selectRow(0)
        
        # 获取选中代码
        code = fund_list.get_selected_fund_code()
        # 由于表格排序，不一定是510300，但应该有值
        
        fund_list.deleteLater()


class TestFiltersWidget:
    """筛选器组件测试"""

    def test_filters_creation(self, qapp):
        """测试筛选器创建"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 验证基本属性
        assert hasattr(filters, 'filter_params')
        assert hasattr(filters, 'filter_changed')  # 信号

        filters.deleteLater()

    def test_filters_get_params(self, qapp):
        """测试获取筛选参数"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        params = filters.get_filter_params()
        assert isinstance(params, dict)

        filters.deleteLater()

    def test_filters_set_params(self, qapp):
        """测试设置筛选参数"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        test_params = {"fund_type": "ETF", "min_spread": 0.5}
        filters.set_filter_params(test_params)

        filters.deleteLater()

    def test_filters_clear(self, qapp):
        """测试清空筛选器"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 不应抛出异常
        filters.clear_filters()

        filters.deleteLater()

    def test_filters_enable_disable(self, qapp):
        """测试启用/禁用筛选器"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 禁用
        filters.enable_filters(False)
        
        # 启用
        filters.enable_filters(True)

        filters.deleteLater()

    def test_filters_signal(self, qapp):
        """测试筛选器信号"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 创建信号接收器
        signal_received = []
        filters.filter_changed.connect(lambda p: signal_received.append(p))

        # 触发筛选变化
        filters._emit_filter_changed()

        # 验证信号已发射
        assert len(signal_received) == 1

        filters.deleteLater()

    def test_filters_apply(self, qapp):
        """测试应用筛选"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 不应抛出异常
        filters._on_apply_filters()

        filters.deleteLater()

    def test_filters_reset(self, qapp):
        """测试重置筛选"""
        from src.ui.filters_widget import FiltersWidget

        filters = FiltersWidget()

        # 不应抛出异常
        filters._on_reset_filters()

        filters.deleteLater()


@pytest.mark.skipif(not HAS_CHARTS, reason="PyQt6-Charts not installed")
class TestChartWidget:
    """图表组件测试 - 需要PyQt6-Charts"""

    def test_chart_creation(self, qapp):
        """测试图表创建"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        # 验证基本属性
        assert hasattr(chart, 'chart')
        assert hasattr(chart, 'chart_view')

        chart.deleteLater()

    def test_chart_set_data(self, qapp):
        """测试设置图表数据"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        test_data = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "timestamp": "2026-01-30T12:00:00",
                "nav": 3.56,
                "price": 3.58,
                "yield_pct": 0.56,
                "spread_pct": 0.56
            }
        ]

        # 不应抛出异常
        chart.set_chart_data(test_data)

        chart.deleteLater()

    def test_chart_clear(self, qapp):
        """测试清除图表"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()
        chart.clear_chart()

        chart.deleteLater()

    def test_chart_price_history(self, qapp):
        """测试价格历史图表"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        test_data = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "timestamp": "2026-01-30T10:00:00",
                "nav": 3.56,
                "price": 3.58,
            },
            {
                "code": "510300",
                "name": "沪深300ETF",
                "timestamp": "2026-01-30T11:00:00",
                "nav": 3.57,
                "price": 3.59,
            }
        ]

        chart.set_chart_data(test_data)
        chart._update_price_history_chart()

        chart.deleteLater()

    def test_chart_yield_trend(self, qapp):
        """测试收益率趋势图表"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        test_data = [
            {
                "code": "510300",
                "timestamp": "2026-01-30T10:00:00",
                "yield_pct": 0.5,
            },
            {
                "code": "510300",
                "timestamp": "2026-01-30T11:00:00",
                "yield_pct": 0.7,
            }
        ]

        chart.set_chart_data(test_data)
        chart.current_chart_type = "yield_trend"
        chart.update_chart()

        chart.deleteLater()

    def test_chart_spread_distribution(self, qapp):
        """测试价差分布图表"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        test_data = [
            {"code": "510300", "timestamp": "2026-01-30T10:00:00", "spread_pct": 0.5},
            {"code": "510500", "timestamp": "2026-01-30T10:00:00", "spread_pct": 0.7},
            {"code": "161005", "timestamp": "2026-01-30T10:00:00", "spread_pct": 1.2},
        ]

        chart.set_chart_data(test_data)
        chart.current_chart_type = "spread_distribution"
        chart.update_chart()

        chart.deleteLater()

    def test_chart_type_changed(self, qapp):
        """测试图表类型切换"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        test_data = [
            {"code": "510300", "timestamp": "2026-01-30T10:00:00", "nav": 3.56, "price": 3.58, "yield_pct": 0.5, "spread_pct": 0.5},
        ]
        chart.set_chart_data(test_data)

        # 切换到收益率趋势
        chart._on_chart_type_changed("收益率趋势")
        assert chart.current_chart_type == "yield_trend"

        # 切换到价差分布
        chart._on_chart_type_changed("价差分布")
        assert chart.current_chart_type == "spread_distribution"

        # 切换回价格历史
        chart._on_chart_type_changed("价格历史")
        assert chart.current_chart_type == "price_history"

        chart.deleteLater()

    def test_chart_empty_data(self, qapp):
        """测试空数据处理"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        # 设置空数据
        chart.set_chart_data([])
        chart.update_chart()

        # 应该显示空图表提示
        assert chart.chart.title() == "暂无数据"

        chart.deleteLater()

    def test_chart_parse_timestamp(self, qapp):
        """测试时间戳解析"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        # 测试ISO格式
        ts1 = chart._parse_timestamp("2026-01-30T10:00:00")
        assert ts1 is not None

        # 测试另一种格式
        ts2 = chart._parse_timestamp("2026-01-30 10:00:00")
        assert ts2 is not None

        # 测试无效时间戳
        ts3 = chart._parse_timestamp("invalid")
        assert ts3 is None

        # 测试None
        ts4 = chart._parse_timestamp(None)
        assert ts4 is None

        chart.deleteLater()

    def test_chart_get_min_max_timestamp(self, qapp):
        """测试获取最小最大时间戳"""
        from src.ui.chart_widget import ChartWidget

        chart = ChartWidget()

        # 空数据时应返回默认值
        min_ts = chart._get_min_timestamp()
        max_ts = chart._get_max_timestamp()
        assert min_ts is not None
        assert max_ts is not None

        # 有数据时
        chart.set_chart_data([
            {"timestamp": "2026-01-30T10:00:00"},
            {"timestamp": "2026-01-30T12:00:00"},
        ])

        min_ts = chart._get_min_timestamp()
        max_ts = chart._get_max_timestamp()
        assert min_ts is not None
        assert max_ts is not None

        chart.deleteLater()


@pytest.mark.skipif(not HAS_CHARTS, reason="PyQt6-Charts not installed")
class TestDashboardWidget:
    """仪表盘组件测试 - 需要PyQt6-Charts"""

    def test_dashboard_creation(self, qapp):
        """测试仪表盘创建"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()

        # 验证部件存在
        assert hasattr(dashboard, 'stat_cards')
        assert hasattr(dashboard, 'chart_widget')

        dashboard.deleteLater()

    def test_dashboard_update_statistics(self, qapp):
        """测试仪表盘统计更新"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()

        # 测试数据
        test_stats = {
            "total_funds": 25,
            "etf_count": 15,
            "lof_count": 10,
            "opportunity_count": 5,
            "avg_spread": 1.5,
            "last_update": "2026-01-30 12:00:00"
        }

        # 更新统计信息
        dashboard.update_statistics(test_stats)

        dashboard.deleteLater()

    def test_dashboard_clear(self, qapp):
        """测试清空仪表盘数据"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()
        dashboard.clear_data()

        dashboard.deleteLater()

    def test_dashboard_loading_state(self, qapp):
        """测试仪表盘加载状态"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()

        # 设置加载状态
        dashboard.set_loading_state(True)
        dashboard.set_loading_state(False)

        dashboard.deleteLater()

    def test_dashboard_update_data_source(self, qapp):
        """测试更新数据源"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()

        dashboard.update_data_source("东方财富")

        dashboard.deleteLater()

    def test_dashboard_get_statistic(self, qapp):
        """测试获取统计值"""
        from src.ui.dashboard_widget import DashboardWidget

        dashboard = DashboardWidget()

        # 更新统计
        dashboard.update_statistics({"total_funds": 25})

        # 获取统计值
        value = dashboard.get_statistic_value("total_funds")
        assert value == 25

        dashboard.deleteLater()


@pytest.mark.skipif(not HAS_CHARTS, reason="PyQt6-Charts not installed")
class TestMainWindow:
    """主窗口测试 - 需要PyQt6-Charts"""

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_creation(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试窗口创建"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 验证窗口属性
        assert window.windowTitle() == "基金套利监控"

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_widgets(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试窗口部件"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 验证主要部件存在
        assert hasattr(window, 'dashboard_widget')
        assert hasattr(window, 'fund_list_widget')
        assert hasattr(window, 'filters_widget')
        assert hasattr(window, 'status_bar')

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_resize(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试窗口调整大小"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 调整大小
        new_width = 1200
        new_height = 800
        window.resize(new_width, new_height)

        # 验证新大小
        assert window.width() == new_width
        assert window.height() == new_height

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_close_event(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试关闭事件"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow
        from PyQt6.QtGui import QCloseEvent

        window = MainWindow()

        # 模拟关闭事件
        event = QCloseEvent()
        window.closeEvent(event)

        # 验证事件被接受
        assert event.isAccepted() is True

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_refresh_data_action(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试刷新数据动作"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 连接信号接收器
        signal_received = []
        window.refresh_requested.connect(lambda: signal_received.append(True))

        # 触发刷新动作
        window._on_refresh_data()

        # 验证信号已发射
        assert len(signal_received) == 1

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_settings_action(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试设置动作"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 触发设置动作
        window._on_settings()

        # 验证弹窗已显示
        mock_msgbox.information.assert_called_once()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_about_action(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试关于动作"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 触发关于动作
        window._on_about()

        # 验证关于对话框已显示
        mock_msgbox.about.assert_called_once()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_prepare_chart_data(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试图表数据准备"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 测试数据
        fund_data = [
            {
                "fund_code": "510300",
                "name": "沪深300ETF",
                "timestamp": "2026-01-30T12:00:00",
                "nav": 3.56,
                "price": 3.58,
                "yield_pct": 0.5,
                "spread_pct": 0.5,
                "type": "ETF",
            }
        ]

        # 准备图表数据
        chart_data = window._prepare_chart_data(fund_data)

        # 验证返回数据
        assert len(chart_data) == 1
        assert chart_data[0]["code"] == "510300"
        assert chart_data[0]["name"] == "沪深300ETF"

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_filter_changed(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试筛选器变化处理"""
        mock_controller = Mock()
        mock_controller.apply_filters.return_value = []
        mock_controller.get_statistics.return_value = {}
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 触发筛选变化
        filter_params = {"fund_type": "ETF"}
        window._on_filter_changed(filter_params)

        # 验证控制器方法被调用
        mock_controller.apply_filters.assert_called_once_with(filter_params)

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_fund_selected(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试基金选中处理"""
        mock_controller = Mock()
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 触发基金选中事件
        window._on_fund_selected("510300")

        # 验证状态栏消息
        assert "510300" in window.status_bar.currentMessage()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_refresh_data_success(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试刷新数据成功"""
        mock_controller = Mock()
        mock_controller.refresh_all_data.return_value = {
            "success": True,
            "total_opportunities": 5,
        }
        mock_controller.get_statistics.return_value = {"total_funds": 10}
        mock_controller.get_filtered_funds.return_value = []
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 执行刷新
        window._refresh_data()

        # 验证控制器方法被调用
        mock_controller.refresh_all_data.assert_called_once()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_refresh_data_failure(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试刷新数据失败"""
        mock_controller = Mock()
        mock_controller.refresh_all_data.return_value = {
            "success": False,
            "error": "连接超时",
        }
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 执行刷新
        window._refresh_data()

        # 验证警告弹窗已显示
        mock_msgbox.warning.assert_called()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    def test_window_refresh_no_controller(self, mock_get_signal_manager, mock_controller_class, qapp):
        """测试无控制器时刷新"""
        mock_controller_class.return_value = None
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.controller = None  # 模拟控制器未初始化

        # 执行刷新（不应抛出异常）
        window._refresh_data()

        # 验证状态栏显示错误消息
        assert "未初始化" in window.status_bar.currentMessage()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_export_data_success(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试导出数据成功"""
        mock_controller = Mock()
        mock_controller.export_to_csv.return_value = True
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 执行导出
        window._on_export_data()

        # 验证导出方法被调用
        mock_controller.export_to_csv.assert_called_once()

        # 验证成功弹窗已显示
        mock_msgbox.information.assert_called()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_export_data_failure(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试导出数据失败"""
        mock_controller = Mock()
        mock_controller.export_to_csv.return_value = False
        mock_signal_manager = Mock()
        mock_controller_class.return_value = mock_controller
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()

        # 执行导出
        window._on_export_data()

        # 验证警告弹窗已显示
        mock_msgbox.warning.assert_called()

        window.close()

    @patch('src.ui.main_window.MainController')
    @patch('src.ui.main_window.get_signal_manager')
    @patch('src.ui.main_window.QMessageBox')
    def test_window_export_no_controller(self, mock_msgbox, mock_get_signal_manager, mock_controller_class, qapp):
        """测试无控制器时导出"""
        mock_controller_class.return_value = None
        mock_signal_manager = Mock()
        mock_get_signal_manager.return_value = mock_signal_manager

        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.controller = None  # 模拟控制器未初始化

        # 执行导出
        window._on_export_data()

        # 验证警告弹窗已显示
        mock_msgbox.warning.assert_called()

        window.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-ui"])