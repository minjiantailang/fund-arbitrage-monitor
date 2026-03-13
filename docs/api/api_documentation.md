# 基金套利监控应用 - API文档

## 概述

本文档描述基金套利监控应用的内部API接口和架构。本文档面向开发者，用于理解应用内部结构、扩展功能或进行二次开发。

### 技术栈
- **语言**：Python 3.9+
- **GUI框架**：PyQt6
- **数据库**：SQLite3
- **数据处理**：Pandas
- **HTTP客户端**：Requests
- **图表库**：PyQtChart

### 架构模式
应用采用MVC（Model-View-Controller）架构：
- **Model**：数据模型层，处理业务逻辑和数据存储
- **View**：视图层，用户界面组件
- **Controller**：控制层，协调模型和视图的交互

---

## 模块结构

### 包结构
```
src/
├── __init__.py
├── main.py                    # 应用主入口
├── models/                    # 数据模型层
│   ├── __init__.py
│   ├── database.py           # 数据库管理
│   ├── arbitrage_calculator.py # 套利计算器
│   ├── data_fetcher.py       # 数据获取器
│   └── fund_manager.py       # 基金管理器
├── ui/                       # 用户界面层
│   ├── __init__.py
│   ├── main_window.py        # 主窗口
│   ├── dashboard_widget.py   # 仪表盘组件
│   ├── fund_list_widget.py   # 基金列表组件
│   ├── filters_widget.py     # 筛选器组件
│   └── chart_widget.py       # 图表组件
└── controllers/              # 控制层
    ├── __init__.py
    ├── main_controller.py    # 主控制器
    ├── data_controller.py    # 数据控制器
    └── signal_manager.py     # 信号管理器
```

### 数据流
```
数据源 → DataFetcher → FundManager → Database
                                    ↓
Controller ← SignalManager → UI Components
```

---

## 数据模型层 (models/)

### Database 类

#### 概述
管理SQLite数据库连接和操作，提供线程安全的数据库访问。

#### 类定义
```python
class Database:
    """数据库管理类（单例模式）"""
```

#### 主要方法

##### `get_instance() -> Database`
获取数据库单例实例。

##### `_get_connection() -> sqlite3.Connection`
获取数据库连接（线程安全）。

##### `initialize_database() -> bool`
初始化数据库表结构。

**表结构**：
- `funds`：基金基本信息
- `fund_prices`：基金价格历史
- `arbitrage_opportunities`：套利机会记录

##### `save_fund_data(fund_data_list: List[Dict[str, Any]]) -> bool`
批量保存基金数据。

**参数**：
- `fund_data_list`：基金数据列表，每个元素包含：
  ```python
  {
      "code": "510300",           # 基金代码
      "name": "沪深300ETF",       # 基金名称
      "type": "ETF",              # 基金类型
      "nav": 3.56,                # 净值
      "price": 3.58,              # 市场价格
      "spread_pct": 0.56,         # 价差百分比
      "yield_pct": 0.43,          # 收益率百分比
      "timestamp": "2026-01-30T10:00:00"  # 时间戳
  }
  ```

##### `get_latest_prices(fund_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]`
获取最新价格数据。

**参数**：
- `fund_codes`：基金代码列表，None表示获取所有基金

**返回**：
```python
[
    {
        "fund_code": "510300",
        "name": "沪深300ETF",
        "type": "ETF",
        "nav": 3.56,
        "price": 3.58,
        "spread_pct": 0.56,
        "yield_pct": 0.43,
        "timestamp": "2026-01-30T10:00:00",
        "volume": 1000000,
        "amount": 3580000.0
    }
]
```

##### `get_price_history(fund_code: str, days: int = 30) -> List[Dict[str, Any]]`
获取价格历史数据。

##### `get_arbitrage_opportunities(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]`
获取套利机会记录。

##### `get_statistics() -> Dict[str, Any]`
获取统计信息。

##### `clean_old_data(days: int = 30) -> bool`
清理旧数据。

### ArbitrageCalculator 类

#### 概述
计算ETF和LOF基金的套利机会，考虑交易费用。

#### 类定义
```python
class ArbitrageCalculator:
    """套利计算器"""
```

#### 费用配置
```python
DEFAULT_FEES = {
    "ETF": {
        "commission": Decimal("0.0003"),  # 佣金 0.03%
        "stamp_tax": Decimal("0.001"),    # 印花税 0.1%
        "total": Decimal("0.0013")        # 总费用 0.13%
    },
    "LOF": {
        "subscription": Decimal("0.015"), # 申购费 1.5%
        "redemption": Decimal("0.005"),   # 赎回费 0.5%
        "total": Decimal("0.02")          # 总费用 2.0%
    }
}
```

