"""
测试数据工厂 - 集中管理测试数据生成
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import random
import string

class TestDataFactory:
    """测试数据工厂"""
    
    # 预定义的基金数据
    SAMPLE_ETF_FUNDS = [
        {"code": "510300", "name": "沪深300ETF", "type": "ETF"},
        {"code": "510500", "name": "中证500ETF", "type": "ETF"},
        {"code": "510050", "name": "上证50ETF", "type": "ETF"},
        {"code": "159915", "name": "创业板ETF", "type": "ETF"},
        {"code": "159919", "name": "沪深300ETF易方达", "type": "ETF"},
    ]
    
    SAMPLE_LOF_FUNDS = [
        {"code": "161005", "name": "富国天惠LOF", "type": "LOF"},
        {"code": "163402", "name": "兴全趋势LOF", "type": "LOF"},
        {"code": "160106", "name": "南方高增LOF", "type": "LOF"},
        {"code": "161903", "name": "万家行业优选LOF", "type": "LOF"},
    ]
    
    @classmethod
    def create_fund(
        cls,
        code: Optional[str] = None,
        name: Optional[str] = None,
        fund_type: str = "ETF",
        nav: Optional[float] = None,
        price: Optional[float] = None,
        volume: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建单个基金数据
        
        Args:
            code: 基金代码，为 None 时随机生成
            name: 基金名称
            fund_type: 基金类型 (ETF/LOF)
            nav: 净值，为 None 时随机生成
            price: 价格，为 None 时基于 nav 生成
            volume: 成交量
            timestamp: 时间戳
        """
        if code is None:
            prefix = "51" if fund_type == "ETF" else "16"
            code = prefix + "".join(random.choices(string.digits, k=4))
            
        if name is None:
            name = f"测试{fund_type}基金{code[-4:]}"
            
        if nav is None:
            nav = round(random.uniform(0.5, 5.0), 4)
            
        if price is None:
            # 生成带有一定溢价/折价的价格
            spread = random.uniform(-0.05, 0.05)  # -5% 到 +5%
            price = round(nav * (1 + spread), 4)
            
        if volume is None:
            volume = random.randint(10000, 10000000)
            
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        return {
            "code": code,
            "name": name,
            "type": fund_type,
            "nav": nav,
            "price": price,
            "volume": volume,
            "amount": round(volume * price, 2),
            "timestamp": timestamp,
        }
    
    @classmethod
    def create_fund_list(
        cls,
        count: int = 10,
        fund_type: str = "ETF",
        include_samples: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        创建基金数据列表
        
        Args:
            count: 要生成的基金数量
            fund_type: 基金类型
            include_samples: 是否包含预定义的样本数据
        """
        funds = []
        
        # 添加样本数据
        if include_samples:
            samples = cls.SAMPLE_ETF_FUNDS if fund_type == "ETF" else cls.SAMPLE_LOF_FUNDS
            for sample in samples[:count]:
                funds.append(cls.create_fund(
                    code=sample["code"],
                    name=sample["name"],
                    fund_type=fund_type,
                ))
                
        # 补充随机数据
        while len(funds) < count:
            funds.append(cls.create_fund(fund_type=fund_type))
            
        return funds[:count]
    
    @classmethod
    def create_price_history(
        cls,
        fund_code: str,
        days: int = 7,
        points_per_day: int = 48,  # 假设交易时间4小时，每5分钟一个点
        base_nav: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        创建价格历史数据
        
        Args:
            fund_code: 基金代码
            days: 天数
            points_per_day: 每天数据点数
            base_nav: 基准净值
        """
        history = []
        current_nav = base_nav
        
        for day_offset in range(days, 0, -1):
            date = (datetime.now() - timedelta(days=day_offset)).date()
            
            for point in range(points_per_day):
                # 模拟价格波动
                change = random.gauss(0, 0.002)  # 0.2% 标准差
                current_nav *= (1 + change)
                current_nav = max(0.1, current_nav)  # 防止负值
                
                # 溢价率波动
                spread_pct = random.gauss(0, 1.5)  # 1.5% 标准差
                price = current_nav * (1 + spread_pct / 100)
                
                # 时间戳
                hour = 9 + (point * 5) // 60
                minute = (point * 5) % 60
                if hour >= 11 and hour < 13:
                    continue  # 跳过午休时间
                if hour >= 15:
                    continue  # 跳过收盘后
                    
                timestamp = f"{date} {hour:02d}:{minute:02d}:00"
                
                history.append({
                    "fund_code": fund_code,
                    "nav": round(current_nav, 4),
                    "price": round(price, 4),
                    "spread_pct": round(spread_pct, 2),
                    "timestamp": timestamp,
                })
                
        return history
    
    @classmethod
    def create_arbitrage_result(
        cls,
        spread_pct: Optional[float] = None,
        is_opportunity: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """创建套利计算结果"""
        if spread_pct is None:
            spread_pct = random.uniform(-5, 5)
            
        if is_opportunity is None:
            is_opportunity = abs(spread_pct) > 1.5
            
        if is_opportunity:
            if abs(spread_pct) > 3:
                level = "excellent"
            elif abs(spread_pct) > 2:
                level = "good"
            else:
                level = "weak"
        else:
            level = "none"
            
        return {
            "spread_pct": round(spread_pct, 2),
            "net_yield_pct": round(spread_pct * 0.8, 2),  # 假设20%成本损耗
            "is_opportunity": is_opportunity,
            "opportunity_level": level,
            "description": f"溢价率 {spread_pct:.2f}%",
        }

# 便捷函数
def create_test_fund(**kwargs) -> Dict[str, Any]:
    """创建测试基金数据的便捷函数"""
    return TestDataFactory.create_fund(**kwargs)

def create_test_fund_list(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """创建测试基金列表的便捷函数"""
    return TestDataFactory.create_fund_list(count=count, **kwargs)
