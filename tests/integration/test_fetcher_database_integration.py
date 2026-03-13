"""
数据获取器与数据库集成测试
"""
import pytest
import time
from decimal import Decimal
from datetime import datetime
from src.models.database import Database
from src.models.data_fetcher import MockDataFetcher


pytestmark = pytest.mark.integration


class TestFetcherDatabaseIntegration:
    """数据获取器与数据库集成测试"""

    def test_fetch_and_save_workflow(self, temp_db_path):
        """测试获取数据并保存到数据库的工作流"""
        # 初始化组件
        fetcher = MockDataFetcher()
        db = Database(str(temp_db_path))

        # 步骤1: 获取ETF数据
        etf_data = fetcher.fetch_etf_data([])  # 空列表获取所有
        assert len(etf_data) > 0

        # 步骤2: 获取LOF数据
        lof_data = fetcher.fetch_lof_data([])  # 空列表获取所有
        assert len(lof_data) > 0

        # 步骤3: 合并所有数据
        all_data = etf_data + lof_data
        assert len(all_data) > 0

        # 步骤4: 转换数据格式以匹配数据库要求
        fund_data = []
        for item in all_data:
            fund_data.append({
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "nav": Decimal(str(item["nav"])),
                "price": Decimal(str(item["price"])),
                "volume": item.get("volume", 0),
                "amount": float(item.get("amount", 0)),
                "timestamp": item.get("timestamp", datetime.now().isoformat())
            })

        # 步骤5: 保存数据到数据库
        save_result = db.save_fund_data(fund_data)
        assert save_result is True

        # 步骤6: 验证数据库中的数据
        saved_prices = db.get_fund_prices(limit=100)
        assert len(saved_prices) == len(fund_data)

    def test_refresh_and_update_data(self, temp_db_path):
        """测试刷新和更新数据"""
        fetcher = MockDataFetcher(cache_duration=0)  # 禁用缓存
        db = Database(str(temp_db_path))

        # 第一次获取和保存
        etf_data = fetcher.fetch_etf_data([])
        fund_data_1 = [
            {
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "nav": Decimal(str(item["nav"])),
                "price": Decimal(str(item["price"])),
                "volume": item.get("volume", 0),
                "amount": float(item.get("amount", 0)),
                "timestamp": datetime.now().isoformat()
            }
            for item in etf_data
        ]
        db.save_fund_data(fund_data_1)

        # 第二次获取和保存（模拟刷新）
        etf_data_2 = fetcher.fetch_etf_data([])
        fund_data_2 = [
            {
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "nav": Decimal(str(item["nav"])),
                "price": Decimal(str(item["price"])),
                "volume": item.get("volume", 0),
                "amount": float(item.get("amount", 0)),
                "timestamp": datetime.now().isoformat()
            }
            for item in etf_data_2
        ]
        db.save_fund_data(fund_data_2)

        # 获取数据库中的所有价格记录
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fund_prices")
            total_prices = cursor.fetchone()[0]

        # 应该有两次保存的记录
        assert total_prices == len(fund_data_1) + len(fund_data_2)

    def test_selective_fetch_and_save(self, temp_db_path):
        """测试选择性获取和保存"""
        fetcher = MockDataFetcher()
        db = Database(str(temp_db_path))

        # 获取所有基金列表
        all_funds = fetcher.fetch_fund_list("ALL")
        assert len(all_funds) > 0

        # 选择部分基金代码
        selected_codes = [fund["code"] for fund in all_funds[:3]]  # 前3个

        # 获取选定基金的ETF和LOF数据
        etf_prices = fetcher.fetch_etf_data(selected_codes)
        lof_prices = fetcher.fetch_lof_data(selected_codes)
        selected_prices = etf_prices + lof_prices

        # 转换格式
        fund_data = [
            {
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "nav": Decimal(str(item["nav"])),
                "price": Decimal(str(item["price"])),
                "volume": item.get("volume", 0),
                "amount": float(item.get("amount", 0)),
                "timestamp": datetime.now().isoformat()
            }
            for item in selected_prices if item["code"] in selected_codes
        ]

        # 保存选定数据
        if fund_data:
            db.save_fund_data(fund_data)

            # 验证只保存了选定数据
            saved_prices = db.get_fund_prices(limit=100)
            assert len(saved_prices) == len(fund_data)

    def test_fund_list_integration(self, temp_db_path):
        """测试基金列表集成"""
        fetcher = MockDataFetcher()
        db = Database(str(temp_db_path))

        # 获取ETF列表
        etf_list = fetcher.fetch_fund_list("ETF")
        assert len(etf_list) > 0

        # 获取LOF列表
        lof_list = fetcher.fetch_fund_list("LOF")
        assert len(lof_list) > 0

        # 获取所有列表
        all_list = fetcher.fetch_fund_list("ALL")
        assert len(all_list) >= len(etf_list)
        assert len(all_list) >= len(lof_list)

        # 验证列表包含必要信息
        for fund in all_list[:3]:
            assert "code" in fund
            assert "name" in fund
            assert "type" in fund

    def test_cache_integration(self, temp_db_path):
        """测试缓存集成"""
        fetcher = MockDataFetcher(cache_duration=2)  # 2秒缓存
        db = Database(str(temp_db_path))

        # 第一次获取（应该从源获取）
        start_time = time.time()
        prices1 = fetcher.fetch_etf_data([])
        first_fetch_time = time.time() - start_time

        # 立即第二次获取（应该从缓存获取）
        start_time = time.time()
        prices2 = fetcher.fetch_etf_data([])
        second_fetch_time = time.time() - start_time

        # 缓存获取应该更快
        assert second_fetch_time < first_fetch_time

        # 数据应该相同（缓存生效）
        assert len(prices1) == len(prices2)

    def test_error_handling_integration(self, temp_db_path):
        """测试集成错误处理"""
        fetcher = MockDataFetcher()
        db = Database(str(temp_db_path))

        # 测试空代码列表（应该返回所有数据）
        all_prices = fetcher.fetch_etf_data([])
        assert len(all_prices) > 0

        # 测试保存空数据到数据库
        save_result = db.save_fund_data([])
        # 空数据应该返回True或False，但不应该崩溃
        assert isinstance(save_result, bool)

    def test_performance_integration(self, temp_db_path):
        """测试集成性能"""
        fetcher = MockDataFetcher(cache_duration=0)  # 禁用缓存
        db = Database(str(temp_db_path))

        start_time = time.time()

        # 执行完整工作流多次
        for i in range(3):
            # 获取数据
            etf_data = fetcher.fetch_etf_data([])
            lof_data = fetcher.fetch_lof_data([])

            # 转换格式
            fund_data = [
                {
                    "code": item["code"],
                    "name": item["name"],
                    "type": item["type"],
                    "nav": Decimal(str(item["nav"])),
                    "price": Decimal(str(item["price"])),
                    "volume": item.get("volume", 0),
                    "amount": float(item.get("amount", 0)),
                    "timestamp": datetime.now().isoformat()
                }
                for item in etf_data + lof_data
            ]

            # 保存到数据库
            db.save_fund_data(fund_data)

            # 从数据库读取
            saved_prices = db.get_fund_prices(limit=100)
            assert len(saved_prices) > 0

        end_time = time.time()
        total_time = end_time - start_time

        # 3次完整工作流应该在合理时间内完成
        assert total_time < 15.0, f"性能测试耗时过长: {total_time:.2f}秒"

    def test_data_types_and_conversions(self, temp_db_path):
        """测试数据类型和转换"""
        fetcher = MockDataFetcher()
        db = Database(str(temp_db_path))

        # 获取数据
        etf_data = fetcher.fetch_etf_data([])

        # 验证原始数据格式
        for item in etf_data:
            assert "code" in item
            assert "nav" in item
            assert "price" in item

        # 转换并保存
        fund_data = [
            {
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "nav": Decimal(str(item["nav"])),
                "price": Decimal(str(item["price"])),
                "volume": item.get("volume", 0),
                "amount": float(item.get("amount", 0)),
                "timestamp": datetime.now().isoformat()
            }
            for item in etf_data
        ]

        save_result = db.save_fund_data(fund_data)
        assert save_result is True

        # 从数据库读取并验证
        saved_prices = db.get_fund_prices(limit=100)
        for saved_price in saved_prices:
            assert "fund_code" in saved_price
            assert "nav" in saved_price
            assert "price" in saved_price

    def test_large_dataset_handling(self, temp_db_path):
        """测试大数据集处理"""
        fetcher = MockDataFetcher(cache_duration=0)
        db = Database(str(temp_db_path))

        # 多次获取和保存数据
        total_saved = 0
        for i in range(5):
            etf_data = fetcher.fetch_etf_data([])
            lof_data = fetcher.fetch_lof_data([])

            fund_data = [
                {
                    "code": item["code"],
                    "name": item["name"],
                    "type": item["type"],
                    "nav": Decimal(str(item["nav"])),
                    "price": Decimal(str(item["price"])),
                    "volume": item.get("volume", 0),
                    "amount": float(item.get("amount", 0)),
                    "timestamp": datetime.now().isoformat()
                }
                for item in etf_data + lof_data
            ]

            db.save_fund_data(fund_data)
            total_saved += len(fund_data)

        # 验证保存的数据量
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fund_prices")
            count = cursor.fetchone()[0]

        assert count == total_saved


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--run-integration"])