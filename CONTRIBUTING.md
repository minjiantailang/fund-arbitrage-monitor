# 贡献指南

感谢你对 **Fund Arbitrage Monitor** 项目感兴趣！我们欢迎任何形式的贡献，包括提交 Bug 报告、功能建议、文档改进以及代码提交。

## 行为准则

请保持友好、尊重和专业的态度。我们致力于提供一个包容和受欢迎的社区环境。

## 如何贡献

### 报告 Bug 或提出建议

1.  **搜索现有 Issue**：在提交新 Issue 之前，请先检查是否已经有人提出过相同的问题。
2.  **使用模板**：如果可能，请使用我们提供的 Issue 模板。
3.  **提供详细信息**：详细描述问题发生的环境、复现步骤以及预期行为。

### 提交代码 (Pull Request)

1.  **Fork 仓库**：点击 GitHub 页面右上角的 "Fork" 按钮，将项目复刻到你的账户。
2.  **克隆仓库**：
    ```bash
    git clone https://github.com/YOUR_USERNAME/fund-arbitrage-monitor.git
    cd fund-arbitrage-monitor
    ```
3.  **创建分支**：为你的修改创建一个新的分支。
    ```bash
    git checkout -b feature/my-new-feature
    # 或者
    git checkout -b fix/bug-fix-description
    ```
4.  **开发环境设置**：安装开发依赖。
    ```bash
    pip install -e ".[dev]"
    ```
5.  **编写代码和测试**：进行修改并确保添加相应的测试。
6.  **运行测试**：确保所有测试通过。
    ```bash
    pytest
    ```
7.  **代码风格**：我们使用 `ruff` 和 `mypy` 进行代码检查。
    ```bash
    ruff check src tests
    mypy src
    ```
8.  **提交更改**：编写清晰的提交信息。
    ```bash
    git commit -m "feat:添加了XXX功能"
    ```
9.  **推送到远程仓库**：
    ```bash
    git push origin feature/my-new-feature
    ```
10. **创建 Pull Request**：在 GitHub 上提交 Pull Request，并详细描述你的更改。

## 开发规范

*   **Python 版本**：本项目支持 Python 3.9 及以上版本。
*   **代码风格**：请遵循 PEP 8 规范。
*   **注释**：请为你的代码添加必要的注释和文档字符串 (Docstrings)。
*   **类型注解**：强烈建议使用 Python 类型提示 (Type Hints)。

## 许可证

通过提交代码，你同意你的代码将遵循本项目的 MIT 许可证。
