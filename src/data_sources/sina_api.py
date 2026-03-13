"""
新浪财经 API 接口封装
比东方财富更稳定，限制更宽松
"""
import re
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SinaAPI:
    """新浪财经 API 接口"""

    def __init__(self):
        self.session = requests.Session()
        
        # 配置重试策略
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn/",
        })

    def get_realtime_quotes(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取基金实时行情
        
        新浪接口支持一次请求多个代码，非常高效
        格式: http://hq.sinajs.cn/list=sh510300,sz159915
        
        Args:
            fund_codes: 基金代码列表
            
        Returns:
            List[Dict]: 实时行情列表
        """
        if not fund_codes:
            return []
        
        results = []
        
        # 新浪接口一次最多支持约 800 个代码，我们分批处理
        batch_size = 100
        batches = [fund_codes[i:i + batch_size] for i in range(0, len(fund_codes), batch_size)]
        
        for batch in batches:
            batch_results = self._fetch_batch(batch)
            results.extend(batch_results)
            # 批次间短暂休眠
            if len(batches) > 1:
                time.sleep(0.1)
        
        return results

    def _fetch_batch(self, codes: List[str]) -> List[Dict[str, Any]]:
        """获取一批基金的行情"""
        # 构建代码列表，需要加上市场前缀
        symbols = []
        for code in codes:
            # 50/51/56/58/60 开头是上海 (sh), 其他是深圳 (sz)
            if code.startswith(("50", "51", "56", "58", "60")):
                symbols.append(f"sh{code}")
            else:
                symbols.append(f"sz{code}")
        
        symbols_str = ",".join(symbols)
        url = f"http://hq.sinajs.cn/list={symbols_str}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析返回数据
            # 格式: var hq_str_sh510300="沪深300ETF,3.530,3.528,3.535,3.540,3.520,3.530,3.531,123456789,435678901.00,...";
            content = response.text
            results = []
            
            for line in content.strip().split("\n"):
                if not line or '=""' in line:
                    continue
                    
                # 提取代码和数据
                match = re.match(r'var hq_str_(\w+)="(.*)";', line)
                if not match:
                    continue
                    
                symbol = match.group(1)
                data_str = match.group(2)
                
                if not data_str:
                    continue
                
                # 提取基金代码 (去掉 sh/sz 前缀)
                fund_code = symbol[2:]
                
                # 解析数据字段
                fields = data_str.split(",")
                if len(fields) < 10:
                    continue
                
                try:
                    # 新浪数据格式 (ETF/LOF):
                    # 0: 名称, 1: 开盘价, 2: 昨收, 3: 当前价, 4: 最高, 5: 最低
                    # 6: 买一价, 7: 卖一价, 8: 成交量(股), 9: 成交额
                    name = fields[0]
                    current_price = float(fields[3]) if fields[3] else 0.0
                    open_price = float(fields[1]) if fields[1] else 0.0
                    prev_close = float(fields[2]) if fields[2] else 0.0
                    high = float(fields[4]) if fields[4] else 0.0
                    low = float(fields[5]) if fields[5] else 0.0
                    volume = int(float(fields[8])) if fields[8] else 0
                    amount = float(fields[9]) if fields[9] else 0.0
                    
                    # 计算涨跌幅
                    change_pct = 0.0
                    if prev_close > 0:
                        change_pct = (current_price - prev_close) / prev_close * 100
                    
                    results.append({
                        "code": fund_code,
                        "name": name,
                        "price": current_price,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "prev_close": prev_close,
                        "change_pct": round(change_pct, 2),
                        "volume": volume,
                        "amount": amount,
                        "timestamp": datetime.now().isoformat()
                    })
                except (ValueError, IndexError) as e:
                    logger.debug(f"解析 {fund_code} 数据失败: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"新浪API批量获取行情失败: {e}")
            return []

    def get_realtime_quote(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """获取单个基金的实时行情"""
        results = self.get_realtime_quotes([fund_code])
        return results[0] if results else None
