"""
配置管理系统 - 集中管理应用配置
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """数据源配置"""
    default_source: str = "eastmoney"
    request_timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 0.5
    use_proxy: bool = False

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5分钟
    max_size: int = 10000
    persist_to_disk: bool = True

@dataclass
class UIConfig:
    """UI配置"""
    auto_refresh_interval: int = 300  # 5分钟，单位秒
    default_sort: str = "spread_pct_desc"
    show_only_opportunities: bool = False
    table_page_size: int = 100

@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = ""  # 空表示使用默认路径
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_history_days: int = 30

@dataclass
class AppConfig:
    """应用总配置"""
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # 元信息
    version: str = "2.0.0"
    debug: bool = False


class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    _config: Optional[AppConfig] = None
    _config_path: Optional[Path] = None
    
    # 默认配置文件位置
    DEFAULT_CONFIG_DIR = Path.home() / ".fund_arbitrage_monitor"
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._ensure_config_dir()
            self._load_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config_path = self.DEFAULT_CONFIG_DIR / self.DEFAULT_CONFIG_FILE
    
    def _load_config(self):
        """加载配置文件"""
        if self._config_path and self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = self._dict_to_config(data)
                logger.info(f"配置已加载: {self._config_path}")
            except Exception as e:
                logger.warning(f"加载配置失败，使用默认配置: {e}")
                self._config = AppConfig()
        else:
            logger.info("配置文件不存在，使用默认配置")
            self._config = AppConfig()
            self.save()  # 保存默认配置
    
    def _dict_to_config(self, data: Dict) -> AppConfig:
        """字典转配置对象"""
        return AppConfig(
            data_source=DataSourceConfig(**data.get("data_source", {})),
            cache=CacheConfig(**data.get("cache", {})),
            ui=UIConfig(**data.get("ui", {})),
            database=DatabaseConfig(**data.get("database", {})),
            version=data.get("version", "2.0.0"),
            debug=data.get("debug", False),
        )
    
    def _config_to_dict(self) -> Dict:
        """配置对象转字典"""
        return {
            "data_source": asdict(self._config.data_source),
            "cache": asdict(self._config.cache),
            "ui": asdict(self._config.ui),
            "database": asdict(self._config.database),
            "version": self._config.version,
            "debug": self._config.debug,
        }
    
    def save(self):
        """保存配置到文件"""
        if self._config_path and self._config:
            try:
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config_to_dict(), f, indent=2, ensure_ascii=False)
                logger.info(f"配置已保存: {self._config_path}")
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
    
    @property
    def config(self) -> AppConfig:
        """获取配置对象"""
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）
        
        Example:
            config_manager.get("data_source.timeout", 10)
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any, save_immediately: bool = True):
        """
        设置配置值
        
        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
            save_immediately: 是否立即保存
        """
        keys = key.split(".")
        target = self._config
        
        # 导航到目标对象
        for k in keys[:-1]:
            if hasattr(target, k):
                target = getattr(target, k)
            else:
                logger.warning(f"无效的配置键: {key}")
                return
        
        # 设置值
        final_key = keys[-1]
        if hasattr(target, final_key):
            setattr(target, final_key, value)
            logger.debug(f"配置已更新: {key} = {value}")
            if save_immediately:
                self.save()
        else:
            logger.warning(f"无效的配置键: {key}")
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = AppConfig()
        self.save()
        logger.info("配置已重置为默认值")
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 便捷函数
def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    return ConfigManager()

def get_config() -> AppConfig:
    """获取配置对象"""
    return get_config_manager().config
