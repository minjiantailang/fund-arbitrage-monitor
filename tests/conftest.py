"""
pytest配置文件 - 提供测试夹具和配置
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging
from decimal import Decimal


def pytest_configure(config):
    """pytest配置钩子"""
    # 配置测试日志级别
    logging.basicConfig(level=logging.WARNING)

    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试，默认跳过"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "ui: UI测试"
    )
    config.addinivalue_line(
        "markers", "database: 数据库测试"
    )


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="运行慢速测试"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="运行集成测试"
    )
    parser.addoption(
        "--run-ui",
        action="store_true",
        default=False,
        help="运行UI测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据命令行选项过滤测试项"""
    skip_slow = pytest.mark.skip(reason="需要 --run-slow 选项来运行慢速测试")
    skip_integration = pytest.mark.skip(reason="需要 --run-integration 选项来运行集成测试")
    skip_ui = pytest.mark.skip(reason="需要 --run-ui 选项来运行UI测试")

    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)
        if "integration" in item.keywords and not config.getoption("--run-integration"):
            item.add_marker(skip_integration)
        if "ui" in item.keywords and not config.getoption("--run-ui"):
            item.add_marker(skip_ui)


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture(scope="session")
def temp_db_dir():
    """创建临时数据库目录"""
    temp_dir = tempfile.mkdtemp(prefix="fund_arbitrage_test_")
    yield Path(temp_dir)
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_db_path(temp_db_dir):
    """返回临时数据库文件路径 - 每个测试使用唯一文件"""
    import uuid
    unique_name = f"test_fund_data_{uuid.uuid4().hex[:8]}.db"
    return temp_db_dir / unique_name


@pytest.fixture(scope="function")
def sample_fund_data():
    """返回样本基金数据 - 使用工厂生成"""
    from tests.factories import TestDataFactory
    return {
        "etf_funds": TestDataFactory.create_fund_list(count=2, fund_type="ETF"),
        "lof_funds": TestDataFactory.create_fund_list(count=2, fund_type="LOF"),
    }


@pytest.fixture(scope="function")
def mock_fund_data():
    """返回模拟基金数据 - 使用工厂生成"""
    from tests.factories import TestDataFactory
    etf = TestDataFactory.create_fund(
        code="510300",
        name="沪深300ETF",
        fund_type="ETF",
        nav=3.56,
        price=3.58,
    )
    lof = TestDataFactory.create_fund(
        code="161005",
        name="富国天惠LOF",
        fund_type="LOF",
        nav=1.56,
        price=1.58,
    )
    # 转换为 Decimal 以保持兼容性
    etf["nav"] = Decimal(str(etf["nav"]))
    etf["price"] = Decimal(str(etf["price"]))
    lof["nav"] = Decimal(str(lof["nav"]))
    lof["price"] = Decimal(str(lof["price"]))
    return [etf, lof]


@pytest.fixture(scope="function")
def decimal_values():
    """返回Decimal测试值"""
    return {
        "nav": Decimal("3.56"),
        "price": Decimal("3.58"),
        "spread": Decimal("0.02"),
        "yield_pct": Decimal("0.43"),
    }


@pytest.fixture(scope="function")
def qapp(request):
    """创建PyQt6 QApplication实例（用于UI测试）"""
    from PyQt6.QtWidgets import QApplication

    # 检查是否已有QApplication实例
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield app

    # 清理
    if not QApplication.instance():
        app.quit()


@pytest.fixture(scope="function")
def cleanup_singletons():
    """清理单例实例（确保测试隔离）"""
    yield

    # 清理全局单例实例
    import gc

    # 清理可能存在的单例
    from src.models.database import _db_instance
    from src.models.data_fetcher import _fetcher_instance
    from src.models.arbitrage_calculator import _calculator_instance

    # 尝试导入signal_manager，可能因PyQt6不可用而失败
    try:
        from src.controllers.signal_manager import _signal_manager_instance
        _signal_manager_instance = None
    except ImportError:
        # PyQt6可能不可用（在无头测试环境中）
        _signal_manager_instance = None
        pass

    _db_instance = None
    _fetcher_instance = None
    _calculator_instance = None

    # 强制垃圾回收
    gc.collect()


@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test(cleanup_singletons):
    """每个测试后自动清理"""
    yield
    # 额外的清理逻辑可以放在这里