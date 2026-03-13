"""
数据库模型单元测试
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from src.models.database import Database, get_database


class TestDatabase:
    """数据库类测试"""

    def test_init_with_temp_db(self, temp_db_path):
        """测试使用临时数据库初始化"""
        db = Database(str(temp_db_path))
        assert db.db_path == str(temp_db_path)

    def test_init_with_default_path(self):
        """测试使用默认路径初始化"""
        db = Database()
        # 默认路径应该包含用户主目录
        assert db.db_path is not None
        assert "fund_data.db" in db.db_path

    def test_create_tables(self, temp_db_path):
        """测试创建数据库表"""
        db = Database(str(temp_db_path))

        # 验证表是否存在
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        expected_tables = {"funds", "fund_prices", "arbitrage_opportunities", "user_settings"}
        assert all(table in tables for table in expected_tables)

    def test_save_fund(self, temp_db_path):
        """测试保存单个基金"""
        db = Database(str(temp_db_path))

        fund_data = {
            "code": "510300",
            "name": "沪深300ETF",
            "type": "ETF",
            "exchange": "SH",
            "currency": "CNY",
            "management_fee": 0.5
        }

        result = db.save_fund(fund_data)
        assert result is True

        # 验证数据已保存
        funds = db.get_funds()
        assert len(funds) == 1
        assert funds[0]["code"] == "510300"

    def test_save_fund_price(self, temp_db_path):
        """测试保存基金价格"""
        db = Database(str(temp_db_path))

        # 先保存基金
        fund_data = {"code": "510300", "name": "沪深300ETF", "type": "ETF"}
        db.save_fund(fund_data)

        # 保存价格
        price_data = {
            "fund_code": "510300",
            "nav": 3.56,
            "price": 3.58,
            "spread_pct": 0.56,
            "yield_pct": 0.43,
            "volume": 1000000,
            "amount": 3580000.0,
            "timestamp": datetime.now().isoformat()
        }

        result = db.save_fund_price(price_data)
        assert result is True

    def test_save_arbitrage_opportunity(self, temp_db_path):
        """测试保存套利机会"""
        db = Database(str(temp_db_path))

        opportunity_data = {
            "fund_code": "510300",
            "opportunity_type": "ETF",
            "nav": 3.56,
            "price": 3.58,
            "spread_pct": 0.56,
            "yield_pct": 0.43,
            "timestamp": datetime.now().isoformat()
        }

        result = db.save_arbitrage_opportunity(opportunity_data)
        assert result is True

    def test_save_fund_data(self, temp_db_path, mock_fund_data):
        """测试保存基金数据"""
        db = Database(str(temp_db_path))

        # 保存数据
        result = db.save_fund_data(mock_fund_data)
        assert result is True

        # 验证数据已保存
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # 检查funds表
            cursor.execute("SELECT COUNT(*) FROM funds")
            fund_count = cursor.fetchone()[0]
            assert fund_count == len(mock_fund_data)

            # 检查fund_prices表
            cursor.execute("SELECT COUNT(*) FROM fund_prices")
            price_count = cursor.fetchone()[0]
            assert price_count == len(mock_fund_data)

    def test_save_arbitrage_opportunities(self, temp_db_path):
        """测试批量保存套利机会"""
        db = Database(str(temp_db_path))

        # 先保存基金数据（因为get_arbitrage_opportunities使用了JOIN）
        db.save_fund({"code": "510300", "name": "沪深300ETF", "type": "ETF"})
        db.save_fund({"code": "161005", "name": "富国天惠LOF", "type": "LOF"})

        opportunities = [
            {
                "fund_code": "510300",
                "opportunity_type": "ETF",
                "yield_pct": 1.5,
                "nav": 3.56,
                "price": 3.58,
                "spread_pct": 0.56,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "fund_code": "161005",
                "opportunity_type": "LOF",
                "yield_pct": 2.0,
                "nav": 1.56,
                "price": 1.60,
                "spread_pct": 2.56,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        result = db.save_arbitrage_opportunities(opportunities)
        assert result is True

        # 验证数据
        saved = db.get_arbitrage_opportunities(limit=10)
        assert len(saved) == 2

    def test_get_funds(self, temp_db_path, mock_fund_data):
        """测试获取基金列表"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取所有基金
        funds = db.get_funds()
        assert len(funds) == len(mock_fund_data)

        # 验证数据格式
        for fund in funds:
            assert "code" in fund
            assert "name" in fund
            assert "type" in fund
            assert "exchange" in fund
            assert "currency" in fund

    def test_get_funds_by_type(self, temp_db_path, mock_fund_data):
        """测试按类型获取基金"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取ETF
        etf_funds = db.get_funds(fund_type="ETF")
        assert all(f["type"] == "ETF" for f in etf_funds)

        # 获取LOF
        lof_funds = db.get_funds(fund_type="LOF")
        assert all(f["type"] == "LOF" for f in lof_funds)

    def test_get_fund_prices(self, temp_db_path, mock_fund_data):
        """测试获取基金价格"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取价格数据
        prices = db.get_fund_prices(limit=10)
        assert len(prices) == len(mock_fund_data)

        # 验证价格数据格式
        for price in prices:
            assert "fund_code" in price  # 数据库列名
            assert "nav" in price
            assert "price" in price
            assert "volume" in price
            assert "amount" in price
            assert "timestamp" in price

    def test_get_latest_prices(self, temp_db_path, mock_fund_data):
        """测试获取最新价格"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取所有最新价格
        prices = db.get_latest_prices()
        assert len(prices) == len(mock_fund_data)

        # 获取指定代码的最新价格
        codes = [mock_fund_data[0]["code"]]
        specific_prices = db.get_latest_prices(fund_codes=codes)
        assert len(specific_prices) == 1

    def test_get_price_history(self, temp_db_path, mock_fund_data):
        """测试获取价格历史"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取历史数据
        history = db.get_price_history("510300", days=30)
        assert isinstance(history, list)

    def test_get_arbitrage_opportunities(self, temp_db_path, mock_fund_data):
        """测试获取套利机会"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 保存套利机会
        opportunities = [
            {
                "fund_code": "510300",
                "opportunity_type": "ETF",
                "yield_pct": Decimal("1.5"),
                "nav": Decimal("3.56"),
                "price": Decimal("3.58"),
                "spread_pct": Decimal("0.56"),
                "timestamp": datetime.now().isoformat(),
                "notes": "测试套利机会"
            }
        ]

        result = db.save_arbitrage_opportunities(opportunities)
        assert result is True

        # 获取套利机会
        saved_opportunities = db.get_arbitrage_opportunities(limit=10)
        assert len(saved_opportunities) == 1

        opportunity = saved_opportunities[0]
        assert opportunity["fund_code"] == "510300"
        assert opportunity["opportunity_type"] == "ETF"

    def test_get_setting(self, temp_db_path):
        """测试获取用户设置"""
        db = Database(str(temp_db_path))

        # 获取不存在的设置（使用默认值）
        value = db.get_setting("test_key", default="default_value")
        assert value == "default_value"

    def test_set_setting(self, temp_db_path):
        """测试设置用户配置"""
        db = Database(str(temp_db_path))

        # 设置配置
        result = db.set_setting("test_key", "test_value", description="测试配置")
        assert result is True

        # 获取配置
        value = db.get_setting("test_key")
        assert value == "test_value"

    def test_set_setting_update(self, temp_db_path):
        """测试更新用户配置"""
        db = Database(str(temp_db_path))

        # 设置初始值
        db.set_setting("test_key", "value1")

        # 更新值
        db.set_setting("test_key", "value2")

        # 获取最新值
        value = db.get_setting("test_key")
        assert value == "value2"

    def test_clean_old_data(self, temp_db_path, mock_fund_data):
        """测试清理旧数据"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        # 获取初始数据量
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fund_prices")
            initial_count = cursor.fetchone()[0]

        # 清理30天前的数据
        result = db.clean_old_data(days=30)
        assert result is True

        # 验证数据未删除（因为都是新数据）
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fund_prices")
            final_count = cursor.fetchone()[0]

        # 新数据不应该被删除
        assert final_count == initial_count

    def test_get_statistics(self, temp_db_path, mock_fund_data):
        """测试获取统计数据"""
        db = Database(str(temp_db_path))
        db.save_fund_data(mock_fund_data)

        stats = db.get_statistics()

        # 验证统计字段
        assert "total_funds" in stats
        assert "etf_count" in stats
        assert "lof_count" in stats
        assert "last_update" in stats

        # 应该有2个基金
        assert stats["total_funds"] == 2

        # 根据mock数据，应该有一个ETF和一个LOF
        assert stats["etf_count"] == 1
        assert stats["lof_count"] == 1

    def test_context_manager(self, temp_db_path):
        """测试上下文管理器"""
        with Database(str(temp_db_path)) as db:
            assert db is not None
            funds = db.get_funds()
            assert isinstance(funds, list)

    def test_close(self, temp_db_path):
        """测试关闭数据库"""
        db = Database(str(temp_db_path))
        # 不应抛出异常
        db.close()

    def test_error_handling(self, temp_db_path):
        """测试错误处理"""
        db = Database(str(temp_db_path))

        # 测试无效的基金数据
        invalid_data = [{"invalid": "data"}]  # 缺少必需字段
        result = db.save_fund_data(invalid_data)
        assert result is False  # 应该返回False表示失败

        # 数据库应该仍然可用
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1


class TestDatabaseSingleton:
    """数据库单例模式测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        import src.models.database as db_module
        db_module._db_instance = None

        db1 = get_database()
        db2 = get_database()

        assert db1 is db2

        # 清理
        db_module._db_instance = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])