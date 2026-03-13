# 基金套利监控应用 - 开发指南

## 概述

本文档为开发者提供基金套利监控应用的开发环境配置、项目结构说明、开发工作流程和扩展开发指南。

### 目标读者
- 应用维护者
- 功能扩展开发者
- 二次开发人员
- 技术研究人员

### 文档结构
1. 开发环境配置
2. 项目结构解析
3. 开发工作流程
4. 代码规范
5. 测试指南
6. 扩展开发
7. 部署与发布

---

## 开发环境配置

### 1. 系统要求

#### 硬件要求
- CPU：双核以上
- 内存：4GB以上
- 磁盘：1GB可用空间

#### 软件要求
- 操作系统：Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- Python：3.9或更高版本
- Git：版本控制工具

### 2. 环境搭建步骤

#### 步骤1：克隆代码库
```bash
git clone <repository-url>
cd fund-arbitrage-monitor
```

#### 步骤2：创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 步骤3：安装依赖
```bash
# 使用清华镜像源（国内用户推荐）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或使用默认源
pip install -r requirements.txt
```

#### 步骤4：验证安装
```bash
# 检查关键包版本
python -c "import PyQt6; print(f'PyQt6 version: {PyQt6.__version__}')"
python -c "import pandas; print(f'pandas version: {pandas.__version__}')"

# 运行简单测试
python demo.py
```

### 3. 开发工具推荐

#### 代码编辑器
- **VS Code**：推荐，安装Python扩展
- **PyCharm**：专业Python IDE
- **Sublime Text**：轻量级编辑器

#### 必备扩展/插件
- Python语言支持
- Git集成
- 代码格式化工具（black, isort）
- 类型检查工具（mypy）

#### 配置示例（VS Code）
`.vscode/settings.json`：
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### 4. 数据库配置

应用使用SQLite数据库，无需额外配置：
- 数据库文件：`data/fund_arbitrage.db`
- 首次运行自动创建
- 开发环境自动填充测试数据

#### 手动初始化数据库
```bash
python -c "
from src.models.database import Database
db = Database.get_instance()
db.initialize_database()
print('数据库初始化完成')
"
```

---

## 项目结构解析

### 整体结构
```
fund-arbitrage-monitor/
├── src/                    # 源代码目录
├── tests/                  # 测试代码
├── docs/                   # 文档
├── data/                   # 数据文件
├── logs/                   # 日志文件
├── build/                  # 构建输出
├── dist/                   # 分发文件
├── requirements.txt        # Python依赖
├── pyproject.toml         # 项目配置
├── README.md              # 项目说明
└── .gitignore             # Git忽略文件
```

### 源代码结构详解

#### `src/models/` - 数据模型层
```
models/
├── database.py           # 数据库管理
├── arbitrage_calculator.py # 套利计算核心
├── data_fetcher.py      # 数据获取抽象
└── fund_manager.py      # 业务逻辑协调
```

**设计模式**：单例模式（Database, FundManager）、策略模式（DataFetcher）

#### `src/ui/` - 用户界面层
```
ui/
├── main_window.py       # 主窗口
├── dashboard_widget.py  # 仪表盘
├── fund_list_widget.py  # 基金列表
├── filters_widget.py    # 筛选器
└── chart_widget.py      # 图表组件
```

**设计模式**：组合模式（Widget组合）、观察者模式（信号-槽）

#### `src/controllers/` - 控制层
```
controllers/
├── main_controller.py   # 主控制器
├── data_controller.py   # 数据控制器
└── signal_manager.py    # 信号管理器
```

**设计模式**：中介者模式（SignalManager）、命令模式（Controller）

### 关键文件说明

#### `src/main.py` - 应用入口
- 初始化QApplication
- 设置高DPI支持
- 创建主窗口
- 启动事件循环

#### `src/models/database.py` - 数据库核心
- 线程安全的连接管理
- SQLite操作封装
- 数据持久化逻辑

#### `src/controllers/signal_manager.py` - 事件总线
- 集中管理应用信号
- 解耦组件通信
- 支持异步事件处理

