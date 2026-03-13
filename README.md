# 基金套利监控桌面应用

[![CI/CD Pipeline](https://github.com/minjiantailang/fund-arbitrage-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/minjiantailang/fund-arbitrage-monitor/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于 Python PyQt6 的桌面应用，用于监控 ETF 和 LOF 基金的套利机会。

![应用截图](docs/screenshot.png)

## ✨ 功能特性

### 核心功能
- **实时监控**：监控 ETF 基金净值与市场价格差异
- **LOF 套利**：监控 LOF 基金场内交易价格与场外申购赎回净值差异
- **套利计算**：自动计算套利收益率，考虑交易费用
- **仪表盘**：显示套利机会统计和关键指标
- **基金列表**：支持搜索、筛选、排序的基金列表
- **图表分析**：价格历史、收益率趋势、价差分布图表

### 用户体验
- **🎨 现代界面**：全新的 Modern 风格 UI，卡片式布局，清爽专业
- **⚡️ 自动刷新**：每 5 分钟自动更新数据，保持行情实时性
- **⌨️ 快捷键支持**：完善的键盘快捷键操作
- **📁 多格式导出**：所见即所得的数据导出（Excel/CSV/JSON）
- **💾 数据缓存**：本地 SQLite 数据库缓存历史数据
- **💻 跨平台**：支持 Windows 和 macOS

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+R` / `F5` | 立即刷新数据 |
| `Ctrl+E` | 导出当前列表数据 |
| `Ctrl+F` | 聚焦搜索框 |
| `Escape` | 清除选择 |

## 🛠 技术栈

| 类别 | 技术 |
|------|------|
| **语言** | Python 3.9+ |
| **GUI框架** | PyQt6 |
| **图表** | PyQt6-Charts (可选) |
| **数据处理** | Pandas |
| **数据库** | SQLite |
| **HTTP请求** | Requests |
| **测试框架** | pytest, pytest-qt |
| **代码检查** | Ruff, MyPy |

## 📦 安装

### 从源码安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/minjiantailang/fund-arbitrage-monitor.git
   cd fund-arbitrage-monitor
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -e .
   ```

4. 安装开发依赖（可选）：
   ```bash
   pip install -e ".[dev]"
   ```

5. 安装图表支持（可选）：
   ```bash
   pip install -e ".[charts]"
   ```

### 使用可执行文件

下载对应平台的预编译版本：
- **Windows**: `fund-arbitrage-monitor-windows.exe`
- **macOS**: `fund-arbitrage-monitor-macos.app`
- **Linux**: `fund-arbitrage-monitor-linux`

> **Windows 用户提示**：请查看 [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) 获取详细的 Windows 安装、运行和打包指南。

## 🚀 使用说明

### 启动应用

```bash
# 从源码运行
python -m src.main

# 或使用安装的脚本
fund-arbitrage-monitor
```

### 基本操作

1. **刷新数据**：点击工具栏的"刷新数据"按钮或按 F5 获取最新基金数据
2. **筛选基金**：使用右侧的筛选器按类型、价差范围筛选基金
3. **查看详情**：双击基金行查看该基金的详细历史图表
4. **导出数据**：点击"导出CSV"按钮或按 Ctrl+E 导出数据
5. **切换主题**：点击"切换主题"按钮或按 Ctrl+T 切换亮色/暗色主题

### 数据导出格式

| 格式 | 说明 |
|------|------|
| CSV | 标准逗号分隔格式，支持Excel打开 |
| JSON | 结构化JSON格式，便于程序处理 |
| Excel | 原生Excel格式 (.xlsx) |
| HTML | 精美的可视化报告 |

## 🧪 开发

### 项目结构

```
fund-arbitrage-monitor/
├── src/
│   ├── models/              # 数据模型层
│   │   ├── database.py      # 数据库操作
│   │   ├── data_fetcher.py  # 数据获取器
│   │   ├── arbitrage_calculator.py  # 套利计算
│   │   └── fund_manager.py  # 基金管理器
│   ├── ui/                  # 用户界面层
│   │   ├── main_window.py   # 主窗口
│   │   ├── dashboard_widget.py  # 仪表盘
│   │   ├── fund_list_widget.py  # 基金列表
│   │   ├── chart_widget.py  # 图表组件
│   │   ├── filters_widget.py  # 筛选器
│   │   └── theme_manager.py # 主题管理
│   ├── controllers/         # 控制器层
│   │   ├── main_controller.py
│   │   ├── data_controller.py
│   │   └── signal_manager.py
│   ├── utils/               # 工具模块
│   │   └── data_exporter.py # 数据导出器
│   └── main.py              # 应用入口
├── tests/                   # 测试文件
│   ├── unit/                # 单元测试
│   ├── ui/                  # UI测试
│   ├── integration/         # 集成测试
│   └── performance/         # 性能测试
├── .github/workflows/       # CI/CD配置
└── pyproject.toml           # 项目配置
```

### 开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装图表支持
pip install PyQt6-Charts
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ --run-ui --run-integration --run-slow -v

# 运行单元测试
pytest tests/unit -v

# 运行UI测试
pytest tests/ui --run-ui -v

# 运行集成测试
pytest tests/integration --run-integration -v

# 运行性能测试
pytest tests/performance --run-slow -v

# 生成覆盖率报告
pytest tests/ --run-ui --run-integration --run-slow --cov=src --cov-report=html
```

### 代码质量

```bash
# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/ --ignore-missing-imports

# 代码格式化
ruff format src/ tests/
```

### 构建可执行文件

```bash
# 安装构建依赖
pip install -e ".[build]"

# 使用PyInstaller构建
python build.py

# 或手动构建
pyinstaller --name="fund-arbitrage-monitor" \
            --windowed \
            --icon=assets/icon.ico \
            --add-data="assets:assets" \
            src/main.py
```

## 📊 测试覆盖率

| 模块 | 覆盖率 |
|------|--------|
| `src/ui/theme_manager.py` | 100% |
| `src/ui/dashboard_widget.py` | 99% |
| `src/models/data_fetcher.py` | 98% |
| `src/ui/filters_widget.py` | 95% |
| `src/controllers/main_controller.py` | 94% |
| `src/controllers/signal_manager.py` | 93% |
| `src/ui/chart_widget.py` | 92% |
| **总计** | **89%** |

## 🔌 数据源

应用使用东方财富API获取基金数据：
- 基金净值查询
- 实时行情数据
- LOF基金场内外数据

**注意**：API有频率限制，请合理使用。应用实现了数据缓存机制以减少API调用。

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 编写测试
4. 提交更改 (`git commit -m 'Add some amazing feature'`)
5. 确保测试通过 (`pytest`)
6. 推送到分支 (`git push origin feature/amazing-feature`)
7. 创建Pull Request

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 编写单元测试（覆盖率 > 80%）
- 更新相关文档

## 📄 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本工具仅供学习和研究使用，不构成投资建议。基金投资有风险，请谨慎决策。作者不对因使用本工具造成的任何投资损失负责。

## 📮 联系方式

- 问题反馈：[GitHub Issues](https://github.com/minjiantailang/fund-arbitrage-monitor/issues)
- 功能建议：[GitHub Discussions](https://github.com/minjiantailang/fund-arbitrage-monitor/discussions)

---

*最后更新：2026年1月31日*