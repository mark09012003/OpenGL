"""主入口文件"""
import tkinter as tk
from utils import setup_logging
from config import ConfigManager
from window_manager import WindowManager
from detection import DetectionManager
from automation import AutomationManager
from gui import MapleStoryAutoPrayerGUI


def initialize_logging():
    """初始化日誌系統"""
    logger = setup_logging()
    logger.info("程式啟動")
    return logger


def create_root_window():
    """創建根視窗"""
    root = tk.Tk()
    return root


def initialize_config_manager(logger):
    """初始化配置管理器"""
    config_manager = ConfigManager(logger=logger)
    return config_manager


def load_configuration(config_manager):
    """載入配置"""
    config = config_manager.load()
    return config


def initialize_window_manager(logger):
    """初始化視窗管理器"""
    window_manager = WindowManager(logger=logger)
    return window_manager


def initialize_detection_manager(window_manager, config, logger):
    """初始化檢測管理器"""
    detection_manager = DetectionManager(window_manager, config=config, logger=logger)
    return detection_manager


def initialize_automation_manager(window_manager, detection_manager, config, logger):
    """初始化自動化管理器"""
    automation_manager = AutomationManager(
        window_manager, detection_manager, config=config, logger=logger
    )
    return automation_manager


def create_gui_application(root, config_manager, window_manager, 
                           detection_manager, automation_manager, logger):
    """創建GUI應用程式"""
    app = MapleStoryAutoPrayerGUI(
        root, config_manager, window_manager, 
        detection_manager, automation_manager, logger
    )
    return app


def start_main_loop(root, logger):
    """啟動主循環"""
    logger.info("GUI初始化完成，開始主循環")
    root.mainloop()


def main():
    """主函數 - 協調所有初始化步驟"""
    # 初始化日誌系統
    logger = initialize_logging()
    
    # 創建根視窗
    root = create_root_window()
    
    # 初始化配置管理器
    config_manager = initialize_config_manager(logger)
    
    # 載入配置
    config = load_configuration(config_manager)
    
    # 初始化視窗管理器
    window_manager = initialize_window_manager(logger)
    
    # 初始化檢測管理器
    detection_manager = initialize_detection_manager(window_manager, config, logger)
    
    # 初始化自動化管理器
    automation_manager = initialize_automation_manager(
        window_manager, detection_manager, config, logger
    )
    
    # 創建GUI應用程式
    app = create_gui_application(
        root, config_manager, window_manager, 
        detection_manager, automation_manager, logger
    )
    
    # 啟動主循環
    start_main_loop(root, logger)


if __name__ == "__main__":
    main()