### 依赖关系图
```
                  +----------------+
                  |   MainWindow   |
                  +-------+--------+
                          |
                  +-------+--------+
                  | MainController |
                  +-------+--------+
                          |
          +---------------+---------------+
          |                               |
  +-------+-------+               +-------+-------+
  | DataController|               | SignalManager |
  +-------+-------+               +---------------+
          |
  +-------+-------+
  |  FundManager  |
  +-------+-------+
          |
  +-------+---------------+
  |                       |
+-----+-----+       +-----+-----+
| Database |       | Calculator|
+-----------+       +-----------+
```

---

## 开发工作流程

### 1. 功能开发流程

#### 步骤1：需求分析
- 明确功能需求
- 确定技术方案
- 评估工作量

#### 步骤2：代码实现
- 创建功能分支
- 实现核心逻辑
- 编写单元测试

#### 步骤3：集成测试
- 测试功能完整性
- 验证与其他模块的兼容性
- 进行UI测试

#### 步骤4：代码审查
- 检查代码质量
- 验证测试覆盖率
- 确保文档完整性

#### 步骤5：合并发布
- 合并到主分支
- 更新版本号
- 生成发布说明

### 2. 调试技巧

#### PyQt6调试
```python
# 启用Qt调试信息
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

# 信号调试
def debug_slot(*args):
    print(f"Signal received: {args}")
    import traceback
    traceback.print_stack()

signal.connect(debug_slot)
```

#### 数据库调试
```python
# 启用SQLite调试
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)
sqlite3.enable_callback_tracebacks(True)

# 查看数据库状态
db = Database.get_instance()
with db._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", cursor.fetchall())
```

#### 性能分析
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # 执行要分析的代码
    your_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('time').print_stats(10)
