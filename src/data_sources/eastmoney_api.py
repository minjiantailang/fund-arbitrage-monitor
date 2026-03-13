"""
东方财富 API 接口封装
"""
import re
import json
import time
import logging
import requests
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class EastMoneyAPI:
    """东方财富 API 接口"""

    def __init__(self, use_proxy: bool = False):
        self.session = requests.Session()
        
        # 配置重试策略 (保守配置，由外部逻辑控制重试)
        retries = Retry(total=1, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 如果不使用系统代理，显式禁用
        if not use_proxy:
            self.session.trust_env = False
            self.session.proxies = {"http": None, "https": None}

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "http://fund.eastmoney.com/",
        })

    def get_fund_list(self) -> List[Dict[str, str]]:
        """
        获取所有基金列表

        Returns:
            List[Dict]: [{'code': '000001', 'name': '华夏成长', 'type': '混合型', ...}]
        """
        url = "http://fund.eastmoney.com/js/fundcode_search.js"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 数据格式: var r = [["000001","HXCZ","华夏成长","混合型","HUAXIACHENGZHANG"],...];
            content = response.text
            
            # 提取数组内容
            match = re.search(r'var r = (\[.*\]);', content)
            if not match:
                logger.error("无法解析基金列表数据")
                return []
                
            data_str = match.group(1)
            # 这是一个 JavaScript 数组，可以用 json.loads 解析
            # 但里面的字符串可能用单引号，JS数组格式与JSON略有不同
            # 这里简单处理，假设它是标准的 JSON 数组格式
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                # 如果标准 JSON 解析失败，尝试使用 exec (慎用，但在受控环境下主要为了解析数据)
                # 或者手动解析。这里为了安全，使用正则简单提取或直接返回空
                # 实际上东方财富返回的是双引号，应该是标准 JSON
                logger.warning("基金列表JSON解析失败，尝试备用解析")
                return []

            funds = []
            for item in data:
                # item: ["code", "pinyin_abbr", "name", "type", "pinyin_full"]
                if len(item) >= 4:
                    funds.append({
                        "code": item[0],
                        "name": item[2],
                        "type": item[3],
                        "pinyin": item[4] if len(item) > 4 else ""
                    })
            
            logger.info(f"成功获取 {len(funds)} 个基金信息")
            return funds

        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            return []

    def get_fund_valuation(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金实时估值（净值估算）

        Args:
            fund_code: 基金代码

        Returns:
            Dict: {'mz': '3.456', 'gsz': '3.457', 'gszzl': '0.03', 'gztime': '...'}
        """
        # 快速跳过已知无估值数据的基金类型
        # 这些基金本身不提供实时估值接口，避免无意义的 404 请求
        skip_prefixes = (
            "159001", "159003", "159005",  # 货币ETF
            "511",    # 511xxx 货币/债券ETF
            "519",    # 519xxx 场外基金代码（非场内交易）
            "56",     # 56xxxx 科创板ETF（部分无估值）
            "58",     # 58xxxx 创业板ETF（部分无估值）
            "50",     # 50xxxx 上证ETF（部分老ETF无估值）
        )
        if fund_code.startswith(skip_prefixes):
            return None
            
        timestamp = int(time.time() * 1000)
        url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js?rt={timestamp}"
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            content = response.text
            
            # 格式: jsonpgz({"fundcode":"510300","name":"...","jzrq":"...","dwjz":"...","gsz":"...","gszzl":"...","gztime":"..."});
            match = re.search(r'jsonpgz\((.*)\)', content)
            if not match:
                # 可能是基金没有实时估值数据，或者停牌等
                logger.debug(f"未找到基金 {fund_code} 的实时估值数据")
                return None
                
            data_json = match.group(1)
            try:
                data = json.loads(data_json)
            except json.JSONDecodeError:
                logger.debug(f"解析基金 {fund_code} 估值数据失败，数据格式错误")
                return None
            
            return {
                "fundcode": data.get("fundcode"),
                "name": data.get("name"),
                "nav": float(data.get("dwjz", 0)),  # 单位净值 (上一交易日)
                "nav_date": data.get("jzrq"),      # 净值日期
                "est_nav": float(data.get("gsz", 0)), # 估算净值 (实时)
                "est_growth": float(data.get("gszzl", 0)), # 估算增长率
                "est_time": data.get("gztime")      # 估算时间
            }
            
        except Exception as e:
            # 降级为 debug 日志，避免刷屏
            logger.debug(f"获取基金 {fund_code} 估值失败: {e}")
            return None

    def get_fund_details(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金详细信息（费率等）
        由于这通常需要解析复杂的 HTML 页面，这里我们简化处理，
        仅尝试获取一些基本信息，或者通过通用接口获取。
        目前可以复用 valuation 接口获取基础信息。
        """
        return self.get_fund_valuation(fund_code)

    def get_realtime_quote(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取场内基金实时行情（ETF/LOF）
        使用东方财富行情接口
        """
        # 区分沪深市场
        # 50/51/56/58 开头是SH (1), 15/16/18 开头是SZ (0)
        market = "1" if fund_code.startswith(("50", "51", "56", "58")) else "0"
        sec_id = f"{market}.{fund_code}"
        
        # 东方财富行情API - 只请求必要字段以减少负载
        # f43: 最新价, f44: 最高, f45: 最低, f46: 开盘, f47: 成交量, f48: 成交额, f58: 名称
        timestamp = int(time.time() * 1000)
        url = "http://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "ut": "fa5fd1943c7b386f172d68934880639a",
            "fltt": "2",
            "invt": "2", 
            "vol": "2",
            "fields": "f43,f44,f45,f46,f47,f48,f58",  # 精简为7个必要字段
            "secid": sec_id,
            "_": timestamp
        }

        try:
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data and "data" in data and data["data"]:
                quote = data["data"]
                # 解析关键字段 (参考东方财富字段定义)
                # f43: 最新价, f44: 最高, f45: 最低, f46: 开盘, f47: 成交量, f48: 成交额
                # f60: 昨收, f170: 涨跌幅
                                
                price = float(quote.get("f43", 0)) / 100 if "f43" in quote and quote["f43"] != "-" else 0.0
                # 注意：有些接口返回的是整数（分），有些是浮点数。这里假设API返回的是原值（如果是整数需要除以100等，但push2接口通常返回浮点数，或者需要看具体field）
                # 实际上 push2 接口通常返回的就是直观数值，除了某些特定字段。
                # 让我们通过观察验证一下：通常 f43 是 3560 代表 3.560 吗？不，push2 get 接口一般返回真实值。
                # 但为了保险，如果数值大得离谱（比如 > 1000 对于ETF），可能需要调整。
                # 不过，对于这个特定接口，如果不确定，我们可以使用更简单的接口。
                
                # 让我们使用更简单的 http://hq.sinajs.cn/list=sh510300 也是一个选择，但为了保持一致性使用东财。
                # 东财这个接口通常返回的就是正常数值。
                
                # 修正：f43 等字段在 push2 接口中，通常是实际价格。
                current_price = quote.get("f43")
                if current_price == "-":
                    current_price = 0.0
                else:
                    current_price = float(current_price)

                return {
                    "code": fund_code,
                    "name": quote.get("f58", ""),
                    "price": current_price,
                    "open": float(quote.get("f46", 0)) if quote.get("f46") != "-" else 0.0,
                    "high": float(quote.get("f44", 0)) if quote.get("f44") != "-" else 0.0,
                    "low": float(quote.get("f45", 0)) if quote.get("f45") != "-" else 0.0,
                    "volume": int(quote.get("f47", 0)) if quote.get("f47") != "-" else 0,
                    "amount": float(quote.get("f48", 0)) if quote.get("f48") != "-" else 0.0,
                    "timestamp": datetime.now().isoformat() # 使用服务器时间更好，这里简化
                }
            
            return None

        except Exception as e:
            logger.debug(f"获取基金 {fund_code} 实时行情失败: {e}")
            return None

    def get_fund_trends(self, fund_code: str) -> List[Dict[str, Any]]:
        """
        获取基金当日分时走势数据
        
        Args:
            fund_code: 基金代码
            
        Returns:
            List[Dict]: 分时数据列表 [{'timestamp': '...', 'price': 1.23, 'avg_price': 1.22, 'volume': 100}, ...]
        """
        # 区分沪深市场
        market = "1" if fund_code.startswith(("50", "51", "56", "58", "60")) else "0"
        sec_id = f"{market}.{fund_code}"
        
        url = "http://push2.eastmoney.com/api/qt/stock/trends2/get"
        params = {
            "secid": sec_id,
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f53,f56,f58",  # f51:时间, f53:价格, f56:均价, f58:成交量
            "iscr": "0",
            "ndays": "1",
        }
        
        try:
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if not data or not data.get("data") or not data["data"].get("trends"):
                return []
                
            trends = data["data"]["trends"]
            result = []
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            for line in trends:
                # 格式可能是: "2026-01-30 14:55,1.234,100,1.233,..." 或 "14:55,1.234,100,1.233,..."
                parts = line.split(",")
                if len(parts) >= 3:
                    time_str = parts[0]
                    try:
                        price = float(parts[1])
                        volume = int(parts[2]) if parts[2] else 0
                        avg_price = float(parts[3]) if len(parts) > 3 and parts[3] else price
                    except (ValueError, IndexError):
                        continue
                    
                    # 智能判断时间格式：如果已经包含日期（长度>8），直接使用；否则拼接今天日期
                    if len(time_str) > 8:
                        # 已经是完整格式 "2026-01-30 14:35"
                        full_time_str = time_str
                    else:
                        # 只有时间 "14:35"，需要拼接日期
                        full_time_str = f"{today} {time_str}"
                    
                    result.append({
                        "timestamp": full_time_str,
                        "price": price,
                        "avg_price": avg_price,
                        "volume": volume,
                        "code": fund_code
                    })
            
            logger.info(f"获取基金 {fund_code} 分时数据成功: {len(result)} 条")
            return result
            
        except Exception as e:
            logger.debug(f"获取基金 {fund_code} 分时走势失败: {e}")
            return []

    def get_realtime_quotes(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取基金实时行情 (并发优化版)
        
        Args:
            fund_codes: 基金代码列表
            
        Returns:
            List[Dict]: 实时行情列表
        """
        if not fund_codes:
            return []
            
        import concurrent.futures
        
        # 将请求拆分为小批次
        batch_size = 20  # 适度增大批次以减少请求次数
        batches = [fund_codes[i:i + batch_size] for i in range(0, len(fund_codes), batch_size)]
        
        results = []
        # 使用线程池并发请求，适度并行（3线程）
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {executor.submit(self._fetch_quotes_batch, batch): batch for batch in batches}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    data = future.result()
                    results.extend(data)
                    # 批次间短暂休眠
                    time.sleep(random.uniform(0.1, 0.3)) 
                except Exception as e:
                    logger.error(f"并发请求批次失败: {e}")
                    
        return results

    def _fetch_quotes_batch(self, codes: List[str]) -> List[Dict[str, Any]]:
        """获取单批次行情数据"""
        secids = []
        for code in codes:
            market = "1" if code.startswith(("50", "51", "56", "58")) else "0"
            secids.append(f"{market}.{code}")
        
        secids_str = ",".join(secids)
        
        # 使用随机负载均衡域名分散请求压力
        domains = [
            "95.push2.eastmoney.com",
            "65.push2.eastmoney.com", 
            "push2.eastmoney.com"
        ]
        url = f"http://{random.choice(domains)}/api/qt/ulist.np/get"
        
        # 优化：只请求必要字段
        params = {
            "ut": "fa5fd1943c7b386f172d68934880639a",
            "fltt": "2",
            "invt": "2",
            "vol": "2",
            "fields": "f12,f14,f2,f3,f5,f6,f18", 
            "secids": secids_str,
            "_": int(time.time() * 1000)
        }
        
        # 移除 Connection:close 以复用连接，只保留 UA
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 重试逻辑
        for attempt in range(2):
            try:
                # 稍微放宽超时时间
                response = self.session.get(url, params=params, headers=headers, timeout=8)
                response.raise_for_status()
                data = response.json()
                
                results = []
                if data and data.get("data") and "diff" in data["data"]:
                    diff = data["data"]["diff"]
                    items = diff.values() if isinstance(diff, dict) else diff
                    
                    for item in items:
                        price = item.get("f2")
                        if price == "-": price = 0.0
                        else: price = float(price)
                        
                        results.append({
                            "code": item.get("f12"),
                            "name": item.get("f14"),
                            "price": price,
                            "change_pct": float(item.get("f3", 0)) if item.get("f3") != "-" else 0.0,
                            "volume": int(item.get("f5", 0)) if item.get("f5") != "-" else 0,
                            "amount": float(item.get("f6", 0)) if item.get("f6") != "-" else 0.0,
                            "high": 0.0, "low": 0.0, "open": 0.0,
                            "prev_close": float(item.get("f18", 0)) if item.get("f18") != "-" else 0.0,
                            "timestamp": datetime.now().isoformat()
                        })
                return results
                
            except Exception as e:
                if attempt == 1:
                    logger.warning(f"批量行情请求失败，正在通过单点接口补救 {len(codes)} 只基金: {e}")
                    # 终极救济逻辑：如果批量行情挂了，尝试通过单点接口逐个补齐（至少保证有价格）
                    rescue_results = []
                    for i, code in enumerate(codes):
                        try:
                            # 终极救济使用 get_realtime_quote，因为它返回价格信息
                            val = self.get_realtime_quote(code)
                            if val:
                                rescue_results.append({
                                    "code": code,
                                    "name": val.get("name", ""),
                                    "price": val.get("price", 0.0),
                                    "change_pct": 0.0,
                                    "volume": val.get("volume", 0),
                                    "amount": val.get("amount", 0.0),
                                    "high": 0.0, "low": 0.0, "open": 0.0,
                                    "prev_close": val.get("price", 0.0), # 救济模式下暂用现价近似昨收
                                    "timestamp": datetime.now().isoformat()
                                })
                            # 优化：每10只基金休眠0.5秒，而非每只都休眠
                            if i % 10 == 9:
                                time.sleep(0.5)
                        except Exception as rescue_e:
                            logger.debug(f"单点补救基金 {code} 失败: {rescue_e}")
                            continue
                    return rescue_results
                else:
                    # 批量模式报错后短暂退避
                    time.sleep(1.0) 
        
        return []
        
    def get_all_fund_nav(self, target_codes: Optional[set] = None) -> Dict[str, float]:
        """
        获取所有基金的最新单位净值
        
        Args:
            target_codes: 目标基金代码集合，如果提供则只解析这些基金
        
        Returns:
            Dict[str, float]: 基金代码 -> 单位净值
        """
        # t=1: 开放式基金
        # lx=1: 楼层
        # page=1,99999: 获取所有 (这里我们用分页逻辑)
        url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
        params = {
            "t": "1",
            "lx": "1",
            "letter": "",
            "gsid": "",
            "text": "",
            "sort": "zdf,desc",
            "dt": int(time.time() * 1000),
            "atfc": "",
            "onlySale": "0",
        }
        
        nav_map = {}
        page = 1
        page_size = 20000 
        
        try:
            import json
            while True:
                params["page"] = f"{page},{page_size}"
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                content = response.text
                
                # 获取总页数
                if page == 1:
                    pm = re.search(r'pages:"(\d+)"', content)
                    total_pages = int(pm.group(1)) if pm else 1
                    logger.info(f"净值数据总页数: {total_pages}, 每页 {page_size}")
                
                # 提取数据项
                match = re.search(r'datas:(\[\[.*\]\])', content)
                if not match:
                    logger.warning(f"第 {page} 页未找到数据")
                    break
                    
                data_str = match.group(1)
                try:
                    data_list = json.loads(data_str)
                    
                    processed_count = 0
                    for item in data_list:
                        if len(item) > 3:
                            code = item[0]
                            
                            # 过滤非目标基金
                            if target_codes and code not in target_codes:
                                continue
                                
                            # 智能动态解析 NAV: 从 index 3 开始查找第一个非日期、非空的数值
                            found_nav = False
                            idx = 3
                            
                            # 1. 如果是日期，跳过
                            if idx < len(item):
                                val = str(item[idx])
                                if "-" in val and len(val) >= 8:
                                    idx += 1
                            
                            # 2. 如果是空字段，继续向后找
                            while idx < len(item):
                                val = str(item[idx]).strip()
                                if val != "":
                                    # 找到第一个非空字段，认为它是 NAV
                                    try:
                                        nav_map[code] = float(val)
                                        found_nav = True
                                        processed_count += 1
                                    except ValueError:
                                        pass 
                                    break
                                idx += 1
                                        
                    logger.info(f"第 {page} 页解析成功 {processed_count} 条数据")
                    
                except Exception as e:
                    logger.warning(f"解析第 {page} 页JSON失败: {e}")
                
                if page >= total_pages:
                    break
                page += 1
                
            logger.info(f"成功获取 {len(nav_map)} 个基金的净值数据")
            return nav_map
            
        except Exception as e:
            logger.error(f"获取所有基金净值失败: {e}")
            return {}