#### 主要方法

##### `calculate_etf_arbitrage(nav: Decimal, price: Decimal, fund_code: str) -> Dict[str, Any]`
计算ETF套利机会。

**参数**：
- `nav`：净值
- `price`：市场价格
- `fund_code`：基金代码

**返回**：
```python
{
    "fund_code": "510300",
    "opportunity_type": "ETF",
    "opportunity_level": "premium",  # premium/discount/none/weak
    "is_opportunity": True,
    "nav": 3.56,
    "price": 3.58,
    "spread": 0.02,
    "spread_pct": 0.56,
    "net_yield_pct": 0.43,
    "fee_rate": 0.13,
    "description": "ETF溢价套利机会"
}
```

##### `calculate_lof_arbitrage(nav: Decimal, price: Decimal, fund_code: str) -> Dict[str, Any]`
计算LOF套利机会。

##### `calculate_batch_arbitrage(fund_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
批量计算套利机会。

##### `get_arbitrage_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]`
获取套利摘要统计。

### DataFetcher 类

#### 概述
抽象基类，定义数据获取接口。

#### 类定义
```python
class DataFetcher(ABC):
    """数据获取器抽象基类"""
```

#### 具体实现

##### `MockDataFetcher`
模拟数据获取器，用于开发和测试。

**方法**：
- `fetch_fund_data() -> List[Dict[str, Any]]`：生成模拟基金数据
- `fetch_single_fund(fund_code: str) -> Dict[str, Any]`：获取单个基金数据

##### `EastMoneyDataFetcher`
东方财富API数据获取器（待实现）。

### FundManager 类

#### 概述
基金管理器，协调数据获取、计算和存储。

#### 类定义
```python
class FundManager:
    """基金管理器（单例模式）"""
```

#### 主要方法

##### `refresh_all_data() -> Dict[str, Any]`
刷新所有基金数据。

**流程**：
1. 从数据源获取数据
2. 计算套利机会
3. 保存到数据库
4. 返回结果

##### `refresh_fund_data(fund_codes: List[str]) -> Dict[str, Any]`
刷新指定基金数据。

##### `get_latest_prices(fund_codes: Optional[List[str]] = None) -> List[Dict[str, Any]]`
获取最新价格数据（带套利计算结果）。

##### `get_price_history(fund_code: str, days: int = 30) -> List[Dict[str, Any]]`
获取价格历史数据。

##### `get_statistics() -> Dict[str, Any]`
获取统计信息。

---

## 控制层 (controllers/)

### MainController 类

#### 概述
主控制器，协调整个应用的工作流。

#### 类定义
```python
class MainController:
    """主控制器"""
```

#### 主要方法

##### `refresh_all_data() -> Dict[str, Any]`
刷新所有数据。

##### `get_statistics() -> Dict[str, Any]`
获取统计信息。

##### `get_all_funds() -> List[Dict[str, Any]]`
获取所有基金数据。

##### `get_filtered_funds(filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`
获取筛选后的基金数据。

##### `apply_filters(filter_params: Dict[str, Any]) -> List[Dict[str, Any]]`
应用筛选条件。

##### `export_to_csv(file_path: str) -> bool`
导出数据到CSV。

### DataController 类

#### 概述
数据控制器，管理数据刷新和业务逻辑。

#### 类定义
```python
class DataController(QObject):
    """数据控制器"""
```

#### 信号定义
```python
class DataRefreshWorker(QThread):
    refresh_complete = pyqtSignal(dict)    # 刷新完成
    refresh_progress = pyqtSignal(int, str) # 刷新进度
    refresh_error = pyqtSignal(str)        # 刷新错误
```

#### 主要方法

##### `refresh_all_data_async()`
异步刷新所有数据。

##### `refresh_selected_funds_async(fund_codes: List[str]) -> bool`
异步刷新指定基金。

##### `get_all_funds() -> List[Dict[str, Any]]`
获取所有基金数据。

##### `get_filtered_funds(filter_params: Dict[str, Any]) -> List[Dict[str, Any]]`
获取筛选后的基金数据。

##### `get_statistics() -> Dict[str, Any]`
获取统计信息。

### SignalManager 类

#### 概述
信号管理器，集中管理应用内的信号通信。

#### 类定义
```python
class SignalManager(QObject):
    """信号管理器（单例模式）"""
```

