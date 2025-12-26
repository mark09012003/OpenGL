"""主入口文件"""
import tkinter as tk
from utils import setup_logging
from config import ConfigManager
from window_manager import WindowManager
from detection import DetectionManager
from automation import AutomationManager
from gui import MapleStoryAutoPrayerGUI


def main():
    """主函數"""
    # 設置日誌
    logger = setup_logging()
    logger.info("程式啟動")
    
    # 創建根視窗
    root = tk.Tk()
    
    # 創建管理器實例
    config_manager = ConfigManager(logger=logger)
    # 載入配置
    config = config_manager.load()
    
    window_manager = WindowManager(logger=logger)
    detection_manager = DetectionManager(window_manager, config=config, logger=logger)
    automation_manager = AutomationManager(window_manager, detection_manager, config=config, logger=logger)
    
    # 創建GUI並整合所有管理器
    app = MapleStoryAutoPrayerGUI(
        root, config_manager, window_manager, 
        detection_manager, automation_manager, logger
    )
    
    logger.info("GUI初始化完成，開始主循環")
    root.mainloop()


if __name__ == "__main__":
    main()

