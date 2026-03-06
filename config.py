"""配置管理模組"""
import json
import os
import logging


def create_default_config():
    """創建預設配置字典"""
    return {
            "window": "MapleStory Worlds-Artale (繁體中文版)",
            "skills": {
                "prayer_key": "1",
                "blessing_interval": "0.5",
                "custom_skill1_enabled": False,
                "custom_skill1_key": "3",
                "angel_blessing": "2",
                "custom_skill2_enabled": False,
                "custom_skill2_key": "f4",
            },
            "parameters": {
                "fm_wait": "230",
                "portal_wait": "1.5",
                "target_width": "1295",
                "target_height": "759",
                "left_move_time": "0.01",
                "right_move_time": "0.01",
                "fm_check_time": "1.0",
                "debug_image": False,
                "auto_stop_enabled": False,
                "auto_stop_time": "11:26",
                "enter_fm": False,
                "use_floating_window": True,
                "move_direction": "left",
                "fixed_move": True,
                "anti_detect_after_fm": True,
                "timed_stop": False,
                "stop_time": "13:00",
            },
            "detection": {
                "hp_bar_y": 445,
                "hp_bar_min_width": 20,
                "hp_bar_max_width": 45,
                "color_r_min": 150,
                "color_r_max": 255,
                "color_g_max": 100,
                "color_b_max": 100,
                "color_r_g_ratio": 1.5,
                "color_r_b_ratio": 1.5,
                "pixel_gap_tolerance": 2,
                "character_y_offset": 15,
                "character_x_tolerance": 100,  # 角色X位置變化容差（像素），超過此值視為其他角色
                "dialog_check_x": 500,
                "dialog_check_y": 300,
                "dialog_check_width": 20,
                "dialog_check_height": 20,
                "dialog_bg_r": 68,
                "dialog_bg_g": 136,
                "dialog_bg_b": 187,
                "dialog_bg_tolerance": 30
            },
            "automation": {
                "exit_target_x": 237,
                "fm_button_x": 980,
                "fm_button_y": 720,
                "key_press_wait": 0.2,
                "key_press_duration": 0.3,
                "sleep_check_interval": 0.1,
                "button_click_wait": 0.2,
                "button_click_delay": 0.1,
                "retry_wait": 0.5,
                "move_check_interval": 0.3,
                "exit_wait": 0.5,
                "exit_key_duration": 0.3,
                "exit_animation_wait": 2.0,
                "enter_retry_wait": 3.0,
                "move_tolerance": 20,
                "move_max_duration": 30.0,
                "skill_interval_random_range": 20.0,
                "anti_detect_min_moves": 0,
                "anti_detect_max_moves": 1,
                "anti_detect_interval": 0.1,
                "dialog_close_button_x": 830,
                "dialog_close_button_y": 466
            },
            "alarm": {
                "volume": 0.5,
            }
        }


def check_config_file_exists(config_file):
    """檢查配置檔案是否存在"""
    return os.path.exists(config_file)


def read_config_file(config_file):
    """讀取配置檔案內容"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_config_copy(config):
    """創建配置的副本"""
    return config.copy()


def merge_top_level_config(default_config, loaded_config):
    """合併頂層配置"""
    merged_config = create_config_copy(default_config)
    merged_config.update(loaded_config)
    return merged_config


def get_nested_config_keys():
    """獲取需要合併的嵌套配置鍵列表"""
    return ["skills", "parameters", "detection", "automation", "alarm"]


def merge_nested_config(merged_config, loaded_config, nested_keys):
    """合併嵌套配置"""
    for key in nested_keys:
        if key in loaded_config:
            merged_config[key].update(loaded_config[key])


def write_config_file(config_file, config_data):
    """寫入配置檔案"""
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json", logger=None):
        self.config_file = config_file
        self.logger = logger or logging.getLogger(__name__)
        self.default_config = create_default_config()
    
    def save(self, config_data):
        """保存配置到檔案"""
        try:
            write_config_file(self.config_file, config_data)
            self.logger.info("配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    def load(self):
        """從檔案載入配置"""
        try:
            if not check_config_file_exists(self.config_file):
                self.logger.info("配置檔案不存在，使用預設值")
                return create_config_copy(self.default_config)
            
            loaded_config = read_config_file(self.config_file)
            
            # 合併預設值，確保所有鍵都存在
            merged_config = merge_top_level_config(self.default_config, loaded_config)
            
            # 合併嵌套字典
            nested_keys = get_nested_config_keys()
            merge_nested_config(merged_config, loaded_config, nested_keys)
            
            self.logger.info("配置已載入")
            return merged_config
        except Exception as e:
            self.logger.error(f"載入配置失敗: {str(e)}")
            return create_config_copy(self.default_config)
    
    def get_default(self):
        """獲取預設配置"""
        return create_config_copy(self.default_config)