#### 信号定义
```python
# 数据相关信号
data_refresh_started = pyqtSignal()
data_refresh_complete = pyqtSignal(dict)
data_refresh_error = pyqtSignal(str)

# UI相关信号
filter_applied = pyqtSignal(dict)
fund_selected = pyqtSignal(str)

# 状态相关信号
status_message_changed = pyqtSignal(str)
data_source_changed = pyqtSignal(str)
```

---

## 用户界面层 (ui/)

### MainWindow 类

#### 概述
主窗口类，管理应用主界面。

#### 类定义
```python
class MainWindow(QMainWindow):
    """主窗口"""
```

#### 信号定义
```python
data_refreshed = pyqtSignal(dict)    # 数据刷新完成
refresh_requested = pyqtSignal()     # 刷新请求
```

#### 主要方法

##### `_init_ui()`
初始化用户界面。

**布局结构**：
- 工具栏：操作按钮
- 分割器：左侧仪表盘（70%），右侧筛选器和列表（30%）
- 状态栏：状态信息

##### `_init_controller()`
初始化控制器。

##### `_connect_signals()`
连接信号。

##### `_update_ui_after_refresh(result: dict)`
刷新后更新UI。

##### `_prepare_chart_data(fund_data: list) -> list`
准备图表数据。

### DashboardWidget 类

#### 概述
仪表盘组件，显示统计信息和图表。

#### 类定义
```python
class DashboardWidget(QWidget):
    """仪表盘组件"""
```

#### 主要方法

##### `update_statistics(statistics: Dict[str, Any])`
更新统计信息。

##### `update_chart_data(chart_data: list)`
更新图表数据。

##### `update_data_source(source_name: str)`
更新数据源显示。

### ChartWidget 类

#### 概述
图表组件，提供数据可视化。

#### 类定义
```python
class ChartWidget(QWidget):
    """图表组件"""
```

#### 支持的图表类型
1. **价格历史图表**：基金净值 vs 市场价格
2. **收益率趋势图表**：套利收益率变化
3. **价差分布图表**：价差分布情况

#### 主要方法

##### `set_chart_data(data: List[Dict[str, Any]])`
设置图表数据。

**数据格式**：
```python
[
    {
        "code": "510300",
        "name": "沪深300ETF",
        "timestamp": "2026-01-30T10:00:00",
        "nav": 3.56,
        "price": 3.58,
        "yield_pct": 0.43,
        "spread_pct": 0.56
    }
]
```

##### `update_chart()`
更新图表显示。

##### `get_chart_image() -> Optional[bytes]`
获取图表图像（用于导出）。

### FundListWidget 类

#### 概述
基金列表组件，显示基金数据和套利机会。

#### 类定义
```python
class FundListWidget(QWidget):
    """基金列表组件"""
```

#### 信号定义
```python
fund_selected = pyqtSignal(str)  # 基金选择信号
```

#### 主要方法

##### `update_fund_data(fund_data: List[Dict[str, Any]])`
更新基金数据。

##### `clear_data()`
清空数据。

### FiltersWidget 类

#### 概述
筛选器组件，提供数据筛选功能。

#### 类定义
```python
class FiltersWidget(QWidget):
    """筛选器组件"""
```

#### 信号定义
```python
filter_changed = pyqtSignal(dict)  # 筛选条件变化
```

#### 筛选条件
- 基金类型（全部/ETF/LOF）
- 价差范围（最小/最大）
- 机会等级（强/弱/无）
- 只显示套利机会
- 排序方式

---

## 数据格式规范

### 基金数据格式
```python
{
    # 必需字段
    "code": "510300",                     # 基金代码，字符串
    "name": "沪深300ETF",                 # 基金名称，字符串
    "type": "ETF",                        # 基金类型，"ETF"或"LOF"

    # 价格数据
    "nav": 3.56,                          # 净值，浮点数
    "price": 3.58,                        # 市场价格，浮点数
    "spread_pct": 0.56,                   # 价差百分比，浮点数
    "yield_pct": 0.43,                    # 收益率百分比，浮点数

    # 时间信息
    "timestamp": "2026-01-30T10:00:00",   # ISO格式时间戳

    # 交易数据
    "volume": 1000000,                    # 成交量，整数
    "amount": 3580000.0,                  # 成交金额，浮点数

    # 套利信息
    "is_opportunity": True,               # 是否有套利机会，布尔值
    "opportunity_level": "premium",       # 机会等级
    "description": "ETF溢价套利机会"       # 描述
}
```

