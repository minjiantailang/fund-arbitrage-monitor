# 基金套利监控应用 - 研究发现

## 项目背景

### 需求分析
- 用户需要监控ETF和LOF基金的套利机会
- 主要关注净值与市场价格差异
- 需要手动数据更新功能
- 界面要求：仪表盘 + 基金列表筛选器

### 技术选择理由
1. **Python + PyQt**：金融数据处理能力强，跨平台支持好
2. **东方财富API**：免费、稳定、数据全面
3. **SQLite**：轻量级，适合桌面应用本地存储
4. **MVC架构**：分离关注点，便于维护和测试

---

## 技术调研

### 东方财富API调研
**可用接口**：
1. 基金净值查询：`http://fund.eastmoney.com/f10/F10DataApi.aspx`
2. 实时行情：`http://push2.eastmoney.com/api/qt/stock/get`
3. LOF基金数据：`http://fund.eastmoney.com/LOF_jzzzl.html`

**数据格式**：
- JSON格式返回
- 需要处理反爬机制（User-Agent、Referer）
- 数据更新频率：净值每日更新，价格实时更新

### PyQt6技术栈
**优势**：
- 成熟的桌面应用框架
- 信号/槽机制适合异步处理
- 丰富的UI组件库
- 良好的文档和社区支持

**关键组件**：
- `QMainWindow`：主窗口框架
- `QTableView`：基金列表显示
- `QChart`：数据可视化
- `QThread`：后台数据处理

### 套利计算逻辑
**ETF套利公式**：
```
价差% = (市场价格 - 基金净值) / 基金净值 × 100%
潜在收益率 = 价差% - 交易费用%
```

**LOF套利公式**：
```
场内场外价差% = (场内价格 - 场外净值) / 场外净值 × 100%
考虑申购赎回费用后的净收益
```

**交易费用估算**：
- ETF：佣金0.03% + 印花税0.1% = 约0.13%
- LOF：申购费1.5% + 赎回费0.5% = 约2.0%

---

## 架构设计发现

### 数据流设计
```
用户操作 → 控制器 → 数据获取 → 套利计算 → UI更新
    ↓          ↓          ↓          ↓         ↓
刷新按钮 → MainController → DataFetcher → Calculator → Dashboard
```

### 数据库设计要点
**表结构**：
1. `funds`表：基金基本信息（代码、名称、类型、成立日期等）
2. `fund_prices`表：历史价格数据（时间、净值、价格）
3. `arbitrage_opportunities`表：套利机会记录
4. `user_settings`表：用户配置

**索引优化**：
- `funds.code`：主键索引
- `fund_prices.fund_code + timestamp`：复合索引
- `arbitrage_opportunities.spread_pct`：排序索引

### UI设计发现
**响应式布局策略**：
- 使用`QHBoxLayout`和`QVBoxLayout`组合
- `QSizePolicy`控制组件伸缩行为
- `QScrollArea`处理内容溢出

**性能优化**：
- 虚拟滚动处理大量数据
- 图片和图标资源缓存
- 异步数据加载防止界面卡顿

---

## 潜在问题与解决方案

### 技术挑战
1. **API限制**：东方财富API有频率限制
   - 解决方案：添加请求间隔，使用缓存数据
   - 备用方案：实现模拟数据生成器

2. **网络稳定性**：数据获取可能失败
   - 解决方案：实现重试机制（3次重试）
   - 错误处理：降级到最近缓存数据

3. **数据一致性**：多线程数据更新可能冲突
   - 解决方案：使用线程安全的数据结构
   - 同步机制：信号/槽确保UI线程安全

### 用户体验考虑
1. **数据更新反馈**：显示加载状态和进度
2. **错误提示**：友好的错误消息和恢复建议
3. **性能感知**：显示数据更新时间戳
4. **离线支持**：缓存数据支持离线查看

---

## 开发工具选择

### 版本控制
- Git + GitHub/GitLab
- 分支策略：feature分支 + main分支

### 代码质量
- **代码格式化**：black + isort
- **类型检查**：mypy
- **代码检查**：pylint
- **测试框架**：pytest

### 开发环境
- Python 3.9+
- PyCharm / VS Code
- SQLite浏览器
- API测试工具（Postman/curl）

---

## 参考资料

### 官方文档
1. [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
2. [Pandas Documentation](https://pandas.pydata.org/docs/)
3. [SQLite Documentation](https://www.sqlite.org/docs.html)

### 相关项目参考
1. **量化交易框架**：vn.py, backtrader
2. **金融数据工具**：akshare, tushare
3. **桌面应用示例**：PyQt官方示例，Real Python教程

### 行业标准
1. **金融数据格式**：OHLC（开盘、最高、最低、收盘）
2. **时间处理**：使用pandas Timestamp，时区处理
3. **数值精度**：使用Decimal处理金融计算

---

## 待解决问题

### 技术决策待定
1. **图表库选择**：PyQtChart vs matplotlib
   - PyQtChart：集成好，性能优
   - matplotlib：功能强，学习成本高

2. **配置管理**：JSON文件 vs YAML vs INI
   - JSON：Python原生支持，结构清晰
   - YAML：可读性好，支持注释
   - INI：简单，适合基础配置

3. **日志系统**：Python logging vs 自定义
   - Python logging：功能完整，标准库
   - 自定义：更轻量，针对性优化

### 业务逻辑待确认
1. **套利阈值设置**：默认值和建议值
2. **基金筛选条件**：常用筛选组合
3. **数据更新策略**：增量更新 vs 全量更新

---

## 更新记录

### 2026-01-30
- 完成技术调研和架构设计
- 确定核心技术栈和开发工具
- 识别潜在技术挑战和解决方案

---

*文档创建时间：2026年1月30日*
*版本：1.0.0*