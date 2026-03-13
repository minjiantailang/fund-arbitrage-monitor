# 基金套利监控应用性能优化实施计划

## 概述
基于性能测试结果，制定具体的优化实施计划，目标将启动时间从22+秒减少到5秒以内，数据刷新时间从3秒/基金减少到0.5秒/基金。

## 性能问题总结

### 实测数据（2026-01-31）
1. **东方财富数据获取器总耗时**：22.58秒
2. **ETF数据获取**：14.15秒（5个基金，平均2.8秒/基金）
3. **基金列表加载**：5.16秒（26,091个基金）
4. **净值数据加载**：约7秒（22,081条记录，分2页）
5. **基金管理器刷新**：12.23秒（4个基金，平均3.06秒/基金）

### 主要问题
1. **缓存策略失效**：每次创建`EastMoneyDataFetcher`都重新加载全量数据
2. **数据量过大**：加载26,091个基金，但只关注2,349个场内基金
3. **串行处理**：ETF数据获取异常缓慢
4. **请求过多**：获取少量基金需要多个独立请求

## 优化实施阶段

### 阶段1：缓存策略优化（立即实施）

#### 1.1 全局缓存共享
**目标**：避免重复加载全量数据
**修改文件**：`src/models/data_fetcher.py`
**具体实现**：
```python
# 模块级全局缓存
_FUND_LIST_CACHE: Dict[str, List[Dict]] = {}
_FUND_LIST_CACHE_TIME: float = 0
_NAV_CACHE: Dict[str, float] = {}
_NAV_CACHE_TIME: float = 0

class EastMoneyDataFetcher(DataFetcher):
    def __init__(self, cache_duration: int = 300):
        super().__init__(cache_duration)
        self.api = EastMoneyAPI()
        # 使用全局缓存，而不是实例变量
        self._fund_list_cache = _FUND_LIST_CACHE
        self._fund_list_cache_time = _FUND_LIST_CACHE_TIME
        self._nav_cache = _NAV_CACHE
        self._nav_cache_time = _NAV_CACHE_TIME
```

#### 1.2 延长缓存时间
**目标**：减少不必要的刷新
**修改文件**：`src/models/data_fetcher.py`
**具体实现**：
```python
def _ensure_fund_list(self):
    now = time.time()
    # 延长到24小时（86400秒）
    if not self._fund_list_cache or now - self._fund_list_cache_time > 86400:
        # 加载数据...
        self._fund_list_cache_time = now

def _ensure_nav_cache(self):
    now = time.time()
    # 延长到12小时（43200秒）
    if not self._nav_cache or now - self._nav_cache_time > 43200:
        # 加载数据...
        self._nav_cache_time = now
```

#### 1.3 磁盘缓存
**目标**：避免重启后重新加载
**修改文件**：新建 `src/utils/cache_manager.py`
**具体实现**：
```python
import pickle
import os
from typing import Any, Dict

class CacheManager:
    def __init__(self, cache_dir: str = "~/.fund_arbitrage_monitor/cache"):
        self.cache_dir = os.path.expanduser(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def save(self, key: str, data: Any, ttl: int = 3600):
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'data': data,
                'expires': time.time() + ttl
            }, f)

    def load(self, key: str) -> Any:
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
                if cached['expires'] > time.time():
                    return cached['data']
        return None
```

### 阶段2：懒加载优化（立即实施）

#### 2.1 只加载场内基金
**目标**：启动时只加载ETF和LOF基金
**修改文件**：`src/models/data_fetcher.py`
**具体实现**：
```python
def _ensure_fund_list(self):
    now = time.time()
    if not self._fund_list_cache or now - self._fund_list_cache_time > 86400:
        raw_list = self.api.get_fund_list()

        # 只处理场内基金
        self._fund_list_cache["ETF"] = []
        self._fund_list_cache["LOF"] = []

        for fund in raw_list:
            code = fund["code"]
            name = fund["name"].upper()

            # 排除场外基金
            if "联接" in name:
                continue

            # 场内基金判断
            if code.startswith(("51", "56", "58", "159")):  # ETF
                self._fund_list_cache["ETF"].append({
                    "code": code,
                    "name": fund["name"],
                    "type": "ETF",
                    "pinyin": fund.get("pinyin", "")
                })
            elif code.startswith(("16", "50")):  # LOF
                self._fund_list_cache["LOF"].append({
                    "code": code,
                    "name": fund["name"],
                    "type": "LOF",
                    "pinyin": fund.get("pinyin", "")
                })

        self._fund_list_cache_time = now
        logger.info(f"更新场内基金列表缓存: ETF {len(self._fund_list_cache['ETF'])} 个, LOF {len(self._fund_list_cache['LOF'])} 个")
```

#### 2.2 后台加载其他数据
**目标**：非关键数据在后台加载
**修改文件**：`src/controllers/data_controller.py`
**具体实现**：
```python
def refresh_all_data_async(self):
    """异步刷新所有数据"""
    # 优先加载场内基金数据
    self.refresh_etf_data_async()
    self.refresh_lof_data_async()

    # 后台加载其他数据
    threading.Thread(target=self._load_other_data, daemon=True).start()

def _load_other_data(self):
    """后台加载其他基金数据"""
    # 这里可以加载场外基金数据或其他非关键数据
    pass
```

