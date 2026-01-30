# 基金套利监控桌面应用

一个基于Python PyQt6的桌面应用，用于监控ETF和LOF基金的套利机会。

## 功能特性

- **实时监控**：监控ETF基金净值与市场价格差异
- **LOF套利**：监控LOF基金场内交易价格与场外申购赎回净值差异
- **手动数据更新**：用户手动触发数据刷新
- **仪表盘**：显示套利机会统计和关键指标
- **基金列表**：支持搜索、筛选、排序的基金列表
- **数据缓存**：本地SQLite数据库缓存历史数据

## 技术栈

- **Python 3.9+**
- **PyQt6**：桌面应用框架
- **Pandas**：数据处理和分析
- **SQLite**：本地数据存储
- **Requests**：HTTP请求库

## 安装

### 从源码安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/username/fund-arbitrage-monitor.git
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

### 使用可执行文件

下载对应平台的预编译版本：
- Windows: `fund-arbitrage-monitor.exe`
- macOS: `fund-arbitrage-monitor.app`
- Linux: `fund-arbitrage-monitor`

## 使用说明

### 启动应用

```bash
# 从源码运行
python -m src.main

# 或使用安装的脚本
fund-arbitrage-monitor
```

### 基本操作

1. **刷新数据**：点击工具栏的"刷新"按钮获取最新基金数据
2. **筛选基金**：使用右侧的筛选器按类型、价差范围筛选基金
3. **查看详情**：双击基金行查看该基金的详细历史图表
4. **导出数据**：点击"导出CSV"按钮将当前数据导出为CSV文件

### 配置说明

应用配置文件位于：
- Windows: `%APPDATA%\fund-arbitrage-monitor\config.json`
- macOS: `~/Library/Application Support/fund-arbitrage-monitor/config.json`
- Linux: `~/.config/fund-arbitrage-monitor/config.json`

可配置项：
- API密钥（如需）
- 数据更新频率
- 通知设置
- 界面主题（深色/浅色）

## 开发

### 项目结构

```
fund-arbitrage-monitor/
├── src/
│   ├── models/          # 数据模型层
│   │   ├── data_fetcher.py
│   │   ├── arbitrage_calculator.py
│   │   └── fund_manager.py
│   ├── ui/             # 用户界面层
│   │   ├── main_window.py
│   │   ├── dashboard_widget.py
│   │   └── fund_list_widget.py
│   ├── controllers/    # 控制器层
│   │   ├── main_controller.py
│   │   └── data_controller.py
│   ├── data_sources/   # 数据源接口
│   │   └── eastmoney_api.py
│   └── main.py         # 应用入口
├── tests/              # 测试文件
├── docs/               # 文档
└── requirements.txt    # 依赖列表
```

### 开发环境设置

1. 安装开发依赖：
   ```bash
   pip install -e ".[dev]"
   ```

2. 运行测试：
   ```bash
   pytest
   ```

3. 代码格式化：
   ```bash
   black src tests
   isort src tests
   ```

4. 类型检查：
   ```bash
   mypy src
   ```

### 构建可执行文件

```bash
# 安装构建依赖
pip install -e ".[build]"

# 使用PyInstaller构建
pyinstaller --name="fund-arbitrage-monitor" --windowed src/main.py
```

## 数据源

应用使用东方财富API获取基金数据：
- 基金净值查询
- 实时行情数据
- LOF基金场内外数据

**注意**：API有频率限制，请合理使用。应用实现了数据缓存机制以减少API调用。

## 贡献

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 编写单元测试
- 更新相关文档

## 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 免责声明

本工具仅供学习和研究使用，不构成投资建议。基金投资有风险，请谨慎决策。作者不对因使用本工具造成的任何投资损失负责。

## 联系方式

- 问题反馈：[GitHub Issues](https://github.com/username/fund-arbitrage-monitor/issues)
- 功能建议：[GitHub Discussions](https://github.com/username/fund-arbitrage-monitor/discussions)

---

*最后更新：2026年1月30日*