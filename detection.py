"""圖像檢測模組"""
import win32gui
import logging
import numpy as np
from PIL import ImageGrab
from typing import Optional, Tuple


class DetectionManager:
    """圖像檢測管理器"""
    
    def __init__(self, window_manager, logger=None):
        self.window_manager = window_manager
        self.logger = logger or logging.getLogger(__name__)
    
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
            
            # 定義紅色區間：血條應該是鮮紅色
            red_mask = (r_channel >= 150) & (r_channel <= 255) & \
                      (g_channel < 100) & (b_channel < 100) & \
                      (r_channel > g_channel * 1.5) & (r_channel > b_channel * 1.5)
            
            # 只在 y=445 這一行檢查血條
            target_y = 445
            
            # 檢查 y=445 是否在視窗範圍內
            if target_y < 0 or target_y >= window_height:
                self.logger.warning(f"目標Y座標 {target_y} 超出視窗範圍 (0-{window_height-1})")
                return None
            
            # 只在 y=445 這一行檢查紅色像素
            row_red_pixels = np.where(red_mask[target_y, :])[0]
            
            if len(row_red_pixels) == 0:
                self.logger.warning(f"在 y={target_y} 未檢測到紅色像素")
                return None
            
            # 找出 y=445 這一行中所有連續的紅色像素區間
            y = target_y
            candidates = []
            
            if len(row_red_pixels) > 0:
                start_x = row_red_pixels[0]
                end_x = row_red_pixels[0]
                
                for i in range(1, len(row_red_pixels)):
                    if row_red_pixels[i] - end_x <= 2:  # 允許2像素間隔
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
                return None
            
            # 選擇最長的連續紅色區間（最可能是血條）
            best_candidate = None
            best_width = 0
            
            for candidate in candidates:
                width = candidate['width']
                if width > best_width:
                    best_width = width
                    best_candidate = candidate
            
            if best_candidate is None:
                self.logger.warning("未找到連續的紅色像素區間")
                return None
            
            # 角色位置判斷為連續紅色出現的最左邊
            character_x = best_candidate['x_start']  # 人物水平位置為連續紅色區間的最左邊
            character_y = best_candidate['y'] + 15  # 人物位置在血條下方約15像素
            
            self.logger.info(f"檢測到血條 - 血條位置: ({best_candidate['x_start']:.0f}, {best_candidate['y']:.0f}), 人物位置: ({character_x:.0f}, {character_y:.0f})")
            return (character_x, character_y)  # 返回人物位置（相對於視窗）
            
        except Exception as e:
            self.logger.error(f"檢測紅色血條位置失敗: {str(e)}")
            return None
    
    def check_free_market_entered(self) -> bool:
        """檢查是否成功進入自由市場（檢測y=445是否有血條）"""
        try:
            # 使用血條檢測來判斷是否進入自由市場
            # 如果能在y=445檢測到血條，說明角色在自由市場中
            character_pos = self.detect_hp_bar_position()
            
            if character_pos is not None:
                self.logger.info("檢測到血條（y=445），已進入自由市場")
                return True
            else:
                self.logger.info("未檢測到血條（y=445），未進入自由市場")
                return False
            
        except Exception as e:
            self.logger.error(f"檢查自由市場狀態失敗: {str(e)}")
            return False