### 统计信息格式
```python
{
    "total_funds": 50,                    # 总基金数
    "etf_count": 30,                      # ETF基金数
    "lof_count": 20,                      # LOF基金数
    "opportunity_count": 15,              # 套利机会数
    "avg_spread": 0.35,                   # 平均价差
    "max_spread": 2.15,                   # 最大价差
    "min_spread": -0.82,                  # 最小价差
    "last_update": "2026-01-30 10:00:00"  # 最后更新时间
}
```

### 筛选参数格式
```python
{
    "fund_type": "ETF",                   # 基金类型：all/ETF/LOF
    "min_spread": -5.0,                   # 最小价差
    "max_spread": 5.0,                    # 最大价差
    "opportunity_levels": ["premium"],    # 机会等级列表
    "only_opportunities": True,           # 只显示机会
    "sort_by": "spread_pct_desc"          # 排序方式
}
```

### 排序选项
- `spread_pct_desc`：价差降序
- `spread_pct_asc`：价差升序
- `yield_pct_desc`：收益率降序
- `yield_pct_asc`：收益率升序
- `code_asc`：代码升序
- `name_asc`：名称升序

---

## 扩展开发指南

### 添加新的数据源

#### 步骤
1. 创建新的数据获取器类，继承`DataFetcher`
2. 实现`fetch_fund_data()`和`fetch_single_fund()`方法
3. 在`FundManager`中注册新的数据源
4. 更新UI以支持数据源切换

#### 示例
```python
class NewDataSourceFetcher(DataFetcher):
    def fetch_fund_data(self) -> List[Dict[str, Any]]:
        # 实现数据获取逻辑
        pass

    def fetch_single_fund(self, fund_code: str) -> Dict[str, Any]:
        # 实现单个基金数据获取
        pass
```

### 添加新的图表类型

#### 步骤
1. 在`ChartWidget`中添加新的图表类型常量
2. 实现对应的图表更新方法（如`_update_new_chart_type()`）
3. 在`_on_chart_type_changed()`中添加类型映射
4. 在图表类型下拉框中添加新选项

### 自定义费用配置

#### 方法
通过`ArbitrageCalculator`的构造函数传入自定义费用：
```python
custom_fees = {
    "ETF": {
        "commission": Decimal("0.00025"),  # 自定义佣金
        "stamp_tax": Decimal("0.001"),     # 默认印花税
        "total": Decimal("0.00125")        # 总费用
    }
}
calculator = ArbitrageCalculator(custom_fees=custom_fees)
```

### 数据库扩展

#### 添加新表
1. 在`Database.initialize_database()`中添加建表SQL
2. 添加对应的数据操作方法
3. 更新数据模型以使用新表

#### 示例：添加用户配置表
```python
# 在建表SQL中添加
CREATE TABLE IF NOT EXISTS user_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 测试指南

### 单元测试
测试文件位于`tests/unit/`目录：
- `test_database.py`：数据库测试
- `test_arbitrage_calculator.py`：套利计算器测试
- `test_data_fetcher.py`：数据获取器测试
- `test_fund_manager.py`：基金管理器测试

### 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/unit/test_database.py

# 带详细输出
pytest -v tests/

# 生成测试覆盖率报告
pytest --cov=src tests/
```

### 集成测试
测试文件位于`tests/integration/`目录：
- `test_database_calculator_integration.py`：数据库与计算器集成测试
- `test_fetcher_database_integration.py`：数据获取器与数据库集成测试

### UI测试
使用pytest-qt进行UI测试：
```python
# 示例UI测试
def test_main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    # 测试窗口标题
    assert window.windowTitle() == "基金套利监控"

    # 测试刷新按钮
    qtbot.mouseClick(window.findChild(QAction, "刷新数据"), Qt.MouseButton.LeftButton)
```

---

## 部署指南

### 打包应用
使用PyInstaller打包：
```bash
# 安装打包工具
pip install pyinstaller

# 运行打包脚本
python build.py
```

### 打包配置
`build.py`配置文件：
```python
app_name = "FundArbitrageMonitor"
entry_point = "src/main.py"
icon_path = "resources/app_icon.ico"  # Windows
# icon_path = "resources/app_icon.icns"  # macOS
```

### 平台特定说明

#### macOS
- 生成`.app`应用程序包
- 需要代码签名（发布版本）
- 可创建DMG安装包

#### Windows
- 生成`.exe`可执行文件
- 可能需要安装Visual C++运行时
- 可创建NSIS或Inno Setup安装程序

