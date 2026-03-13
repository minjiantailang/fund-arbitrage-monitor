"""
测试东方财富数据源集成
此脚本会发起真实网络请求，请确保网络连接正常
"""
import sys
import os
import logging
from pprint import pprint

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.data_fetcher import DataFetcherFactory

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_eastmoney_fetcher():
    print("=== 测试东方财富数据获取器 ===")
    
    # 1. 创建获取器
    fetcher = DataFetcherFactory.create_fetcher("eastmoney")
    print(f"创建获取器类型: {type(fetcher).__name__}")
    
    # 2. 获取基金列表
    print("\n[1] 获取基金列表...")
    etf_list = fetcher.fetch_fund_list("ETF")
    lof_list = fetcher.fetch_fund_list("LOF")
    print(f"ETF数量: {len(etf_list)}")
    print(f"LOF数量: {len(lof_list)}")
    
    if etf_list:
        print(f"示例ETF: {etf_list[0]}")
    
    # 3. 获取实时数据 (选取前5个ETF)
    if etf_list:
        sample_codes = [f["code"] for f in etf_list[:5]]
        print(f"\n[2] 获取实时ETF数据 ({len(sample_codes)}个)...")
        print(f"代码: {sample_codes}")
        
        etf_data = fetcher.fetch_etf_data(sample_codes)
        print(f"获取到 {len(etf_data)} 条数据")
        for item in etf_data:
            print(f"- {item['code']} {item['name']}: 价格={item['price']}, 净值={item['nav']}")
            
    # 4. 获取LOF数据
    if lof_list:
        sample_codes = [f["code"] for f in lof_list[:5]]
        print(f"\n[3] 获取实时LOF数据 ({len(sample_codes)}个)...")
        
        lof_data = fetcher.fetch_lof_data(sample_codes)
        for item in lof_data:
             print(f"- {item['code']} {item['name']}: 价格={item['price']}, 净值={item['nav']}")
             
    print("\n测试完成")

if __name__ == "__main__":
    try:
        test_eastmoney_fetcher()
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
