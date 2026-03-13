
import logging
import sys
import os
import time

# 添加 src 到路径
sys.path.append(os.path.join(os.getcwd()))

from src.models.data_fetcher import EastMoneyDataFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_161226():
    fetcher = EastMoneyDataFetcher()
    
    # 1. 验证 fetch_lof_data 是否返回 161226
    logger.info("测试 fetch_lof_data...")
    # 强制只获取 161226，看看fetch_lof_data怎么处理
    # 注意：fetch_lof_data 会先 fetch_fund_list，然后 filter
    # 但我们也可以直接传 code
    
    # 手动填充一下列表缓存，避免等待太久（或者就让它下）
    # 为了真实模拟，我们直接调用 fetch_lof_data 并传入全量列表（None）太慢
    # 我们先验证 API 是否能获取到
    
    # 既然之前验证了 API 能获取到，现在验证 Fetcher 逻辑
    # 只有当 161226 在 fund_list 缓存里时，它才会被处理
    
    fetcher._ensure_fund_list()
    lof_list = fetcher._fund_list_cache.get("LOF", [])
    found = False
    for f in lof_list:
        if f["code"] == "161226":
            logger.info(f"列表中存在 161226: {f}")
            found = True
            break
            
    if not found:
        logger.error("列表中未找到 161226！分类逻辑可能有误")
        return
        
    fetcher._ensure_nav_cache()
    
    logger.info("获取 161226 数据...")
    results = fetcher.fetch_lof_data(["161226"])
    
    if results:
        logger.info(f"成功获取数据: {results[0]}")
    else:
        logger.error("fetch_lof_data 返回空！")

if __name__ == "__main__":
    test_161226()
