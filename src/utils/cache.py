"""
缓存管理系统 - 支持 TTL、LRU 淘汰和持久化
"""
import time
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    ttl: float  # 生存时间（秒），0 表示永不过期
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.ttl <= 0:
            return False
        return time.time() - self.timestamp > self.ttl


class LRUCache:
    """
    LRU 缓存实现
    
    Features:
    - TTL 过期支持
    - LRU 淘汰策略
    - 线程安全
    - 可选持久化
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300,  # 默认5分钟
        persist_path: Optional[Path] = None,
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._persist_path = persist_path
        self._lock = threading.RLock()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        
        # 如果有持久化路径，尝试加载
        if persist_path:
            self._load_from_disk()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
                
            entry = self._cache[key]
            
            # 检查过期
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return default
            
            # LRU: 移到末尾
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
        """
        with self._lock:
            if ttl is None:
                ttl = self._default_ttl
                
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 检查容量
            while len(self._cache) >= self._max_size:
                # 删除最旧的（LRU）
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"LRU淘汰: {oldest_key}")
            
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl,
            )
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[float] = None,
    ) -> Any:
        """
        获取缓存值，如果不存在则使用 factory 创建并缓存
        
        Args:
            key: 缓存键
            factory: 值工厂函数
            ttl: 过期时间
        """
        value = self.get(key)
        if value is None:
            value = factory()
            if value is not None:
                self.set(key, value, ttl)
        return value
    
    def invalidate_prefix(self, prefix: str):
        """删除所有以指定前缀开头的缓存"""
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            logger.debug(f"已清除 {len(keys_to_delete)} 个前缀为 '{prefix}' 的缓存")
    
    def cleanup_expired(self) -> int:
        """清理所有过期条目"""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")
            return len(expired_keys)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2%}",
            }
    
    def _load_from_disk(self):
        """从磁盘加载缓存"""
        if not self._persist_path or not self._persist_path.exists():
            return
            
        try:
            with open(self._persist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            now = time.time()
            loaded = 0
            for key, entry_data in data.items():
                entry = CacheEntry(
                    value=entry_data["value"],
                    timestamp=entry_data["timestamp"],
                    ttl=entry_data["ttl"],
                )
                # 只加载未过期的
                if not entry.is_expired():
                    self._cache[key] = entry
                    loaded += 1
                    
            logger.info(f"从磁盘加载了 {loaded} 个缓存条目")
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
    
    def save_to_disk(self):
        """保存缓存到磁盘"""
        if not self._persist_path:
            return
            
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                data = {
                    key: {
                        "value": entry.value,
                        "timestamp": entry.timestamp,
                        "ttl": entry.ttl,
                    }
                    for key, entry in self._cache.items()
                    if not entry.is_expired()  # 只保存未过期的
                }
                
            with open(self._persist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
                
            logger.debug(f"缓存已保存到磁盘: {len(data)} 条")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")


class CacheManager:
    """
    缓存管理器 - 管理多个命名空间的缓存
    """
    
    _instance = None
    _caches: Dict[str, LRUCache] = {}
    
    # 默认缓存目录
    DEFAULT_CACHE_DIR = Path.home() / ".fund_arbitrage_monitor" / "cache"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_cache(
        self,
        namespace: str,
        max_size: int = 1000,
        default_ttl: float = 300,
        persist: bool = False,
    ) -> LRUCache:
        """
        获取指定命名空间的缓存实例
        
        Args:
            namespace: 命名空间（如 'fund_data', 'quotes'）
            max_size: 最大条目数
            default_ttl: 默认 TTL
            persist: 是否持久化
        """
        if namespace not in self._caches:
            persist_path = None
            if persist:
                persist_path = self.DEFAULT_CACHE_DIR / f"{namespace}.json"
                
            self._caches[namespace] = LRUCache(
                max_size=max_size,
                default_ttl=default_ttl,
                persist_path=persist_path,
            )
            
        return self._caches[namespace]
    
    def clear_all(self):
        """清空所有缓存"""
        for cache in self._caches.values():
            cache.clear()
        logger.info("所有缓存已清空")
    
    def cleanup_expired_all(self) -> int:
        """清理所有命名空间的过期缓存"""
        total = 0
        for cache in self._caches.values():
            total += cache.cleanup_expired()
        return total
    
    def save_all(self):
        """保存所有持久化缓存"""
        for cache in self._caches.values():
            cache.save_to_disk()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计信息"""
        return {
            namespace: cache.stats
            for namespace, cache in self._caches.items()
        }


# 便捷函数
def get_cache_manager() -> CacheManager:
    """获取缓存管理器单例"""
    return CacheManager()

def get_cache(namespace: str, **kwargs) -> LRUCache:
    """获取指定命名空间的缓存"""
    return get_cache_manager().get_cache(namespace, **kwargs)
