"""
套利计算器单元测试 - 与实际ArbitrageCalculator实现对齐
"""
import pytest
from decimal import Decimal
from src.models.arbitrage_calculator import ArbitrageCalculator, get_calculator


class TestArbitrageCalculator:
    """套利计算器测试"""

    def test_init_with_default_fees(self):
        """测试使用默认费用初始化"""
        calculator = ArbitrageCalculator()
        assert "ETF" in calculator.fees
        assert "LOF" in calculator.fees

        # 验证默认费用值
        etf_fees = calculator.fees["ETF"]
        assert etf_fees["commission"] == Decimal("0.0003")
        assert etf_fees["stamp_tax"] == Decimal("0.001")
        assert etf_fees["total"] == Decimal("0.0013")

        lof_fees = calculator.fees["LOF"]
        assert lof_fees["subscription"] == Decimal("0.015")
        assert lof_fees["redemption"] == Decimal("0.005")
        assert lof_fees["total"] == Decimal("0.02")

    def test_init_with_custom_fees(self):
        """测试使用自定义费用初始化"""
        custom_fees = {
            "ETF": {
                "commission": Decimal("0.00025"),  # 更低的佣金
                "total": Decimal("0.00125"),       # 更新总费用
            }
        }

        calculator = ArbitrageCalculator(custom_fees=custom_fees)

        # 验证自定义费用
        etf_fees = calculator.fees["ETF"]
        assert etf_fees["commission"] == Decimal("0.00025")  # 自定义值
        assert etf_fees["stamp_tax"] == Decimal("0.001")      # 默认值保持不变
        assert etf_fees["total"] == Decimal("0.00125")        # 自定义值

        # LOF费用应保持默认
        assert calculator.fees["LOF"]["subscription"] == Decimal("0.015")

    def test_calculate_etf_arbitrage_premium(self):
        """测试计算ETF溢价套利"""
        calculator = ArbitrageCalculator()

        # 价格 > 净值 = 溢价
        nav = Decimal("3.56")
        price = Decimal("3.58")  # 价格高于净值

        result = calculator.calculate_etf_arbitrage(nav, price, "510300")

        assert result["fund_code"] == "510300"
        assert result["opportunity_type"] == "ETF"
        assert result["nav"] == float(nav)
        assert result["price"] == float(price)
        assert result["spread"] == pytest.approx(0.02, abs=0.001)

        # 验证收益率计算
        assert result["spread_pct"] > 0  # 价差百分比应为正
        assert "net_yield_pct" in result
        assert "fee_rate" in result

    def test_calculate_etf_arbitrage_discount(self):
        """测试计算ETF折价套利"""
        calculator = ArbitrageCalculator()

        # 价格 < 净值 = 折价
        nav = Decimal("3.58")
        price = Decimal("3.56")  # 价格低于净值

        result = calculator.calculate_etf_arbitrage(nav, price, "510300")

        assert result["opportunity_type"] == "ETF"
        assert result["spread"] == pytest.approx(-0.02, abs=0.001)  # 负价差
        assert result["spread_pct"] < 0  # 折价套利时，价差百分比为负

    def test_calculate_etf_no_arbitrage(self):
        """测试无套利机会的ETF"""
        calculator = ArbitrageCalculator()

        # 价格等于净值
        nav = Decimal("3.56")
        price = Decimal("3.56")

        result = calculator.calculate_etf_arbitrage(nav, price, "510300")

        assert result["spread"] == 0.0
        assert result["spread_pct"] == 0.0
        assert result["is_opportunity"] is False
        assert result["opportunity_level"] == "none"

    def test_calculate_lof_arbitrage_premium(self):
        """测试计算LOF溢价套利"""
        calculator = ArbitrageCalculator()

        # 价格 > 净值 = 溢价
        nav = Decimal("1.56")
        price = Decimal("1.58")

        result = calculator.calculate_lof_arbitrage(nav, price, "161005")

        assert result["fund_code"] == "161005"
        assert result["opportunity_type"] == "LOF"
        assert result["nav"] == float(nav)
        assert result["price"] == float(price)
        assert result["spread"] == pytest.approx(0.02, abs=0.001)
        assert result["direction"] == "场内溢价"

    def test_calculate_lof_arbitrage_discount(self):
        """测试计算LOF折价套利"""
        calculator = ArbitrageCalculator()

        # 价格 < 净值 = 折价
        nav = Decimal("1.58")
        price = Decimal("1.56")

        result = calculator.calculate_lof_arbitrage(nav, price, "161005")

        assert result["opportunity_type"] == "LOF"
        assert result["spread"] == pytest.approx(-0.02, abs=0.001)
        assert result["direction"] == "场内折价"

    def test_calculate_with_zero_nav(self):
        """测试净值为0的情况"""
        calculator = ArbitrageCalculator()

        # 净值为0应该安全处理
        nav = Decimal("0")
        price = Decimal("3.58")

        result = calculator.calculate_etf_arbitrage(nav, price, "510300")
        assert result["is_opportunity"] is False
        assert result["opportunity_level"] == "none"

    def test_calculate_with_negative_nav(self):
        """测试负净值情况"""
        calculator = ArbitrageCalculator()

        # 负净值应该安全处理
        nav = Decimal("-3.56")
        price = Decimal("3.58")

        result = calculator.calculate_etf_arbitrage(nav, price, "510300")
        assert result["is_opportunity"] is False

    def test_calculate_arbitrage_generic_etf(self):
        """测试通用套利计算接口 - ETF"""
        calculator = ArbitrageCalculator()

        result = calculator.calculate_arbitrage("ETF", 3.56, 3.58, "510300")

        assert result["opportunity_type"] == "ETF"
        assert result["nav"] == 3.56
        assert result["price"] == 3.58

    def test_calculate_arbitrage_generic_lof(self):
        """测试通用套利计算接口 - LOF"""
        calculator = ArbitrageCalculator()

        result = calculator.calculate_arbitrage("LOF", 1.56, 1.58, "161005")

        assert result["opportunity_type"] == "LOF"
        assert result["nav"] == 1.56
        assert result["price"] == 1.58
        assert "direction" in result

    def test_calculate_arbitrage_invalid_type(self):
        """测试无效基金类型"""
        calculator = ArbitrageCalculator()

        result = calculator.calculate_arbitrage("INVALID", 3.56, 3.58, "000000")

        assert result["is_opportunity"] is False

    def test_determine_opportunity_type_excellent(self):
        """测试判断优秀套利机会"""
        calculator = ArbitrageCalculator()

        # 净收益 >= 1% 应该是优秀机会
        result = calculator._determine_opportunity_type(Decimal("1.5"))
        assert result == "excellent"

    def test_determine_opportunity_type_good(self):
        """测试判断良好套利机会"""
        calculator = ArbitrageCalculator()

        # 净收益 >= 0.5% 应该是良好机会
        result = calculator._determine_opportunity_type(Decimal("0.7"))
        assert result == "good"

    def test_determine_opportunity_type_weak(self):
        """测试判断一般套利机会"""
        calculator = ArbitrageCalculator()

        # 净收益 >= 0.2% 应该是一般机会
        result = calculator._determine_opportunity_type(Decimal("0.3"))
        assert result == "weak"

    def test_determine_opportunity_type_none(self):
        """测试判断无套利机会"""
        calculator = ArbitrageCalculator()

        # 净收益 < 0.2% 应该没有机会
        result = calculator._determine_opportunity_type(Decimal("0.1"))
        assert result == "none"

    def test_update_fees(self):
        """测试更新交易费用"""
        calculator = ArbitrageCalculator()

        # 更新ETF费用
        new_fees = {"commission": Decimal("0.0002")}
        calculator.update_fees("ETF", new_fees)

        assert calculator.fees["ETF"]["commission"] == Decimal("0.0002")

    def test_update_fees_invalid_type(self):
        """测试更新无效类型的费用"""
        calculator = ArbitrageCalculator()

        # 尝试更新无效类型（不应该崩溃）
        calculator.update_fees("INVALID", {"commission": Decimal("0.0002")})

        # 原有费用不应改变
        assert "INVALID" not in calculator.fees

    def test_get_fee_summary(self):
        """测试获取费用汇总"""
        calculator = ArbitrageCalculator()

        summary = calculator.get_fee_summary()

        assert "ETF" in summary
        assert "LOF" in summary
        assert isinstance(summary["ETF"]["total"], float)
        assert isinstance(summary["LOF"]["total"], float)

    def test_get_opportunity_description(self):
        """测试获取机会描述"""
        calculator = ArbitrageCalculator()

        # 测试各种机会类型的描述
        excellent_desc = calculator._get_opportunity_description("excellent", Decimal("1.5"))
        assert "优秀" in excellent_desc

        good_desc = calculator._get_opportunity_description("good", Decimal("0.7"))
        assert "良好" in good_desc

        weak_desc = calculator._get_opportunity_description("weak", Decimal("0.3"))
        assert "一般" in weak_desc

        none_desc = calculator._get_opportunity_description("none", Decimal("0.1"))
        assert "无" in none_desc

    def test_create_empty_result(self):
        """测试创建空结果"""
        calculator = ArbitrageCalculator()

        result = calculator._create_empty_result("ETF", Decimal("3.56"), Decimal("3.58"))

        assert result["opportunity_type"] == "ETF"
        assert result["is_opportunity"] is False
        assert result["opportunity_level"] == "none"
        assert "计算失败" in result["description"]


class TestArbitrageCalculatorSingleton:
    """套利计算器单例模式测试"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        # 重置全局实例
        import src.models.arbitrage_calculator as ac
        ac._calculator_instance = None

        # 获取计算器实例
        calc1 = get_calculator()
        calc2 = get_calculator()

        # 应该是同一个实例
        assert calc1 is calc2

        # 清理
        ac._calculator_instance = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])