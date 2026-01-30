#!/usr/bin/env python3
"""
基金套利监控应用 - 主入口文件
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """应用主函数"""
    try:
        logger.info("启动基金套利监控应用")

        # 检查Python版本
        if sys.version_info < (3, 9):
            logger.error("需要Python 3.9或更高版本")
            print("错误：需要Python 3.9或更高版本")
            return 1

        # 尝试导入PyQt6
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import Qt
        except ImportError as e:
            logger.error(f"PyQt6导入失败: {e}")
            print("错误：请安装PyQt6: pip install PyQt6")
            return 1

        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("基金套利监控")
        app.setOrganizationName("FundArbitrageMonitor")

        # 设置高DPI支持
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        # 导入并创建主窗口
        try:
            from src.ui.main_window import MainWindow
            window = MainWindow()
            window.show()

            logger.info("应用启动成功")

            # 运行应用
            return app.exec()

        except ImportError as e:
            logger.error(f"导入模块失败: {e}")
            print(f"错误：模块导入失败 - {e}")
            return 1

    except Exception as e:
        logger.exception(f"应用启动失败: {e}")
        print(f"致命错误：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())