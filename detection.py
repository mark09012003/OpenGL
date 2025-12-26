"""圖像檢測模組"""
import win32gui
import logging
import numpy as np
from PIL import ImageGrab
from typing import Optional, Tuple


class DetectionManager:
    """圖像檢測管理器"""
    
    def __init__(self, window_manager, config=None, logger=None):
        self.window_manager = window_manager
        self.logger = logger or logging.getLogger(__name__)
        self.last_hp_bar_info = None  # 保存最後一次檢測到的血條信息
        self.all_candidates = []  # 保存所有檢測到的候選（包括未達門檻的）
        
        # 從配置中讀取檢測參數
        if config and "detection" in config:
            detection_config = config["detection"]
            self.hp_bar_y = int(detection_config.get("hp_bar_y", 445))
            self.hp_bar_min_width = int(detection_config.get("hp_bar_min_width", 40))
            self.hp_bar_max_width = int(detection_config.get("hp_bar_max_width", 43))
            self.color_r_min = int(detection_config.get("color_r_min", 150))
            self.color_r_max = int(detection_config.get("color_r_max", 255))
            self.color_g_max = int(detection_config.get("color_g_max", 100))
            self.color_b_max = int(detection_config.get("color_b_max", 100))
            self.color_r_g_ratio = float(detection_config.get("color_r_g_ratio", 1.5))
            self.color_r_b_ratio = float(detection_config.get("color_r_b_ratio", 1.5))
            self.pixel_gap_tolerance = int(detection_config.get("pixel_gap_tolerance", 2))
            self.character_y_offset = int(detection_config.get("character_y_offset", 15))
        else:
            # 預設值
            self.hp_bar_y = 445
            self.hp_bar_min_width = 40
            self.hp_bar_max_width = 43
            self.color_r_min = 150
            self.color_r_max = 255
            self.color_g_max = 100
            self.color_b_max = 100
            self.color_r_g_ratio = 1.5
            self.color_r_b_ratio = 1.5
            self.pixel_gap_tolerance = 2
            self.character_y_offset = 15
    
    def detect_hp_bar_position(self) -> Optional[Tuple[float, float]]:
        """檢測角色頭頂上方的紅色血條位置，用於判斷人物位置（相對於視窗）"""
        window_handle = self.window_manager.get_window_handle()
        if not window_handle:
            return None
        
        try:
            # 獲取視窗位置和大小
            rect = self.window_manager.get_window_rect()
            if not rect:
                return None
            
            window_x, window_y, window_width, window_height = rect
            
            # 截圖整個視窗
            screenshot = ImageGrab.grab(bbox=(
                int(window_x), 
                int(window_y), 
                int(window_x + window_width), 
                int(window_y + window_height)
            ))
            
            # 轉換為RGB數組
            img_array = np.array(screenshot)
            
            # 定義紅色血條的顏色範圍
            r_channel = img_array[:, :, 0]
            g_channel = img_array[:, :, 1]
            b_channel = img_array[:, :, 2]
            
            # 定義紅色區間：血條應該是鮮紅色（使用配置的顏色閾值）
            red_mask = (r_channel >= self.color_r_min) & (r_channel <= self.color_r_max) & \
                      (g_channel < self.color_g_max) & (b_channel < self.color_b_max) & \
                      (r_channel > g_channel * self.color_r_g_ratio) & (r_channel > b_channel * self.color_r_b_ratio)
            
            # 使用配置的 Y 軸位置檢查血條
            target_y = self.hp_bar_y
            
            # 檢查目標 Y 軸是否在視窗範圍內
            if target_y < 0 or target_y >= window_height:
                self.logger.warning(f"目標Y座標 {target_y} 超出視窗範圍 (0-{window_height-1})")
                return None
            
            # 只在配置的 Y 軸位置檢查紅色像素
            row_red_pixels = np.where(red_mask[target_y, :])[0]
            
            if len(row_red_pixels) == 0:
                self.logger.warning(f"在 y={target_y} 未檢測到紅色像素")
                self.last_hp_bar_info = None  # 清空血條信息
                self.all_candidates = []  # 清空候選列表
                return None
            
            # 找出目標 Y 軸位置這一行中所有連續的紅色像素區間
            y = target_y
            candidates = []
            
            if len(row_red_pixels) > 0:
                start_x = row_red_pixels[0]
                end_x = row_red_pixels[0]
                
                for i in range(1, len(row_red_pixels)):
                    if row_red_pixels[i] - end_x <= self.pixel_gap_tolerance:  # 使用配置的像素間隔容差
                        end_x = row_red_pixels[i]
                    else:
                        # 找到一個連續的紅色區間，記錄它
                        width = end_x - start_x + 1
                        candidates.append({
                            'y': y,
                            'x_start': start_x,
                            'x_end': end_x,
                            'width': width
                        })
                        start_x = row_red_pixels[i]
                        end_x = row_red_pixels[i]
                
                # 處理最後一個區間
                width = end_x - start_x + 1
                candidates.append({
                    'y': y,
                    'x_start': start_x,
                    'x_end': end_x,
                    'width': width
                })
            
            if not candidates:
                self.logger.warning(f"在 y={target_y} 未找到連續的紅色像素區間")
                self.last_hp_bar_info = None  # 清空血條信息
                self.all_candidates = []  # 清空候選列表
                return None
            
            # 保存所有候選（包括未達門檻的）供測試和懸浮框使用
            self.all_candidates = candidates.copy()
            
            # 選擇最長的連續紅色區間（最可能是血條）
            # 使用配置的寬度範圍
            min_width_threshold = self.hp_bar_min_width
            max_width_threshold = self.hp_bar_max_width
            best_candidate = None
            best_width = 0
            
            for candidate in candidates:
                width = candidate['width']
                # 只考慮寬度在 40~43px 之間的區間
                if min_width_threshold <= width <= max_width_threshold and width > best_width:
                    best_width = width
                    best_candidate = candidate
            
            if best_candidate is None:
                self.logger.warning(f"未找到寬度在 {min_width_threshold}~{max_width_threshold}px 之間的連續紅色像素區間")
                self.last_hp_bar_info = None  # 清空血條信息
                return None
            
            # 角色位置判斷為連續紅色出現的最左邊
            character_x = best_candidate['x_start']  # 人物水平位置為連續紅色區間的最左邊
            character_y = best_candidate['y'] + self.character_y_offset  # 使用配置的人物位置偏移
            
            self.logger.info(f"檢測到血條 - 血條位置: ({best_candidate['x_start']:.0f}, {best_candidate['y']:.0f}), 寬度: {best_width}px, 人物位置: ({character_x:.0f}, {character_y:.0f})")
            
            # 保存血條信息供測試使用
            self.last_hp_bar_info = {
                'x_start': best_candidate['x_start'],
                'x_end': best_candidate['x_end'],
                'y': best_candidate['y'],
                'width': best_width,
                'character_x': character_x,
                'character_y': character_y
            }
            
            return (character_x, character_y)  # 返回人物位置（相對於視窗）
            
        except Exception as e:
            self.logger.error(f"檢測紅色血條位置失敗: {str(e)}")
            self.last_hp_bar_info = None  # 清空血條信息
            self.all_candidates = []  # 清空候選列表
            return None
    
    def check_free_market_entered(self) -> bool:
        """檢查是否成功進入自由市場（檢測配置的Y軸位置是否有血條）"""
        try:
            # 使用血條檢測來判斷是否進入自由市場
            # 如果能在配置的Y軸位置檢測到血條，說明角色在自由市場中
            character_pos = self.detect_hp_bar_position()
            
            if character_pos is not None:
                self.logger.info(f"檢測到血條（y={self.hp_bar_y}），已進入自由市場")
                return True
            else:
                self.logger.info(f"未檢測到血條（y={self.hp_bar_y}），未進入自由市場")
                return False
            
        except Exception as e:
            self.logger.error(f"檢查自由市場狀態失敗: {str(e)}")
            return False

