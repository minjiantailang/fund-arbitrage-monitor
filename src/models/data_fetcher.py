"""
数据获取器 - 从 API 获取基金数据
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
from decimal import Decimal

from src.data_sources.eastmoney_api import EastMoneyAPI
from src.data_sources.sina_api import SinaAPI

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器基类"""

    def __init__(self, cache_duration: int = 300):
        """
        初始化数据获取器

        Args:
            cache_duration: 缓存持续时间（秒）
        """
        self.cache_duration = cache_duration
        self._cache: Dict[str, Tuple[float, Any]] = {}  # key -> (timestamp, data)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        })

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self.cache_duration:
                logger.debug(f"从缓存获取数据: {key}")
                return data
            else:
                del self._cache[key]  # 缓存过期
        return None

    def _save_to_cache(self, key: str, data: Any):
        """保存数据到缓存"""
        self._cache[key] = (time.time(), data)

    def fetch_etf_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取ETF数据（需子类实现）

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[Dict]: ETF数据列表
        """
        raise NotImplementedError

    def fetch_lof_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取LOF数据（需子类实现）

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[Dict]: LOF数据列表
        """
        raise NotImplementedError

    def fetch_fund_list(self, fund_type: str) -> List[Dict[str, Any]]:
        """
        获取基金列表（需子类实现）

        Args:
            fund_type: 基金类型（ETF/LOF）

        Returns:
            List[Dict]: 基金列表
        """
        raise NotImplementedError

    def close(self):
        """关闭会话"""
        self.session.close()



from src.models.database import get_database

# 模块级全局缓存变量，确保跨实例共享（尽管单例模式下实例唯一，但作为双重保障）
_FUND_LIST_CACHE: Dict[str, List[Dict]] = {}
_FUND_LIST_CACHE_TIME: float = 0
_NAV_CACHE: Dict[str, float] = {}
_NAV_CACHE_TIME: float = 0

