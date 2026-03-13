"""
性能测试 - 测试各组件的响应时间和处理能力
"""
import pytest
import time
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime


pytestmark = pytest.mark.slow


class TestPerformance:
    """性能测试类"""

    def test_database_save_performance(self, temp_db_path):
        """测试数据库保存性能"""
        from src.models.database import Database

        db = Database(str(temp_db_path))

        # 生成大量测试数据
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "code": f"51{i:04d}",
                "name": f"测试基金{i}",
                "type": "ETF" if i % 2 == 0 else "LOF",
                "nav": Decimal(f"{3.0 + i * 0.01:.2f}"),
                "price": Decimal(f"{3.02 + i * 0.01:.2f}"),
                "volume": 1000000 + i * 10000,
                "amount": float(3000000 + i * 50000),
                "timestamp": datetime.now().isoformat()
            })

        # 测量保存时间
        start_time = time.time()
        result = db.save_fund_data(large_dataset)
        elapsed_time = time.time() - start_time

        assert result is True
        # 保存100条数据应该在1秒内完成
        assert elapsed_time < 1.0, f"保存性能过慢: {elapsed_time:.2f}秒"

    def test_database_query_performance(self, temp_db_path):
        """测试数据库查询性能"""
        from src.models.database import Database

        db = Database(str(temp_db_path))

        # 先保存一些数据
        test_data = []
        for i in range(50):
            test_data.append({
                "code": f"51{i:04d}",
                "name": f"测试基金{i}",
                "type": "ETF",
                "nav": Decimal(f"{3.0 + i * 0.01:.2f}"),
                "price": Decimal(f"{3.02 + i * 0.01:.2f}"),
                "volume": 1000000,
                "amount": 3000000.0,
                "timestamp": datetime.now().isoformat()
            })
        db.save_fund_data(test_data)

        # 测量查询时间
        start_time = time.time()
        for _ in range(10):
            prices = db.get_fund_prices(limit=50)
        elapsed_time = time.time() - start_time

        # 10次查询应该在0.5秒内完成
        assert elapsed_time < 0.5, f"查询性能过慢: {elapsed_time:.2f}秒"

    def test_calculator_batch_performance(self):
        """测试计算器批量计算性能"""
        from src.models.arbitrage_calculator import ArbitrageCalculator

        calculator = ArbitrageCalculator()

        # 生成大量测试数据
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "code": f"51{i:04d}",
                "type": "ETF" if i % 2 == 0 else "LOF",
                "nav": 3.0 + i * 0.01,
                "price": 3.02 + i * 0.01,
            })

        # 测量计算时间
        start_time = time.time()
        for _ in range(10):
            for fund in large_dataset:
                calculator.calculate_arbitrage(
                    fund["type"],
                    fund["nav"],
                    fund["price"],
                    fund["code"]
                )
        elapsed_time = time.time() - start_time

        # 10次批量计算应该在0.5秒内完成
        assert elapsed_time < 0.5, f"计算性能过慢: {elapsed_time:.2f}秒"

    def test_fund_manager_refresh_performance(self, temp_db_path):
        """测试FundManager刷新性能"""
        from src.models.fund_manager import FundManager

        manager = FundManager(fetcher_type="mock")

        # 测量刷新时间（使用模拟数据）
        start_time = time.time()
        result = manager.refresh_all_data()
        elapsed_time = time.time() - start_time

        # 刷新应该在2秒内完成
        assert elapsed_time < 2.0, f"刷新性能过慢: {elapsed_time:.2f}秒"
        
        manager.close()

    def test_statistics_calculation_performance(self, temp_db_path):
        """测试统计计算性能"""
        from src.models.database import Database

        db = Database(str(temp_db_path))

        # 先保存一些数据
        test_data = []
        for i in range(50):
            test_data.append({
                "code": f"51{i:04d}",
                "name": f"测试基金{i}",
                "type": "ETF" if i % 2 == 0 else "LOF",
                "nav": Decimal(f"{3.0 + i * 0.01:.2f}"),
                "price": Decimal(f"{3.02 + i * 0.01:.2f}"),
                "volume": 1000000,
                "amount": 3000000.0,
                "timestamp": datetime.now().isoformat()
            })
        db.save_fund_data(test_data)

        # 测量统计计算时间
        start_time = time.time()
        for _ in range(20):
            stats = db.get_statistics()
        elapsed_time = time.time() - start_time

        # 20次统计计算应该在0.5秒内完成
        assert elapsed_time < 0.5, f"统计计算性能过慢: {elapsed_time:.2f}秒"


class TestMemoryUsage:
    """内存使用测试"""

    def test_large_dataset_memory(self, temp_db_path):
        """测试大数据集内存使用"""
        import sys
        from src.models.database import Database

        db = Database(str(temp_db_path))

        # 生成大数据集
        large_dataset = []
        for i in range(500):
            large_dataset.append({
                "code": f"51{i:04d}",
                "name": f"测试基金{i}",
                "type": "ETF",
                "nav": Decimal(f"{3.0 + i * 0.01:.2f}"),
                "price": Decimal(f"{3.02 + i * 0.01:.2f}"),
                "volume": 1000000,
                "amount": 3000000.0,
                "timestamp": datetime.now().isoformat()
            })

        # 保存数据
        db.save_fund_data(large_dataset)

        # 测量获取数据后的内存使用
        prices = db.get_fund_prices(limit=500)
        memory_size = sys.getsizeof(prices)

        # 500条数据应该小于1MB
        assert memory_size < 1024 * 1024, f"内存使用过高: {memory_size / 1024:.2f}KB"


class TestConcurrency:
    """并发性能测试"""

    def test_concurrent_database_access(self, temp_db_path):
        """测试并发数据库访问"""
        import threading
        from src.models.database import Database

        # 先创建一些数据
        db = Database(str(temp_db_path))
        test_data = []
        for i in range(10):
            test_data.append({
                "code": f"51{i:04d}",
                "name": f"测试基金{i}",
                "type": "ETF",
                "nav": Decimal("3.56"),
                "price": Decimal("3.58"),
                "volume": 1000000,
                "amount": 3000000.0,
                "timestamp": datetime.now().isoformat()
            })
        db.save_fund_data(test_data)

        errors = []
        results = []

        def worker(worker_id):
            try:
                local_db = Database(str(temp_db_path))
                for _ in range(10):
                    prices = local_db.get_fund_prices(limit=10)
                    results.append((worker_id, len(prices)))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # 启动5个并发线程
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误
        assert len(errors) == 0, f"并发错误: {errors}"
        # 验证所有结果
        assert len(results) == 50  # 5 threads * 10 iterations


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-slow"])
