import logging
import functools
import traceback
from typing import Callable, Any, Optional, Type
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class ErrorHandler:
    """统一错误处理类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def handle_exception(e: Exception, context: str = "", show_ui: bool = False, parent=None):
        """处理异常"""
        error_msg = f"{context} 发生错误: {str(e)}" if context else f"发生错误: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        
        if show_ui:
            ErrorHandler.show_error_dialog(error_msg, parent)

    @staticmethod
    def show_error_dialog(message: str, parent=None):
        """显示错误对话框"""
        # 确保在主线程中调用 GUI（如果需要更复杂的线程安全，可以使用信号）
        try:
            QMessageBox.critical(parent, "错误", message)
        except Exception as dialog_err:
            logger.error(f"无法显示错误对话框: {dialog_err}")

def catch_exception(context: str = "", show_ui: bool = False, return_val: Any = None):
    """
    异常捕获装饰器
    
    Args:
        context: 错误上下文描述
        show_ui: 是否显示错误弹窗
        return_val: 发生异常时的返回值
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 尝试获取 self 作为 parent
                parent = args[0] if args and hasattr(args[0], 'receivers') else None
                ErrorHandler.handle_exception(e, context=context, show_ui=show_ui, parent=parent)
                return return_val
        return wrapper
    return decorator
