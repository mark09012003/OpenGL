"""配置管理模組"""
import json
import os
import logging


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json", logger=None):
        self.config_file = config_file
        self.logger = logger or logging.getLogger(__name__)
        self.default_config = {
            "window": "",
            "skills": {
                "prayer_key": "f1",
                "blessing_interval": "0.5",
                "custom_skill1_enabled": False,
                "custom_skill1_key": "f3",
                "angel_blessing": "f2",
                "custom_skill2_enabled": False,
                "custom_skill2_key": "f4",
            },
            "parameters": {
                "fm_wait": "230",
                "portal_wait": "1.5",
                "target_width": "1295",
                "target_height": "759",
                "left_move_time": "0.1",
                "right_move_time": "0.1",
                "fm_check_time": "3.0",
                "debug_image": False,
                "enter_fm": True,
                "move_direction": "left",
                "fixed_move": False,
                "anti_detect_after_fm": False,
                "timed_stop": False,
                "stop_time": "13:00",
            },
            "alarm": {
                "volume": 0.5,
            }
        }
    
    def save(self, config_data):
        """保存配置到檔案"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            self.logger.info("配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    def load(self):
        """從檔案載入配置"""
        try:
            if not os.path.exists(self.config_file):
                self.logger.info("配置檔案不存在，使用預設值")
                return self.default_config.copy()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 合併預設值，確保所有鍵都存在
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            # 合併嵌套字典
            for key in ["skills", "parameters", "alarm"]:
                if key in config:
                    merged_config[key].update(config[key])
            
            self.logger.info("配置已載入")
            return merged_config
        except Exception as e:
            self.logger.error(f"載入配置失敗: {str(e)}")
            return self.default_config.copy()
    
    def get_default(self):
        """獲取預設配置"""
        return self.default_config.copy()