```

### 3. 版本控制流程

#### 分支策略
- `main`：稳定版本分支
- `develop`：开发分支
- `feature/*`：功能分支
- `bugfix/*`：修复分支
- `release/*`：发布分支

#### 提交规范
```
类型(模块): 简要描述

详细描述：
- 变更内容1
- 变更内容2

相关issue: #123
```

**类型说明**：
- `feat`：新功能
- `fix`：bug修复
- `docs`：文档更新
- `style`：代码格式
- `refactor`：代码重构
- `test`：测试相关
- `chore`：构建/工具更新

### 4. 代码质量保证

#### 静态检查
```bash
# 代码格式化
black src/ tests/

# 导入排序
isort src/ tests/

# 类型检查
mypy src/

# 代码质量
pylint src/
```

#### 自动化检查
创建预提交钩子（`.git/hooks/pre-commit`）：
```bash
#!/bin/bash
echo "Running pre-commit checks..."

# 运行代码格式化
black --check src/ tests/
if [ $? -ne 0 ]; then
    echo "Code formatting check failed. Run 'black src/ tests/' to fix."
    exit 1
fi

# 运行导入排序检查
isort --check-only src/ tests/
if [ $? -ne 0 ]; then
    echo "Import sorting check failed. Run 'isort src/ tests/' to fix."
    exit 1
fi

echo "All checks passed!"
exit 0
```

---

## 代码规范

### 1. Python编码规范

#### PEP 8规范
- 缩进：4个空格
- 行宽：最大79字符（代码），72字符（注释/文档）
- 导入：分组排序（标准库、第三方、本地）
- 命名：
  - 类名：`CamelCase`
  - 函数/变量：`snake_case`
  - 常量：`UPPER_CASE`

#### 类型注解
```python
from typing import List, Dict, Optional, Any

def process_data(
    data_list: List[Dict[str, Any]],
    max_items: Optional[int] = None
) -> Dict[str, Any]:
    """处理数据函数"""
    pass
```

#### 文档字符串
```python
def calculate_yield(nav: float, price: float) -> float:
    """
    计算套利收益率

    Args:
        nav: 基金净值
        price: 市场价格

    Returns:
        float: 收益率百分比

    Raises:
        ValueError: 当净值为0时抛出

    Example:
        >>> calculate_yield(1.0, 1.05)
        5.0
    """
    if nav == 0:
        raise ValueError("净值不能为0")
    return (price - nav) / nav * 100
```

### 2. PyQt6开发规范

#### 信号-槽规范
```python
class MyWidget(QWidget):
    # 信号定义在类级别
    data_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._connect_signals()

    def _connect_signals(self):
        # 使用lambda时避免捕获问题
        self.button.clicked.connect(lambda: self._on_button_clicked())
        # 或者使用functools.partial
        from functools import partial
        self.button.clicked.connect(partial(self._on_button_clicked, param=value))
```

#### 线程安全
```python
class Worker(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        try:
            result = self._do_work()
            # 通过信号传递结果（线程安全）
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Worker error: {e}")

    def _do_work(self):
        # 耗时操作
        pass
```

### 3. 数据库访问规范

#### 连接管理
```python
class Database:
    def _get_connection(self) -> sqlite3.Connection:
        """获取线程安全的数据库连接"""
        # 每个线程创建独立连接
        thread_id = threading.get_ident()
        if thread_id not in self._connections:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            conn.row_factory = sqlite3.Row
            self._connections[thread_id] = conn
        return self._connections[thread_id]
```

#### 事务处理
```python
def save_data(self, data: List[Dict]) -> bool:
    """批量保存数据（使用事务）"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 开始事务（隐式）
            for item in data:
                cursor.execute(insert_sql, item)
            conn.commit()  # 提交事务
            return True
    except sqlite3.Error as e:
        conn.rollback()  # 回滚事务
        logger.error(f"Save failed: {e}")
        return False
```

### 4. 错误处理规范

#### 异常层次
```python
class AppError(Exception):
    """应用基础异常"""
    pass

class DatabaseError(AppError):
    """数据库异常"""
    pass

class CalculationError(AppError):
    """计算异常"""
    pass

# 使用示例
try:
    result = calculator.calculate(nav, price)
except CalculationError as e:
    logger.error(f"Calculation failed: {e}")
    show_error_message("计算失败", str(e))
except Exception as e:
    logger.exception("Unexpected error")
    show_error_message("系统错误", "请查看日志")
```

#### 日志记录
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用不同日志级别
logger.debug("调试信息")    # 开发调试
logger.info("普通信息")     # 正常运行
logger.warning("警告信息")  # 潜在问题
logger.error("错误信息")    # 功能错误
logger.critical("严重错误") # 系统错误
```

---

## 测试指南

### 1. 测试策略

#### 测试金字塔
```
        UI测试（少量）
           ↑
   集成测试（中等）
           ↑
单元测试（大量基础）
```

#### 测试范围
- **单元测试**：函数、类方法
- **集成测试**：模块间交互
- **UI测试**：用户界面交互
- **性能测试**：响应时间、内存使用

### 2. 单元测试示例

#### 数据库测试
```python
import pytest
from src.models.database import Database

class TestDatabase:
    @pytest.fixture
    def db(self):
        """创建测试数据库"""
        db = Database.get_instance()
        db.db_path = ":memory:"  # 内存数据库
        db.initialize_database()
        yield db
        # 清理
        db._connections.clear()

    def test_save_fund_data(self, db):
        """测试保存基金数据"""
        test_data = [{
            "code": "TEST001",
            "name": "测试基金",
            "type": "ETF",
            "nav": 1.0,
            "price": 1.05,
            "timestamp": "2026-01-01T00:00:00"
        }]

        result = db.save_fund_data(test_data)
        assert result is True

        # 验证数据保存
        prices = db.get_latest_prices(["TEST001"])
        assert len(prices) == 1
        assert prices[0]["fund_code"] == "TEST001"
```

#### 计算器测试
```python
from decimal import Decimal
from src.models.arbitrage_calculator import ArbitrageCalculator

def test_etf_premium_calculation():
    """测试ETF溢价计算"""
    calculator = ArbitrageCalculator()

    result = calculator.calculate_etf_arbitrage(
        Decimal("1.00"),  # NAV
        Decimal("1.05"),  # Price
        "TEST001"
    )

    assert result["is_opportunity"] is True
    assert result["opportunity_level"] == "premium"
    assert result["spread_pct"] > 0
    assert result["net_yield_pct"] > 0
    assert result["net_yield_pct"] < result["spread_pct"]  # 扣除费用
```

### 3. 集成测试示例

```python
import pytest
from src.models.fund_manager import get_fund_manager
from src.models.database import Database

class TestFundManagerIntegration:
    @pytest.fixture
    def setup(self):
        """测试设置"""
        manager = get_fund_manager()
        db = Database.get_instance()
        db.db_path = ":memory:"
        db.initialize_database()
        yield manager
        # 清理

    def test_refresh_and_calculate_integration(self, setup):
        """测试刷新和计算集成"""
        manager = setup

        # 刷新数据
        result = manager.refresh_all_data()
        assert result["success"] is True

        # 获取数据并验证计算
        prices = manager.get_latest_prices()
        assert len(prices) > 0

        for price in prices:
            assert "spread_pct" in price
            assert "yield_pct" in price
            assert "is_opportunity" in price
```

### 4. UI测试示例

```python
import pytest
from pytestqt.qt_compat import qt_api
from src.ui.main_window import MainWindow

def test_main_window_creation(qtbot):
    """测试主窗口创建"""
    window = MainWindow()
    qtbot.addWidget(window)

    # 验证窗口属性
    assert window.windowTitle() == "基金套利监控"

    # 验证组件存在
    assert window.dashboard_widget is not None
    assert window.fund_list_widget is not None
    assert window.filters_widget is not None

    # 测试刷新按钮
    refresh_action = window.findChild(qt_api.QtWidgets.QAction, "刷新数据")
    assert refresh_action is not None

    # 模拟点击
    with qtbot.waitSignal(window.refresh_requested, timeout=1000):
        refresh_action.trigger()
```

### 5. 测试运行

#### 运行所有测试
```bash
pytest tests/ -v
```

#### 运行特定测试
```bash
pytest tests/unit/test_database.py -v
pytest tests/unit/test_database.py::TestDatabase::test_save_fund_data -v
```

#### 生成覆盖率报告
```bash
pytest --cov=src tests/ --cov-report=html
# 打开 htmlcov/index.html 查看报告
```

#### 测试配置
`pytest.ini`配置文件：
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

---

## 扩展开发

### 1. 添加新功能模块

#### 步骤示例：添加报警功能
1. **创建报警模块**
   ```bash
   src/
   ├── models/
   │   └── alert_manager.py
   ├── controllers/
   │   └── alert_controller.py
   └── ui/
       └── alert_widget.py
   ```

2. **实现报警逻辑**
   ```python
   # src/models/alert_manager.py
   class AlertManager:
       def __init__(self):
           self.thresholds = {}
           self.subscribers = []

       def add_threshold(self, fund_code: str, threshold: float):
           """添加报警阈值"""
           pass

       def check_alerts(self, prices: List[Dict]) -> List[Dict]:
           """检查报警条件"""
           pass
   ```

3. **集成到主应用**
   ```python
   # 在主控制器中添加
   class MainController:
       def __init__(self):
           self.alert_manager = AlertManager()
           self.alert_controller = AlertController(self.alert_manager)
   ```

### 2. 添加新数据源

#### 实现新的DataFetcher
```python
class NewAPIDataFetcher(DataFetcher):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.example.com"

    def fetch_fund_data(self) -> List[Dict[str, Any]]:
        """从新API获取数据"""
        import requests

        response = requests.get(
            f"{self.base_url}/funds",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()

        # 转换数据格式
        return self._transform_data(response.json())

    def _transform_data(self, raw_data: dict) -> List[Dict]:
        """转换数据格式为应用标准格式"""
        transformed = []
        for item in raw_data.get("data", []):
            transformed.append({
                "code": item["symbol"],
                "name": item["name"],
                "type": "ETF" if item.get("is_etf") else "LOF",
                "nav": float(item["nav"]),
                "price": float(item["price"]),
                "timestamp": item["timestamp"],
                "volume": int(item.get("volume", 0)),
                "amount": float(item.get("amount", 0))
            })
        return transformed
```

#### 注册数据源
```python
# 在FundManager中
class FundManager:
    def __init__(self, fetcher_type: str = "mock"):
        if fetcher_type == "new_api":
            self.fetcher = NewAPIDataFetcher(api_key="your_key")
        elif fetcher_type == "mock":
            self.fetcher = MockDataFetcher()
        # ... 其他数据源
```

### 3. 自定义图表类型

#### 添加新图表
```python
class ChartWidget(QWidget):
    # 添加新图表类型
    CHART_TYPES = {
        "price_history": "价格历史",
        "yield_trend": "收益率趋势",
        "spread_distribution": "价差分布",
        "volume_analysis": "成交量分析"  # 新增
    }

    def _update_volume_analysis_chart(self):
        """更新成交量分析图表"""
        # 实现新图表逻辑
        pass

    def update_chart(self):
        """更新图表（扩展）"""
        if self.current_chart_type == "volume_analysis":
            self._update_volume_analysis_chart()
        # ... 原有逻辑
```

### 4. 国际化支持

#### 添加多语言
```python
# 创建翻译文件
translations/
├── zh_CN.ts    # 中文
├── en_US.ts    # 英文
└── ja_JP.ts    # 日文

# 在代码中使用
class MainWindow(QMainWindow):
    def __init__(self):
        self.translator = QTranslator()
        self.load_language("zh_CN")

    def load_language(self, lang: str):
        """加载语言文件"""
        if self.translator.load(f":/translations/{lang}.ts"):
            QApplication.instance().installTranslator(self.translator)
            self.retranslate_ui()

    def retranslate_ui(self):
        """重新翻译UI"""
        self.setWindowTitle(self.tr("Fund Arbitrage Monitor"))
        # ... 其他翻译
```

---

## 部署与发布

### 1. 版本管理

#### 版本号规范
语义化版本：`主版本.次版本.修订版本`
- `主版本`：不兼容的API修改
- `次版本`：向下兼容的功能性新增
- `修订版本`：向下兼容的问题修正

#### 版本发布流程
1. 更新`pyproject.toml`中的版本号
2. 更新CHANGELOG.md
3. 创建发布分支
4. 运行完整测试套件
5. 打包发布版本
6. 创建Git标签

### 2. 打包配置

#### PyInstaller配置
```python
# build.py
import PyInstaller.__main__

app_name = "FundArbitrageMonitor"
version = "1.4.0"

PyInstaller.__main__.run([
    'src/main.py',
    '--name', app_name,
    '--windowed',  # 无控制台窗口
    '--onefile',   # 单文件（可选）
    '--icon', 'resources/app_icon.ico',
    '--add-data', 'data:data',
    '--add-data', 'docs:docs',
    '--hidden-import', 'PyQt6.sip',
    '--hidden-import', 'pandas',
    '--clean',
    '--noconfirm'
])
```

#### 平台特定配置
**Windows**：
- 图标：`.ico`格式
- 可能需要安装Visual C++ Redistributable

**macOS**：
- 图标：`.icns`格式
- 需要代码签名（发布版本）
- 可创建`.dmg`安装包

**Linux**：
- 图标：`.png`格式
- 可能需要安装系统依赖
- 可创建`.deb`或`.rpm`包

### 3. 持续集成

#### GitHub Actions示例
`.github/workflows/test.yml`：
```yaml
name: Test and Build

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-qt pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2

  build:
    needs: test
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macOS-latest, ubuntu-latest]

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Build application
      run: python build.py

    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: ${{ matrix.os }}-build
        path: dist/
```

### 4. 发布检查清单

- [ ] 所有测试通过
- [ ] 文档更新完成
- [ ] 版本号已更新
- [ ] 变更日志已记录
- [ ] 代码已格式化
- [ ] 依赖包已更新
- [ ] 打包版本测试通过
- [ ] 发布说明已编写

---

## 故障排除与调试

### 常见问题解决方案

#### 1. PyQt6导入错误
**问题**：`ModuleNotFoundError: No module named 'PyQt6'`
**解决**：
```bash
# 确认虚拟环境激活
# 重新安装PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-Charts
pip install PyQt6 PyQt6-Charts
```

#### 2. 数据库线程错误
**问题**：`SQLite objects created in a thread can only be used in that same thread.`
**解决**：使用`Database._get_connection()`方法获取线程安全连接。

#### 3. 高DPI显示模糊
**解决**：在主入口文件中添加：
```python
try:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
except AttributeError:
    pass
```

#### 4. 打包后资源丢失
**解决**：确保在PyInstaller配置中添加资源文件：
```python
'--add-data', 'data:data',
'--add-data', 'resources:resources',
```

### 调试工具

#### PyQt6调试工具
```python
# 启用Qt调试
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'

# 查看可用样式
from PyQt6.QtWidgets import QStyleFactory
print("Available styles:", QStyleFactory.keys())

# 设置调试样式
app.setStyle('Fusion')  # 跨平台样式
```

#### 性能分析工具
```python
import cProfile
import pstats
from io import StringIO

def profile_code():
    pr = cProfile.Profile()
    pr.enable()

    # 要分析的代码
    your_function()

    pr.disable()
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())
```

#### 内存分析工具
```python
import tracemalloc

def analyze_memory():
    tracemalloc.start()

    # 执行代码
    your_function()

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("[ Top 10 memory usage ]")
    for stat in top_stats[:10]:
        print(stat)

    tracemalloc.stop()
```

### 获取帮助

#### 资源链接
- **PyQt6文档**：https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Python文档**：https://docs.python.org/3/
- **SQLite文档**：https://www.sqlite.org/docs.html
- **项目Issue**：GitHub Issues页面

#### 社区支持
- Stack Overflow：使用标签`[pyqt6]`、`[python]`
- PyQt邮件列表
- GitHub Discussions

---

## 附录

### A. 开发命令速查

```bash
# 环境管理
python -m venv venv              # 创建虚拟环境
source venv/bin/activate         # 激活环境（macOS/Linux）
venv\Scripts\activate            # 激活环境（Windows）
deactivate                       # 退出虚拟环境

# 依赖管理
pip install -r requirements.txt  # 安装依赖
pip freeze > requirements.txt    # 生成依赖文件
pip list                         # 查看已安装包

# 代码质量
black src/ tests/                # 代码格式化
isort src/ tests/                # 导入排序
mypy src/                        # 类型检查
pylint src/                      # 代码检查

# 测试
pytest tests/ -v                 # 运行测试
pytest --cov=src tests/          # 测试覆盖率
pytest tests/ -k "test_database" # 运行特定测试

# 运行
python -m src.main               # 运行应用
python demo.py                   # 运行演示
```

### B. 配置文件示例

#### `pyproject.toml`
```toml
[project]
name = "fund-arbitrage-monitor"
version = "1.4.0"
description = "ETF and LOF arbitrage monitoring desktop application"
authors = [{name = "Developer", email = "dev@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "PyQt6>=6.5.0",
    "PyQt6-Charts>=6.5.0",
    "pandas>=2.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-qt>=4.2.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "pylint>=3.0.0",
]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 79
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 79
```

### C. 有用的代码片段

#### 单例模式实现
```python
from threading import Lock

class SingletonMeta(type):
    """线程安全的单例元类"""
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    pass
```

#### 信号管理器模式
```python
from PyQt6.QtCore import QObject, pyqtSignal

class SignalManager(QObject, metaclass=SingletonMeta):
    """集中式信号管理器"""
    data_updated = pyqtSignal(dict)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)

    def emit_data_updated(self, data):
        """发射数据更新信号"""
        self.data_updated.emit(data)
```

#### 线程安全的数据缓存
```python
from threading import RLock
from typing import Dict, Any

class ThreadSafeCache:
    """线程安全缓存"""
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = RLock()

    def get(self, key: str, default=None):
        with self._lock:
            return self._cache.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = value

    def clear(self):
        with self._lock:
            self._cache.clear()
```

---

## 更新日志

### v1.4.0 (2026-01-31)
- 添加图表分析功能
- 完善开发文档体系
- 优化代码结构

### v1.3.0 (2026-01-31)
- 建立完整测试框架
- 修复线程安全问题
- 添加代码质量工具

### v1.2.0 (2026-01-30)
- 实现应用打包
- 修复兼容性问题
- 添加资源文件管理

### v1.1.0 (2026-01-30)
- 优化架构设计
- 完善错误处理
- 添加日志系统

### v1.0.0 (2026-01-30)
- 初始版本发布
- 实现核心功能
- 建立项目基础

---

*文档版本：1.4.0*
*最后更新：2026年1月31日*