"""
数据库与计算器集成测试
"""
import pytest
from decimal import Decimal
from datetime import datetime
from src.models.database import Database
from src.models.arbitrage_calculator import ArbitrageCalculator


pytestmark = pytest.mark.integration


class TestDatabaseCalculatorIntegration:
    """数据库与计算器集成测试"""

    def test_save_and_calculate_arbitrage(self, temp_db_path, mock_fund_data):
        """测试保存数据并计算套利"""
        # 初始化组件
        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 保存基金数据到数据库
        save_result = db.save_fund_data(mock_fund_data)
        assert save_result is True

        # 从数据库获取价格数据
        prices = db.get_fund_prices(limit=10)
        assert len(prices) == len(mock_fund_data)

        # 使用计算器计算每个基金的套利机会
        opportunities = []
        for price in prices:
            result = calculator.calculate_arbitrage(
                fund_type=price["type"],
                nav=float(price["nav"]),
                price=float(price["price"]),
                fund_code=price["fund_code"]
            )
            result["fund_code"] = price["fund_code"]
            opportunities.append(result)

        assert len(opportunities) == len(prices)

        # 验证套利机会数据格式
        for opportunity in opportunities:
            assert "fund_code" in opportunity
            assert "spread" in opportunity
            assert "spread_pct" in opportunity
            assert "is_opportunity" in opportunity

    def test_data_consistency_through_workflow(self, temp_db_path):
        """测试完整工作流的数据一致性"""
        # 创建测试数据
        test_fund_data = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": Decimal("3.56"),
                "price": Decimal("3.58"),
                "volume": 1000000,
                "amount": 3580000.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "code": "161005",
                "name": "富国天惠LOF",
                "type": "LOF",
                "nav": Decimal("1.56"),
                "price": Decimal("1.58"),
                "volume": 500000,
                "amount": 790000.0,
                "timestamp": datetime.now().isoformat()
            }
        ]

        # 初始化组件
        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 步骤1: 保存数据
        db.save_fund_data(test_fund_data)

        # 步骤2: 获取数据
        retrieved_prices = db.get_fund_prices(limit=10)
        assert len(retrieved_prices) == 2

        # 步骤3: 计算套利
        opportunities = []
        for price in retrieved_prices:
            result = calculator.calculate_arbitrage(
                fund_type=price["type"],
                nav=float(price["nav"]),
                price=float(price["price"]),
                fund_code=price["fund_code"]
            )
            opportunities.append(result)
        assert len(opportunities) == 2

        # 步骤4: 获取统计信息
        stats = db.get_statistics()
        assert stats["total_funds"] == 2
        assert stats["etf_count"] == 1
        assert stats["lof_count"] == 1

    def test_multiple_calculations_same_data(self, temp_db_path, mock_fund_data):
        """测试相同数据的多次计算一致性"""
        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 保存数据
        db.save_fund_data(mock_fund_data)

        # 多次获取和计算，结果应该一致
        results = []
        for _ in range(3):
            prices = db.get_fund_prices(limit=10)
            opportunities = []
            for price in prices:
                result = calculator.calculate_arbitrage(
                    fund_type=price["type"],
                    nav=float(price["nav"]),
                    price=float(price["price"]),
                    fund_code=price["fund_code"]
                )
                opportunities.append(result)
            results.append(opportunities)

        # 验证多次计算结果一致
        for i in range(1, len(results)):
            assert len(results[i]) == len(results[0])
            for result1, result2 in zip(results[0], results[i]):
                # 主要字段应该一致
                assert result1["is_opportunity"] == result2["is_opportunity"]
                assert abs(result1["spread_pct"] - result2["spread_pct"]) < 0.01

    def test_error_recovery_in_workflow(self, temp_db_path):
        """测试工作流中的错误恢复"""
        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 测试数据：一个有效，一个无效（零价格）
        mixed_data = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": Decimal("3.56"),
                "price": Decimal("3.58"),
                "volume": 1000000,
                "amount": 3580000.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "code": "INVALID",
                "name": "无效基金",
                "type": "ETF",
                "nav": Decimal("0"),  # 无效净值
                "price": Decimal("0"),  # 无效价格
                "volume": 0,
                "amount": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        ]

        # 保存应该处理无效数据
        save_result = db.save_fund_data(mixed_data)
        assert save_result is True

        # 获取数据
        prices = db.get_fund_prices(limit=10)

        # 应该返回所有保存的数据
        assert len(prices) >= 1

    def test_concurrent_access_simulation(self, temp_db_path, mock_fund_data):
        """测试模拟并发访问"""
        import threading

        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 先保存一些数据
        db.save_fund_data(mock_fund_data)

        results = []
        errors = []

        def worker(worker_id):
            """工作线程函数"""
            try:
                # 每个线程独立工作
                local_db = Database(str(temp_db_path))
                local_calculator = ArbitrageCalculator()

                # 获取数据
                prices = local_db.get_fund_prices(limit=10)

                # 计算套利
                opportunities = []
                for price in prices:
                    result = local_calculator.calculate_arbitrage(
                        fund_type=price["type"],
                        nav=float(price["nav"]),
                        price=float(price["price"]),
                        fund_code=price["fund_code"]
                    )
                    opportunities.append(result)

                # 保存结果
                results.append((worker_id, len(opportunities)))

            except Exception as e:
                errors.append((worker_id, str(e)))

        # 创建多个线程
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误
        assert len(errors) == 0, f"并发访问错误: {errors}"

        # 验证所有线程都成功
        assert len(results) == 3
        for worker_id, opp_count in results:
            assert opp_count == len(mock_fund_data)

    def test_data_persistence_across_instances(self, temp_db_path, mock_fund_data):
        """测试跨实例的数据持久性"""
        # 第一个实例保存数据
        db1 = Database(str(temp_db_path))
        save_result = db1.save_fund_data(mock_fund_data)
        assert save_result is True

        # 第二个实例读取数据
        db2 = Database(str(temp_db_path))
        prices = db2.get_fund_prices(limit=10)

        # 验证数据一致性
        assert len(prices) == len(mock_fund_data)

        for price_data in prices:
            # 找到对应的原始数据
            original = next(
                (f for f in mock_fund_data if f["code"] == price_data["fund_code"]),
                None
            )
            assert original is not None
            assert price_data["type"] == original["type"]

    def test_calculation_with_different_fund_types(self, temp_db_path):
        """测试使用不同基金类型的计算"""
        db = Database(str(temp_db_path))
        calculator = ArbitrageCalculator()

        # 创建ETF和LOF数据
        test_data = [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "type": "ETF",
                "nav": Decimal("3.56"),
                "price": Decimal("3.60"),  # 溢价
                "volume": 1000000,
                "amount": 3600000.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "code": "161005",
                "name": "富国天惠LOF",
                "type": "LOF",
                "nav": Decimal("1.56"),
                "price": Decimal("1.50"),  # 折价
                "volume": 500000,
                "amount": 750000.0,
                "timestamp": datetime.now().isoformat()
            }
        ]

        # 保存数据
        db.save_fund_data(test_data)

        # 获取数据并计算
        prices = db.get_fund_prices(limit=10)

        for price in prices:
            result = calculator.calculate_arbitrage(
                fund_type=price["type"],
                nav=float(price["nav"]),
                price=float(price["price"]),
                fund_code=price["fund_code"]
            )

            # 验证结果格式
            assert "spread" in result
            assert "spread_pct" in result
            assert "fee_rate" in result

            # ETF溢价应该显示正价差
            if price["fund_code"] == "510300":
                assert result["spread_pct"] > 0
            # LOF折价应该显示负价差
            elif price["fund_code"] == "161005":
                assert result["spread_pct"] < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-integration"])