### 阶段3：并发处理优化（短期优化）

#### 3.1 并行获取数据
**目标**：使用线程池并发获取数据
**修改文件**：`src/models/data_fetcher.py`
**具体实现**：
```python
import concurrent.futures

class EastMoneyDataFetcher(DataFetcher):
    def fetch_etf_data_concurrent(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """并发获取ETF数据"""
        if not fund_codes:
            fund_codes = [f["code"] for f in self._fund_list_cache["ETF"]]

        # 分批处理，每批50个基金
        batch_size = 50
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(0, len(fund_codes), batch_size):
                batch = fund_codes[i:i+batch_size]
                future = executor.submit(self._fetch_etf_batch, batch)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    batch_result = future.result()
                    results.extend(batch_result)
                except Exception as e:
                    logger.error(f"批量获取ETF数据失败: {e}")

        return results

    def _fetch_etf_batch(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
        """获取一批ETF数据"""
        # 批量获取行情
        quotes = self.api.get_realtime_quotes(fund_codes)

        results = []
        for quote in quotes:
            # 处理单个基金数据...
            pass

        return results
```

#### 3.2 优化实时行情获取
**目标**：减少实时行情API调用延迟
**修改文件**：`src/data_sources/eastmoney_api.py`
**具体实现**：
```python
def get_realtime_quotes_optimized(self, fund_codes: List[str]) -> List[Dict[str, Any]]:
    """优化版批量获取行情"""
    if not fund_codes:
        return []

    # 增加批量大小到200
    batch_size = 200
    results = []

    for i in range(0, len(fund_codes), batch_size):
        batch_codes = fund_codes[i:i+batch_size]

        # 优化请求参数，只请求必要字段
        params = {
            "ut": "fa5fd1943c7b386f172d68934880639a",
            "fltt": "2",
            "invt": "2",
            "fields": "f12,f14,f2,f3,f5,f6,f18",  # 只请求必要字段
            "secids": self._build_secids(batch_codes),
            "_": int(time.time() * 1000)
        }

        # 发送请求...

    return results
```

### 阶段4：架构优化（长期优化）

#### 4.1 单例模式
**目标**：确保只有一个数据获取器实例
**修改文件**：`src/models/data_fetcher.py`
**具体实现**：
```python
class EastMoneyDataFetcher(DataFetcher):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_duration: int = 300):
        if not self._initialized:
            super().__init__(cache_duration)
            self.api = EastMoneyAPI()
            # 初始化缓存...
            self._initialized = True
```

#### 4.2 依赖注入
**目标**：更好地管理依赖关系
**修改文件**：`src/models/fund_manager.py`
**具体实现**：
```python
class FundManager:
    def __init__(self, fetcher: Optional[DataFetcher] = None):
        self.db = get_database()
        self.fetcher = fetcher or get_data_fetcher("eastmoney")
        self.calculator = get_calculator()
        # ...
```

## 实施时间表

### 第1周：核心优化
- 完成阶段1和阶段2的优化
- 预期效果：启动时间减少到10秒以内

### 第2周：性能提升
- 完成阶段3的优化
- 预期效果：数据刷新时间减少到1秒/基金

### 第3周：架构完善
- 完成阶段4的优化
- 预期效果：启动时间减少到5秒以内，刷新时间0.5秒/基金

## 测试计划

### 性能测试
1. **基准测试**：优化前后对比测试
2. **压力测试**：大量基金数据获取测试
3. **稳定性测试**：长时间运行测试

### 功能测试
1. **回归测试**：确保现有功能不受影响
2. **边界测试**：测试极端情况
3. **兼容性测试**：测试不同网络环境

## 风险控制

### 技术风险
1. **API限制**：东方财富API可能有频率限制
   - 应对：添加请求间隔和限流机制
2. **网络不稳定**：网络波动可能导致失败
   - 应对：优化重试机制和超时设置
3. **数据一致性**：并发处理可能导致数据不一致
   - 应对：添加数据校验和同步机制

### 开发风险
1. **进度延迟**：优化可能比预期复杂
   - 应对：分阶段实施，优先核心优化
2. **兼容性问题**：优化可能影响现有功能
   - 应对：充分测试，逐步发布

## 成功标准

### 量化指标
1. **启动时间**：从22+秒减少到5秒以内（减少77%）
2. **数据刷新**：从3秒/基金减少到0.5秒/基金（减少83%）
3. **内存使用**：减少全量数据加载，内存使用降低30%
4. **网络请求**：请求次数减少50%

### 用户体验
1. **界面响应**：无卡顿，流畅操作
2. **数据更新**：快速获取最新数据
3. **稳定性**：长时间运行稳定
4. **错误处理**：友好的错误提示和恢复

## 监控和评估

### 性能监控
1. **添加性能日志**：记录各阶段耗时
2. **实时监控**：监控关键性能指标
3. **报警机制**：性能下降时报警

### 效果评估
1. **定期评估**：每周评估优化效果
2. **用户反馈**：收集用户使用反馈
3. **持续优化**：根据评估结果持续改进

---
*计划创建时间：2026年1月31日*
*版本：1.0.0*