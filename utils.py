"""工具模組"""
import logging


def get_default_log_level():
    """獲取預設日誌級別"""
    return logging.INFO


def get_default_log_format():
    """獲取預設日誌格式"""
    return '%(asctime)s - %(levelname)s - %(message)s'


def create_console_handler():
    """創建控制台日誌處理器"""
    return logging.StreamHandler()


def create_log_handlers():
    """創建所有日誌處理器"""
    handlers = [create_console_handler()]
    return handlers


def configure_logging_basic_config(level, format_str, handlers):
    """配置日誌基本設定"""
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )


def get_logger(name):
    """獲取日誌記錄器"""
    return logging.getLogger(name)


def setup_logging():
    """設定日誌系統"""
    level = get_default_log_level()
    format_str = get_default_log_format()
    handlers = create_log_handlers()
    configure_logging_basic_config(level, format_str, handlers)
    return get_logger(__name__)