class EastMoneyDataFetcher(DataFetcher):
    """数据获取器 (单例模式) - 优先使用新浪 API，东财作为备用"""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_duration: int = 300):
        # 确保只初始化一次
        if not hasattr(self, '_initialized') or not self._initialized:
            super().__init__(cache_duration)
            self.api = EastMoneyAPI()  # 东财用于基金列表和净值
            self.sina_api = SinaAPI()  # 新浪用于行情数据（主要）
            self.db = get_database()
            self._initialized = True
            logger.info("创建数据获取器（优先使用新浪 API）")
            
            # 使用全局缓存而非实例变量
            global _FUND_LIST_CACHE, _NAV_CACHE
            self._fund_list_cache = _FUND_LIST_CACHE
            self._nav_cache = _NAV_CACHE

        
    def _ensure_fund_list(self):
        """确保基金列表已加载（内存缓存 -> 24小时DB缓存）"""
        global _FUND_LIST_CACHE, _FUND_LIST_CACHE_TIME
        now = time.time()
        
        # 0. 检查内存缓存 (1小时内不查DB，或者跟DB保持一致? 
        # 这里为了极致性能，内存缓存有效时直接返回，内存缓存设为1小时或跟DB一致)
        # 简单起见，内存缓存有效期设为 1 小时，过期后再查 DB
        if self._fund_list_cache and now - _FUND_LIST_CACHE_TIME < 3600:
            return

        # 1. 尝试从数据库加载缓存
        last_update_str = self.db.get_setting("fund_list_updated_at")
        use_cache = False
        if last_update_str:
            try:
                last_update = float(last_update_str)
                if now - last_update < 86400: # 24小时
                    # DB 有效，加载到内存
                    etf_list = self.db.get_funds("ETF")
                    lof_list = self.db.get_funds("LOF")
                    if etf_list or lof_list:
                        self._fund_list_cache["ETF"] = etf_list
                        self._fund_list_cache["LOF"] = lof_list
                        
                        # 更新内存缓存时间
                        _FUND_LIST_CACHE_TIME = now
                        logger.info(f"从数据库加载基金列表: ETF {len(etf_list)}, LOF {len(lof_list)}")
                        use_cache = True
            except Exception as e:
                logger.warning(f"读取基金列表缓存失败: {e}")

        if use_cache:
            return

        # 2. 从 API 获取并过滤
        logger.info("正在从API更新基金列表...")
        raw_list = self.api.get_fund_list()
        
        self._fund_list_cache["ETF"] = []
        self._fund_list_cache["LOF"] = []
        
        # 准备批量保存的数据
        funds_to_save = []
        
        for fund in raw_list:
            code = fund["code"]
            name = fund["name"].upper()
            
            # 1. 排除 ETF 联接基金
            if "联接" in name:
                continue
            
            is_etf = False
            is_lof = False
            
            # 2. 严格代码段判断
            if code.startswith(("51", "56", "58", "159")):
                is_etf = True
            elif code.startswith(("16", "50")):
                is_lof = True
            
            if not is_etf and not is_lof:
                continue
            
            fund_info = {
                "code": code,
                "name": fund["name"],
                "type": "ETF" if is_etf else "LOF",
                "pinyin": fund.get("pinyin", "")
            }
            
            if is_etf:
                self._fund_list_cache["ETF"].append(fund_info)
            elif is_lof:
                self._fund_list_cache["LOF"].append(fund_info)
                
            funds_to_save.append(fund_info)
        
        # 3. 保存到数据库 (先清理该类型的旧数据，防止污染)
        if funds_to_save:
            try:
                with self.db._get_connection() as conn:
                    cursor = conn.cursor()
                    # 只有全量获取成功后才清理并更新
                    cursor.execute("DELETE FROM funds WHERE type IN ('ETF', 'LOF')")
                    for f in funds_to_save:
                        cursor.execute("""
                            INSERT OR REPLACE INTO funds
                            (code, name, type, pinyin, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (f["code"], f["name"], f["type"], f.get("pinyin", ""), datetime.now().isoformat()))
                
                self.db.set_setting("fund_list_updated_at", str(now))
                _FUND_LIST_CACHE_TIME = now
                logger.info(f"基金列表更新成功: 共 {len(funds_to_save)} 条")
            except Exception as e:
                logger.error(f"保存基金列表失败: {e}")
            logger.info(f"更新并保存基金列表: ETF {len(self._fund_list_cache['ETF'])}, LOF {len(self._fund_list_cache['LOF'])}")

    def _ensure_nav_cache(self):
        """确保所有基金净值已加载（内存缓存 -> 12小时DB缓存 -> 懒加载）"""
        global _NAV_CACHE, _NAV_CACHE_TIME
        self._ensure_fund_list() # 依赖基金列表
        now = time.time()
        
        # 0. 检查内存缓存 (1小时)
        if self._nav_cache and now - _NAV_CACHE_TIME < 3600:
            return
        
        # 1. 尝试从数据库加载缓存 (Blob)
        last_update_str = self.db.get_setting("nav_cache_updated_at")
        use_cache = False
        
        if last_update_str:
            try:
                last_update = float(last_update_str)
                if now - last_update < 43200: # 12小时
                    blob = self.db.get_setting("nav_cache_blob")
                    if blob:
                        loaded_cache = json.loads(blob)
                        # 更新实例缓存（实际上由于引用绑定，也就是更新全局缓存）
                        self._nav_cache.clear()
                        self._nav_cache.update(loaded_cache)
                        
                        _NAV_CACHE_TIME = now
                        logger.info(f"从数据库加载净值缓存: {len(self._nav_cache)} 条")
                        use_cache = True
            except Exception as e:
                logger.warning(f"读取净值缓存失败: {e}")
        
        if use_cache:
            return

        # 2. 从 API 获取 (带过滤优化)
        target_codes = set()
        for f in self._fund_list_cache.get("ETF", []):
            target_codes.add(f["code"])
        for f in self._fund_list_cache.get("LOF", []):
            target_codes.add(f["code"])
            
        logger.info(f"正在全量更新 {len(target_codes)} 只场内基金的净值数据...")
        
        # 只拉取我们关心的基金净值
        new_navs = self.api.get_all_fund_nav(target_codes=target_codes)
        self._nav_cache.clear()
        self._nav_cache.update(new_navs)
        
        # 3. 保存缓存
        try:
            blob = json.dumps(self._nav_cache)
            self.db.set_setting("nav_cache_blob", blob)
            self.db.set_setting("nav_cache_updated_at", str(now))
            _NAV_CACHE_TIME = now
            logger.info(f"净值数据更新完成并保存，共 {len(self._nav_cache)} 条")
        except Exception as e:
            logger.error(f"保存净值缓存失败: {e}")

    def fetch_etf_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """从东方财富获取ETF数据"""
        self._ensure_fund_list()
        self._ensure_nav_cache()
        
        # 如果未指定代码，获取所有ETF（限制数量以免请求过多？）
        # 这里为了演示，如果是全部，我们获取前50个热门的，或者全部获取行情（只要是一次批量请求就没问题）
        # 东方财富批量接口支持很多，我们可以尝试获取所有缓存中的ETF
        
        target_indices = []
        if not fund_codes:
            # 默认只获取部分活跃的，或者全部
            # 为防止列表过大，这里获取全部，因为批量接口效率较高
            target_indices = self._fund_list_cache["ETF"]
        else:
            code_set = set(fund_codes)
            target_indices = [f for f in self._fund_list_cache["ETF"] if f["code"] in code_set]
            
        if not target_indices:
            return []
            
        codes = [f["code"] for f in target_indices]
        
        # 优先使用新浪 API 获取行情（限制更宽松）
        quotes = self.sina_api.get_realtime_quotes(codes)
        
        # 如果新浪失败，回退到东财
        if not quotes or len(quotes) < len(codes) * 0.5:
            logger.warning(f"新浪 API 返回数据不足（{len(quotes)}/{len(codes)}），尝试东财 API...")
            eastmoney_quotes = self.api.get_realtime_quotes(codes)
            if eastmoney_quotes:
                quotes = eastmoney_quotes
        
        # 合并信息
        result = []
        quote_map = {q["code"]: q for q in quotes}
        
        for fund in target_indices:
            code = fund["code"]
            quote = quote_map.get(code)
            
            if quote:
                # 过滤无成交或价格无效的基金
                if quote["volume"] == 0:
                    if quote["price"] <= 0.001 or abs(quote["price"] - 1.0) < 0.001:
                       continue
                if quote["price"] <= 0:
                    continue
                    
                # 能够获取到行情的
                # 系统性修复：严禁使用 prev_close 填充缺失的 NAV
                nav = self._nav_cache.get(code)
                
                # 数据补救机制
                if not nav:
                    try:
                        valuation = self.api.get_fund_valuation(code)
                        if valuation and valuation.get("nav"):
                            nav = valuation["nav"]
                            self._nav_cache[code] = nav
                    except Exception:
                        pass
                
                if nav is None:
                    nav = 0.0

                price = quote["price"]
                # 如果当前没有成交（价格为0），使用昨收盘价
                if price <= 0 and quote["prev_close"] > 0:
                    price = quote["prev_close"]
                
                # 如果列表比较小（比如手动刷新了几个），我们可以尝试获取实时估值
                est_nav = 0.0
                if len(codes) <= 20: 
                    try:
                        valuation = self.api.get_fund_valuation(code)
                        if valuation:
                            est_nav = valuation["est_nav"]
                            # 如果有实时估值，ETF通常优先参考IOPV(est_nav)
                            nav = est_nav if est_nav > 0 else nav
                    except Exception:
                        pass

                result.append({
                    "code": code,
                    "name": fund["name"],
                    "type": "ETF",
                    "nav": nav, # 以后改进为真实IOPV
                    "price": price,
                    "volume": quote["volume"],
                    "amount": quote["amount"],
                    "timestamp": quote["timestamp"],
                    "prev_close": quote["prev_close"]
                })
                
        return result

    def fetch_lof_data(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """获取LOF数据（优先使用新浪 API）"""
        self._ensure_fund_list()
        self._ensure_nav_cache()
        
        target_indices = []
        if not fund_codes:
            target_indices = self._fund_list_cache["LOF"]
        else:
            code_set = set(fund_codes)
            target_indices = [f for f in self._fund_list_cache["LOF"] if f["code"] in code_set]
            
        if not target_indices:
            return []

        codes = [f["code"] for f in target_indices]
        
        # 优先使用新浪 API 获取行情
        quotes = self.sina_api.get_realtime_quotes(codes)
        
        # 如果新浪失败，回退到东财
        if not quotes or len(quotes) < len(codes) * 0.5:
            logger.warning(f"新浪 API 返回 LOF 数据不足，尝试东财 API...")
            eastmoney_quotes = self.api.get_realtime_quotes(codes)
            if eastmoney_quotes:
                quotes = eastmoney_quotes

        result = []
        quote_map = {q["code"]: q for q in quotes}
        
        for fund in target_indices:
            code = fund["code"]
            quote = quote_map.get(code)
            
            if quote:
                # 过滤无成交或价格无效的基金
                if quote["volume"] == 0:
                    if quote["price"] <= 0.001 or abs(quote["price"] - 1.0) < 0.001:
                       continue
                if quote["price"] <= 0:
                    continue

                # 系统性修复：严禁使用 prev_close 填充缺失的 NAV，这会导致折溢价率误算为 0%
                nav = self._nav_cache.get(code)
                
                # 数据补救机制：如果批量缓存中没有 NAV，尝试单点获取
                if not nav:
                    try:
                        # get_fund_valuation 返回的 nav 通常是昨晚的单位净值
                        valuation = self.api.get_fund_valuation(code)
                        if valuation and valuation.get("nav"):
                            nav = valuation["nav"]
                            # 顺便回填缓存，避免下次重复请求
                            self._nav_cache[code] = nav
                    except Exception as e:
                        logger.warning(f"基金 {code} 补救获取净值失败: {e}")
                
                # 如果依然获取不到，保持为 0，诚实反映数据缺失
                if nav is None:
                    nav = 0.0

                price = quote["price"]
                # 如果当前没有成交（价格为0），使用昨收盘价
                if price <= 0 and quote["prev_close"] > 0:
                    price = quote["prev_close"]
                
                # LOF通常更依赖估值接口的实时估值(est_nav)来做参考? 
                # 不，套利通常基于IOPV(ETF)或昨净值(LOF)。
                # 之前的逻辑是用 est_nav 覆盖 nav，这取决于策略。
                # 如果用户策略是 T+0 ETF 套利，需要 IOPV。LOF T+1 通常看昨净值。
                # 保留原有逻辑：如果 valuation 存在且有 est_nav (实时估值)，对于LOF可能作为参考
                # 但稳健起见，只要有确定的 nav (昨净值)，就优先使用。
                
                result.append({
                    "code": code,
                    "name": fund["name"],
                    "type": "LOF",
                    "nav": nav,
                    "price": price,
                    "volume": quote["volume"],
                    "amount": quote["amount"],
                    "timestamp": quote["timestamp"],
                    "prev_close": quote["prev_close"]
                })
                
        return result

    def fetch_fund_list(self, fund_type: str) -> List[Dict[str, Any]]:
        """从东方财富获取基金列表"""
        self._ensure_fund_list()
        return self._fund_list_cache.get(fund_type, [])

    def fetch_fund_trends(self, fund_code: str) -> List[Dict[str, Any]]:
        """获取基金分时走势数据"""
        return self.api.get_fund_trends(fund_code)


# 数据获取器工厂
class DataFetcherFactory:
    """数据获取器工厂"""

    @staticmethod
    def create_fetcher(fetcher_type: str = "eastmoney", **kwargs) -> DataFetcher:
        """
        创建数据获取器

        Args:
            fetcher_type: 获取器类型（目前仅支持 eastmoney）
            **kwargs: 传递给获取器的参数

        Returns:
            DataFetcher: 数据获取器实例
        """
        # 所有类型都使用东方财富数据源
        logger.info("创建东方财富数据获取器")
        return EastMoneyDataFetcher(**kwargs)


# 全局数据获取器实例
_fetcher_instance: Optional[DataFetcher] = None


def get_data_fetcher(fetcher_type: str = "eastmoney", **kwargs) -> DataFetcher:
    """
    获取数据获取器实例

    Args:
        fetcher_type: 获取器类型（目前仅支持 eastmoney）
        **kwargs: 传递给获取器的参数

    Returns:
        DataFetcher: 数据获取器实例
    """
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = DataFetcherFactory.create_fetcher(fetcher_type, **kwargs)
    return _fetcher_instance