#### Linux
- 生成可执行文件
- 可能需要安装系统依赖
- 可创建DEB/RPM包

---

## 故障排除

### 开发环境问题

#### PyQt6导入错误
```bash
# 解决方案：重新安装PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6 PyQt6-Charts
```

#### SQLite线程错误
错误：`SQLite objects created in a thread can only be used in that same thread.`

解决方案：使用`Database._get_connection()`方法获取线程安全的连接。

#### 高DPI显示问题
解决方案：在主入口文件中添加高DPI支持：
```python
try:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
except AttributeError:
    pass  # 旧版本PyQt6可能不支持此属性
```

### 运行时问题

#### 数据库文件权限
确保应用对`data/`目录有读写权限。

#### 内存使用
应用默认使用SQLite数据库，内存使用较低。如果处理大量历史数据，考虑：
- 定期清理旧数据
- 增加数据库缓存大小
- 优化查询语句

### 性能优化建议

1. **数据库索引**：为常用查询字段添加索引
2. **批量操作**：使用批量插入/更新减少数据库操作
3. **数据缓存**：缓存频繁访问的数据
4. **异步操作**：使用QThread处理耗时操作
5. **懒加载**：延迟加载非必要数据

---

## API参考速查

### 核心类方法速查

#### Database
- `get_instance()`：获取单例实例
- `save_fund_data()`：保存基金数据
- `get_latest_prices()`：获取最新价格
- `get_price_history()`：获取价格历史
- `get_statistics()`：获取统计信息

#### ArbitrageCalculator
- `calculate_etf_arbitrage()`：计算ETF套利
- `calculate_lof_arbitrage()`：计算LOF套利
- `calculate_batch_arbitrage()`：批量计算
- `get_arbitrage_summary()`：获取摘要

#### FundManager
- `refresh_all_data()`：刷新所有数据
- `get_latest_prices()`：获取最新价格（带计算）
- `get_statistics()`：获取统计信息

#### MainController
- `refresh_all_data()`：刷新数据
- `get_filtered_funds()`：获取筛选数据
- `apply_filters()`：应用筛选
- `export_to_csv()`：导出CSV

### 信号速查

#### SignalManager信号
- `data_refresh_started`：数据刷新开始
- `data_refresh_complete`：数据刷新完成
- `filter_applied`：筛选条件应用
- `fund_selected`：基金选择

#### UI组件信号
- `DashboardWidget.statistic_clicked`：统计项点击
- `FundListWidget.fund_selected`：基金选择
- `FiltersWidget.filter_changed`：筛选条件变化

### 配置常量

#### 默认费用
```python
ETF_COMMISSION = Decimal("0.0003")    # 0.03%
ETF_STAMP_TAX = Decimal("0.001")      # 0.1%
ETF_TOTAL_FEE = Decimal("0.0013")     # 0.13%

LOF_SUBSCRIPTION = Decimal("0.015")   # 1.5%
LOF_REDEMPTION = Decimal("0.005")     # 0.5%
LOF_TOTAL_FEE = Decimal("0.02")       # 2.0%
```

#### 机会等级阈值
```python
STRONG_OPPORTUNITY_THRESHOLD = 1.5    # 强机会阈值系数
```

---

## 更新日志

### v1.4.0 (2026-01-31)
- 添加图表分析功能
- 支持三种图表类型：价格历史、收益率趋势、价差分布
- 图表随筛选条件动态更新
- 完善用户手册和API文档

### v1.3.0 (2026-01-31)
- 添加单元测试和集成测试框架
- 修复数据库线程安全问题
- 完善测试覆盖率

### v1.2.0 (2026-01-30)
- 打包为可执行文件（macOS .app）
- 添加PyInstaller打包配置
- 修复高DPI兼容性问题

### v1.1.0 (2026-01-30)
- 修复数据库线程安全问题
- 修复PyQt6版本兼容性问题
- 完善错误处理机制

### v1.0.0 (2026-01-30)
- 初始版本发布
- 实现ETF/LOF套利监控核心功能
- 提供仪表盘和基金列表界面
- 支持手动数据刷新和筛选

---

## 贡献指南

### 开发流程
1. Fork项目仓库
2. 创建功能分支
3. 实现功能并添加测试
4. 提交Pull Request
5. 通过代码审查

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 添加文档字符串
- 编写单元测试

### 提交信息格式
```
类型(范围): 简要描述

详细描述（可选）

修复 #问题编号
```

**类型**：feat、fix、docs、style、refactor、test、chore

---

*文档版本：1.4.0*
*最后更新：2026年1月31日*