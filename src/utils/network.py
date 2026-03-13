"""
网络请求工具 - 重试逻辑和错误处理
"""
import logging
import time
import functools
from typing import Callable, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)

class RetryConfig:
    """重试配置"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 5.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions

# 默认配置实例
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.3,
    max_delay=3.0,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
)

def retry_on_failure(config: Optional[RetryConfig] = None, context: str = ""):
    """
    重试装饰器
    
    Args:
        config: 重试配置，为 None 时使用默认配置
        context: 上下文描述，用于日志
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
        
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        log_context = f"[{context}] " if context else ""
                        logger.warning(
                            f"{log_context}请求失败 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}. "
                            f"{delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{log_context}请求失败，已达最大重试次数: {e}")
                except Exception as e:
                    # 非重试异常，直接抛出
                    raise
                    
            # 所有重试都失败
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

def safe_request(func: Callable, default: Any = None, context: str = "") -> Any:
    """
    安全执行请求，捕获异常并返回默认值
    
    Args:
        func: 要执行的函数
        default: 失败时的默认返回值
        context: 日志上下文
    """
    try:
        return func()
    except Exception as e:
        log_context = f"[{context}] " if context else ""
        logger.debug(f"{log_context}请求失败: {e}")
        return default
