"""
基金管理器单元测试 - 与实际FundManager实现对齐
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.models.fund_manager import FundManager


class TestFundManager:
    """基金管理器测试"""

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_init(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试初始化"""
        # 模拟依赖
        mock_db = Mock()
        mock_fetcher = Mock()
        mock_calculator = Mock()

        mock_get_database.return_value = mock_db
        mock_get_fetcher.return_value = mock_fetcher
        mock_get_calculator.return_value = mock_calculator

        # 创建基金管理器
        manager = FundManager(fetcher_type="mock")

        # 验证依赖注入
        assert manager.db == mock_db
        assert manager.fetcher == mock_fetcher
        assert manager.calculator == mock_calculator
        assert manager._fund_cache == {}
        assert manager._price_cache == {}

        # 验证正确调用了获取器工厂
        mock_get_fetcher.assert_called_once_with("mock")

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_refresh_all_data_success(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试成功刷新所有数据"""
        # 模拟依赖
        mock_db = Mock()
        mock_fetcher = Mock()
        mock_calculator = Mock()

        mock_get_database.return_value = mock_db
        mock_get_fetcher.return_value = mock_fetcher
        mock_get_calculator.return_value = mock_calculator

        # 模拟ETF数据
        mock_etf_data = [
            {"code": "510300", "name": "沪深300ETF", "nav": 3.56, "price": 3.58, "volume": 1000000, "amount": 3580000.0}
        ]
        mock_fetcher.fetch_etf_data.return_value = mock_etf_data

        # 模拟LOF数据
        mock_lof_data = [
            {"code": "161005", "name": "富国天惠LOF", "nav": 1.56, "price": 1.58, "volume": 500000, "amount": 790000.0}
        ]
        mock_fetcher.fetch_lof_data.return_value = mock_lof_data

        # 模拟套利计算结果
        mock_calculator.calculate_arbitrage.return_value = {
            "spread_pct": 0.56,
            "net_yield_pct": 0.43,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "无显著套利机会"
        }

        # 模拟数据库保存成功
        mock_db.save_fund.return_value = True
        mock_db.save_fund_price.return_value = True

        # 创建管理器并刷新数据
        manager = FundManager()
        result = manager.refresh_all_data()

        # 验证结果
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        assert "total_funds" in result
        assert "etf_funds" in result
        assert "lof_funds" in result
        assert "elapsed_seconds" in result

        # 验证方法调用
        mock_fetcher.fetch_etf_data.assert_called_once()
        mock_fetcher.fetch_lof_data.assert_called_once()

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_refresh_all_data_failure(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试刷新数据失败"""
        # 模拟依赖
        mock_db = Mock()
        mock_fetcher = Mock()
        mock_get_database.return_value = mock_db
        mock_get_fetcher.return_value = mock_fetcher

        # 模拟获取器抛出异常
        mock_fetcher.fetch_etf_data.side_effect = Exception("API错误")

        # 创建管理器并刷新数据
        manager = FundManager()
        result = manager.refresh_all_data()

        # 验证错误处理
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "API错误" in result["error"]

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_get_funds(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试获取基金列表"""
        # 模拟依赖
        mock_db = Mock()
        mock_get_database.return_value = mock_db

        # 模拟数据库返回的基金列表
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "161005", "name": "富国天惠LOF", "type": "LOF"}
        ]
        mock_db.get_funds.return_value = mock_funds

        # 创建管理器并获取基金
        manager = FundManager()
        funds = manager.get_funds()

        # 验证结果
        assert len(funds) == 2
        assert funds == mock_funds
        mock_db.get_funds.assert_called_once_with(None)

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_get_funds_with_type_filter(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试使用类型筛选获取基金"""
        # 模拟依赖
        mock_db = Mock()
        mock_get_database.return_value = mock_db

        # 模拟数据库返回ETF基金
        mock_etf_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "510500", "name": "中证500ETF", "type": "ETF"},
        ]
        mock_db.get_funds.return_value = mock_etf_funds

        # 创建管理器
        manager = FundManager()

        # 测试ETF筛选
        etf_funds = manager.get_funds(fund_type="ETF")
        assert len(etf_funds) == 2
        mock_db.get_funds.assert_called_with("ETF")

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_get_latest_prices(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试获取最新价格"""
        # 模拟依赖
        mock_db = Mock()
        mock_calculator = Mock()
        mock_get_database.return_value = mock_db
        mock_get_calculator.return_value = mock_calculator

        # 模拟数据库返回价格
        mock_prices = [
            {
                "fund_code": "510300",
                "type": "ETF",
                "nav": 3.56,
                "price": 3.58,
                "timestamp": "2026-01-30T12:00:00"
            }
        ]
        mock_db.get_latest_prices.return_value = mock_prices

        # 模拟计算器返回套利结果
        mock_calculator.calculate_arbitrage.return_value = {
            "spread_pct": 0.56,
            "net_yield_pct": 0.43,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "无显著套利机会"
        }

        # 创建管理器并获取价格
        manager = FundManager()
        prices = manager.get_latest_prices()

        # 验证结果
        assert len(prices) == 1
        price_data = prices[0]
        assert price_data["fund_code"] == "510300"
        assert "spread_pct" in price_data
        assert "yield_pct" in price_data

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_get_statistics(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试获取统计数据"""
        # 模拟依赖
        mock_db = Mock()
        mock_calculator = Mock()
        mock_get_database.return_value = mock_db
        mock_get_calculator.return_value = mock_calculator

        # 模拟数据库返回价格数据
        mock_prices = [
            {"fund_code": "510300", "type": "ETF", "nav": 3.56, "price": 3.58, "timestamp": "2026-01-30T12:00:00"},
            {"fund_code": "510500", "type": "ETF", "nav": 5.23, "price": 5.20, "timestamp": "2026-01-30T12:00:00"},
            {"fund_code": "161005", "type": "LOF", "nav": 1.56, "price": 1.58, "timestamp": "2026-01-30T12:00:00"},
        ]
        mock_db.get_latest_prices.return_value = mock_prices

        # 模拟计算器返回套利结果
        mock_calculator.calculate_arbitrage.return_value = {
            "spread_pct": 0.56,
            "net_yield_pct": 0.43,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "无显著套利机会"
        }

        # 创建管理器并获取统计
        manager = FundManager()
        stats = manager.get_statistics()

        # 验证结果
        assert "total_funds" in stats
        assert "etf_count" in stats
        assert "lof_count" in stats
        assert "opportunity_count" in stats
        assert "avg_spread" in stats
        assert "max_spread" in stats
        assert "min_spread" in stats

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_search_funds(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试搜索基金"""
        # 模拟依赖
        mock_db = Mock()
        mock_get_database.return_value = mock_db

        # 模拟数据库返回所有基金
        mock_funds = [
            {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
            {"code": "510500", "name": "中证500ETF", "type": "ETF"},
            {"code": "161005", "name": "富国天惠成长混合(LOF)", "type": "LOF"}
        ]
        mock_db.get_funds.return_value = mock_funds

        # 创建管理器
        manager = FundManager()

        # 测试代码搜索
        code_results = manager.search_funds(keyword="5103")
        assert len(code_results) == 1
        assert code_results[0]["code"] == "510300"

        # 测试名称搜索
        name_results = manager.search_funds(keyword="300")
        assert len(name_results) == 1
        assert "300" in name_results[0]["name"]

        # 测试全名搜索
        full_results = manager.search_funds(keyword="富国天惠")
        assert len(full_results) == 1
        assert "富国天惠" in full_results[0]["name"]

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_filter_funds_by_spread(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试按价差筛选基金"""
        # 模拟依赖
        mock_db = Mock()
        mock_calculator = Mock()
        mock_get_database.return_value = mock_db
        mock_get_calculator.return_value = mock_calculator

        # 模拟数据库返回价格数据
        mock_prices = [
            {"fund_code": "510300", "type": "ETF", "nav": 3.56, "price": 3.58, "spread_pct": 0.56},
            {"fund_code": "510500", "type": "ETF", "nav": 5.23, "price": 5.20, "spread_pct": -0.57},
            {"fund_code": "161005", "type": "LOF", "nav": 1.56, "price": 1.60, "spread_pct": 2.56},
        ]
        mock_db.get_latest_prices.return_value = mock_prices

        # 模拟计算器返回
        mock_calculator.calculate_arbitrage.side_effect = lambda ft, nav, price, code: {
            "spread_pct": mock_prices[[p["fund_code"] for p in mock_prices].index(code)]["spread_pct"],
            "net_yield_pct": 0.4,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "测试"
        }

        # 创建管理器
        manager = FundManager()

        # 测试价差筛选
        filtered = manager.filter_funds_by_spread(min_spread=0.0, max_spread=1.0)
        # 应该只返回spread_pct在0-1%范围内的基金
        assert len(filtered) == 1
        assert filtered[0]["fund_code"] == "510300"

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_export_to_csv(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试导出CSV"""
        import tempfile
        import os

        # 模拟依赖
        mock_db = Mock()
        mock_calculator = Mock()
        mock_get_database.return_value = mock_db
        mock_get_calculator.return_value = mock_calculator

        # 模拟数据库返回价格数据
        mock_prices = [
            {"fund_code": "510300", "type": "ETF", "nav": 3.56, "price": 3.58, "timestamp": "2026-01-30T12:00:00"},
        ]
        mock_db.get_latest_prices.return_value = mock_prices

        # 模拟计算器返回
        mock_calculator.calculate_arbitrage.return_value = {
            "spread_pct": 0.56,
            "net_yield_pct": 0.43,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "测试"
        }

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            # 创建管理器并导出
            manager = FundManager()
            result = manager.export_to_csv(temp_path)

            # 验证结果
            assert result is True
            assert os.path.exists(temp_path)

            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert "fund_code" in content
                assert "510300" in content

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_close(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试关闭资源"""
        # 模拟依赖
        mock_db = Mock()
        mock_fetcher = Mock()
        mock_get_database.return_value = mock_db
        mock_get_fetcher.return_value = mock_fetcher

        # 创建管理器
        manager = FundManager()

        # 关闭资源
        manager.close()

        # 验证关闭方法被调用
        mock_fetcher.close.assert_called_once()
        mock_db.close.assert_called_once()

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_refresh_fund_data(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试刷新指定基金数据"""
        # 模拟依赖
        mock_db = Mock()
        mock_fetcher = Mock()
        mock_calculator = Mock()

        mock_get_database.return_value = mock_db
        mock_get_fetcher.return_value = mock_fetcher
        mock_get_calculator.return_value = mock_calculator

        # 模拟ETF数据
        mock_etf_data = [
            {"code": "510300", "name": "沪深300ETF", "nav": 3.56, "price": 3.58, "volume": 1000000, "amount": 3580000.0}
        ]
        mock_fetcher.fetch_etf_data.return_value = mock_etf_data

        # 模拟套利计算结果
        mock_calculator.calculate_arbitrage.return_value = {
            "spread_pct": 0.56,
            "net_yield_pct": 0.43,
            "is_opportunity": False,
            "opportunity_level": "none",
            "description": "无显著套利机会"
        }

        # 模拟数据库保存成功
        mock_db.save_fund.return_value = True
        mock_db.save_fund_price.return_value = True

        # 创建管理器并刷新指定基金
        manager = FundManager()
        result = manager.refresh_fund_data(["510300"])

        # 验证结果
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        assert "processed_funds" in result

    @patch('src.models.fund_manager.get_database')
    @patch('src.models.fund_manager.get_data_fetcher')
    @patch('src.models.fund_manager.get_calculator')
    def test_get_price_history(self, mock_get_calculator, mock_get_fetcher, mock_get_database):
        """测试获取价格历史"""
        # 模拟依赖
        mock_db = Mock()
        mock_get_database.return_value = mock_db

        # 模拟数据库返回历史数据
        mock_history = [
            {"fund_code": "510300", "nav": 3.56, "price": 3.58, "timestamp": "2026-01-30T12:00:00"},
            {"fund_code": "510300", "nav": 3.55, "price": 3.57, "timestamp": "2026-01-29T12:00:00"},
        ]
        mock_db.get_price_history.return_value = mock_history

        # 创建管理器并获取历史
        manager = FundManager()
        history = manager.get_price_history("510300", days=30)

        # 验证结果
        assert len(history) == 2
        mock_db.get_price_history.assert_called_once_with("510300", 30)


class TestFundManagerSingleton:
    """基金管理器单例模式测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        # 重置全局实例
        import src.models.fund_manager as fm
        fm._manager_instance = None

        # 获取管理器实例
        manager1 = fm.get_fund_manager()
        manager2 = fm.get_fund_manager()

        # 应该是同一个实例（单例）
        assert manager1 is manager2

        # 清理
        fm._manager_instance = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])