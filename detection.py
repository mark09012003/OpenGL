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
        self.last_dialog_rgb = None  # 保存最後一次檢測到的對話框RGB平均值
        self.last_dialog_match_ratio = None  # 保存最後一次檢測到的匹配比例
        self.last_character_x = None  # 保存上一次檢測到的角色X位置，用於驗證位置變化
        
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
            self.character_x_tolerance = int(detection_config.get("character_x_tolerance", 100))  # 角色X位置變化容差（像素）
            self.dialog_check_x = int(detection_config.get("dialog_check_x", 500))
            self.dialog_check_y = int(detection_config.get("dialog_check_y", 300))
            self.dialog_check_width = int(detection_config.get("dialog_check_width", 200))
            self.dialog_check_height = int(detection_config.get("dialog_check_height", 100))
            self.dialog_bg_r = int(detection_config.get("dialog_bg_r", 64))
            self.dialog_bg_g = int(detection_config.get("dialog_bg_g", 164))
            self.dialog_bg_b = int(detection_config.get("dialog_bg_b", 223))
            self.dialog_bg_tolerance = int(detection_config.get("dialog_bg_tolerance", 30))
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
            self.character_x_tolerance = 100  # 角色X位置變化容差（像素）
            self.dialog_check_x = 500
            self.dialog_check_y = 300
            self.dialog_check_width = 200
            self.dialog_check_height = 100
            self.dialog_bg_r = 64
            self.dialog_bg_g = 164
            self.dialog_bg_b = 223
            self.dialog_bg_tolerance = 30
    
    def detect_hp_bar_position(self, exclude_x_range: Optional[Tuple[float, float]] = None) -> Optional[Tuple[float, float]]:
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
            
            # 選擇最左邊的連續紅色區間（最可能是血條）
            # 使用配置的寬度範圍
            min_width_threshold = self.hp_bar_min_width
            max_width_threshold = self.hp_bar_max_width
            best_candidate = None
            best_x_start = float('inf')  # 用於找最左邊的候選
            
            # 過濾候選：只考慮寬度在範圍內的候選，並標記離開位置附近的候選為低優先級
            # 但如果候選接近上次位置（在容差範圍內），則不應該標記為低優先級（因為這是自己的角色）
            valid_candidates = []
            low_priority_candidates = []  # 離開位置附近的候選（低優先級）
            
            for candidate in candidates:
                width = candidate['width']
                x_start = candidate['x_start']
                # 只考慮寬度在範圍內的區間
                if min_width_threshold <= width <= max_width_threshold:
                    # 如果提供了排除的X範圍，標記該範圍內的候選為低優先級
                    # 但如果候選接近上次位置（在容差範圍內），則不應該標記為低優先級（因為這是自己的角色）
                    if exclude_x_range is not None:
                        exclude_x_min, exclude_x_max = exclude_x_range
                        if exclude_x_min <= x_start <= exclude_x_max:
                            # 如果候選接近上次位置（在容差範圍內），不標記為低優先級（這是自己的角色）
                            if self.last_character_x is not None:
                                distance = abs(x_start - self.last_character_x)
                                if distance <= self.character_x_tolerance:
                                    # 接近上次位置，不標記為低優先級（這是自己的角色）
                                    self.logger.debug(f"候選血條在排除範圍內但接近上次位置，不標記為低優先級: x={x_start:.0f} (上次位置: {self.last_character_x:.0f}, 距離: {distance:.0f}px)")
                                    valid_candidates.append(candidate)
                                    continue
                            
                            # 標記為低優先級
                            self.logger.debug(f"標記離開位置附近的候選血條為低優先級: x={x_start:.0f} (排除範圍: {exclude_x_min:.0f}~{exclude_x_max:.0f})")
                            low_priority_candidates.append(candidate)
                            continue
                    valid_candidates.append(candidate)
            
            # 如果沒有高優先級候選，使用低優先級候選
            if not valid_candidates and low_priority_candidates:
                self.logger.info("沒有其他候選，使用離開位置附近的血條")
                valid_candidates = low_priority_candidates
            
            # 選擇策略：
            # 1. 如果上一次有記錄的位置，優先選擇與上一次位置最接近的候選（在容差範圍內）
            # 2. 如果沒有接近的候選，選擇最左邊的
            if self.last_character_x is not None:
                # 優先選擇與上一次位置最接近的候選
                closest_candidate = None
                closest_distance = float('inf')
                
                for candidate in valid_candidates:
                    x_start = candidate['x_start']
                    distance = abs(x_start - self.last_character_x)
                    
                    # 如果距離在容差範圍內，優先選擇
                    if distance <= self.character_x_tolerance:
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_candidate = candidate
                
                if closest_candidate is not None:
                    # 找到接近的候選，使用它
                    best_candidate = closest_candidate
                    self.logger.debug(f"選擇與上一次位置最接近的候選 (距離: {closest_distance:.0f}px, 上次位置: {self.last_character_x:.0f})")
                else:
                    # 沒有接近的候選，優先選擇位置變化最小的候選（而不是最左邊的）
                    # 這樣可以避免選擇到完全不相關的血條（如其他玩家的血條）
                    closest_candidate = None
                    closest_distance = float('inf')
                    
                    for candidate in valid_candidates:
                        x_start = candidate['x_start']
                        distance = abs(x_start - self.last_character_x)
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_candidate = candidate
                    
                    if closest_candidate is not None:
                        # 如果位置變化過大（超過容差的2倍），可能是檢測錯誤
                        # 但如果候選在排除範圍內或附近（可能是自己的角色在離開位置附近），則允許較大的位置變化
                        is_in_exclude_range = False
                        is_near_exclude_range = False
                        if exclude_x_range is not None:
                            exclude_x_min, exclude_x_max = exclude_x_range
                            candidate_x = closest_candidate['x_start']
                            # 檢查候選是否在排除範圍內
                            if exclude_x_min <= candidate_x <= exclude_x_max:
                                is_in_exclude_range = True
                            # 檢查候選是否在排除範圍附近（擴展50像素範圍，用於判斷角色正在移動到離開位置）
                            elif (exclude_x_min - 50) <= candidate_x <= (exclude_x_max + 50):
                                is_near_exclude_range = True
                        
                        # 如果上次位置也在排除範圍內或附近，且當前候選也在排除範圍內或附近，可能是自己的角色在移動
                        last_in_exclude_range = False
                        if exclude_x_range is not None and self.last_character_x is not None:
                            exclude_x_min, exclude_x_max = exclude_x_range
                            if (exclude_x_min - 50) <= self.last_character_x <= (exclude_x_max + 50):
                                last_in_exclude_range = True
                        
                        if closest_distance > self.character_x_tolerance * 2:
                            if is_in_exclude_range or (is_near_exclude_range and last_in_exclude_range):
                                # 候選在排除範圍內或附近，且上次位置也在排除範圍附近，可能是自己的角色在移動到離開位置，允許較大的位置變化
                                best_candidate = closest_candidate
                                self.logger.warning(f"沒有找到接近的候選，但候選在離開位置附近，選擇位置變化最小的候選 (位置變化: {closest_distance:.0f}px > {self.character_x_tolerance * 2}px，上次位置: {self.last_character_x:.0f})")
                            else:
                                # 候選不在排除範圍內或附近，且位置變化過大
                                # 但如果沒有提供排除範圍（不是移動到離開位置的情況），可能是剛進入自由市場，位置變化大是正常的
                                # 在這種情況下，清除位置記錄，讓系統重新選擇最左邊的血條
                                if exclude_x_range is None:
                                    self.logger.warning(f"沒有找到接近的候選，且最近候選的位置變化過大 ({closest_distance:.0f}px > {self.character_x_tolerance * 2}px)，可能是剛進入自由市場，清除位置記錄並重新選擇")
                                    self.last_character_x = None
                                    self.last_hp_bar_info = None
                                    # 重新選擇最左邊的候選
                                    for candidate in valid_candidates:
                                        x_start = candidate['x_start']
                                        if x_start < best_x_start:
                                            best_x_start = x_start
                                            best_candidate = candidate
                                    if best_candidate is not None:
                                        self.logger.info(f"清除位置記錄後，選擇最左邊的候選: x={best_candidate['x_start']:.0f}")
                                    else:
                                        return None
                                else:
                                    # 候選不在排除範圍內或附近，且位置變化過大，可能是其他玩家的血條，不選擇
                                    self.logger.warning(f"沒有找到接近的候選，且最近候選的位置變化過大 ({closest_distance:.0f}px > {self.character_x_tolerance * 2}px)，可能是其他玩家的血條，不選擇任何候選")
                                    # 不清除位置記錄，保留上次的位置，等待下次檢測
                                    # 返回None，讓調用者處理
                                    return None
                        else:
                            # 位置變化在可接受範圍內（雖然超過容差但不太大），使用最近的候選
                            best_candidate = closest_candidate
                            self.logger.warning(f"沒有找到接近的候選，選擇位置變化最小的候選 (位置變化: {closest_distance:.0f}px > {self.character_x_tolerance}px，上次位置: {self.last_character_x:.0f})")
                    else:
                        # 沒有候選，選擇最左邊的（作為最後的備選）
                        for candidate in valid_candidates:
                            x_start = candidate['x_start']
                            if x_start < best_x_start:
                                best_x_start = x_start
                                best_candidate = candidate
                        
                        if best_candidate is not None:
                            position_diff = abs(best_candidate['x_start'] - self.last_character_x)
                            self.logger.warning(f"沒有找到接近的候選，選擇最左邊的候選 (位置變化: {position_diff:.0f}px > {self.character_x_tolerance}px，上次位置: {self.last_character_x:.0f})")
            else:
                # 第一次檢測，選擇最左邊的
                for candidate in valid_candidates:
                    x_start = candidate['x_start']
                    if x_start < best_x_start:
                        best_x_start = x_start
                        best_candidate = candidate
            
            if best_candidate is None:
                if self.last_character_x is not None:
                    self.logger.warning(f"未找到寬度在 {min_width_threshold}~{max_width_threshold}px 之間且位置變化在容差範圍內的連續紅色像素區間（容差: ±{self.character_x_tolerance}px，上次位置: {self.last_character_x:.0f}）")
                else:
                    self.logger.warning(f"未找到寬度在 {min_width_threshold}~{max_width_threshold}px 之間的連續紅色像素區間")
                self.last_hp_bar_info = None  # 清空血條信息
                return None
            
            # 角色位置判斷為連續紅色出現的最左邊
            character_x = best_candidate['x_start']  # 人物水平位置為連續紅色區間的最左邊
            character_y = best_candidate['y'] + self.character_y_offset  # 使用配置的人物位置偏移
            
            best_width = best_candidate['width']  # 獲取選中候選的寬度
            
            # 記錄位置變化（如果有上一次記錄）
            position_diff_str = ""
            if self.last_character_x is not None:
                position_diff = abs(character_x - self.last_character_x)
                position_diff_str = f", 位置變化: {position_diff:.0f}px"
            
            self.logger.info(f"檢測到血條 - 血條位置: ({best_candidate['x_start']:.0f}, {best_candidate['y']:.0f}), 寬度: {best_width}px, 人物位置: ({character_x:.0f}, {character_y:.0f}){position_diff_str}")
            
            # 保存血條信息供測試使用
            self.last_hp_bar_info = {
                'x_start': best_candidate['x_start'],
                'x_end': best_candidate['x_end'],
                'y': best_candidate['y'],
                'width': best_width,
                'character_x': character_x,
                'character_y': character_y
            }
            
            # 更新上一次檢測到的角色X位置
            self.last_character_x = character_x
            
            return (character_x, character_y)  # 返回人物位置（相對於視窗）
            
        except Exception as e:
            self.logger.error(f"檢測紅色血條位置失敗: {str(e)}")
            self.last_hp_bar_info = None  # 清空血條信息
            self.all_candidates = []  # 清空候選列表
            return None
    
    def check_free_market_entered(self, exclude_x_range: Optional[Tuple[float, float]] = None) -> bool:
        """檢查是否成功進入自由市場（檢測配置的Y軸位置是否有血條，且血條是自己的）"""
        try:
            # 使用血條檢測來判斷是否進入自由市場
            # 如果能在配置的Y軸位置檢測到血條，說明角色在自由市場中
            # 但需要確保檢測到的血條是自己的（通過位置驗證）
            character_pos = self.detect_hp_bar_position(exclude_x_range=exclude_x_range)
            
            if character_pos is not None:
                # 檢查檢測到的血條是否為自己的
                # 如果上一次有記錄的位置，檢查位置是否接近
                if self.last_hp_bar_info is not None:
                    detected_x = self.last_hp_bar_info['character_x']
                    last_x = self.last_character_x
                    
                if last_x is not None:
                    position_diff = abs(detected_x - last_x)
                    if position_diff > self.character_x_tolerance:
                        # 位置變化過大，可能是其他角色的血條
                        # 清除位置記錄，讓下次檢測可以選擇其他血條
                        self.logger.warning(f"檢測到血條但位置變化過大 ({position_diff:.0f}px > {self.character_x_tolerance}px)，可能是其他角色的血條，清除位置記錄以便重新檢測")
                        self.last_character_x = None
                        self.last_hp_bar_info = None
                        return False
                
                # 檢查血條的Y軸位置是否在配置的Y軸附近（允許一定誤差）
                detected_y = self.last_hp_bar_info['y']
                y_tolerance = 10  # Y軸容差（像素）
                if abs(detected_y - self.hp_bar_y) <= y_tolerance:
                    self.logger.info(f"檢測到自己的血條（y={detected_y:.0f}，配置y={self.hp_bar_y}），已進入自由市場")
                    return True
                else:
                    self.logger.debug(f"檢測到血條但Y軸位置不匹配（檢測y={detected_y:.0f}，配置y={self.hp_bar_y}），視為未進入自由市場")
                    return False
            else:
                self.logger.info(f"未檢測到血條（y={self.hp_bar_y}），未進入自由市場")
                return False
            
        except Exception as e:
            self.logger.error(f"檢查自由市場狀態失敗: {str(e)}")
            return False
    
    def detect_dialog_window(self) -> bool:
        """檢測提示視窗是否存在（通過檢測指定區域的背景顏色）
        
        返回 True 如果檢測到提示視窗，False 否則
        同時將檢測到的實際RGB平均值保存到 self.last_dialog_rgb
        """
        window_handle = self.window_manager.get_window_handle()
        if not window_handle:
            return False
        
        try:
            # 獲取視窗位置和大小
            rect = self.window_manager.get_window_rect()
            if not rect:
                return False
            
            window_x, window_y, window_width, window_height = rect
            
            # 檢查檢測區域是否在視窗範圍內
            check_x = self.dialog_check_x
            check_y = self.dialog_check_y
            check_width = self.dialog_check_width
            check_height = self.dialog_check_height
            
            if (check_x < 0 or check_y < 0 or 
                check_x + check_width > window_width or 
                check_y + check_height > window_height):
                self.logger.warning(f"提示視窗檢測區域超出視窗範圍")
                return False
            
            # 截圖檢測區域
            screenshot = ImageGrab.grab(bbox=(
                int(window_x + check_x), 
                int(window_y + check_y), 
                int(window_x + check_x + check_width), 
                int(window_y + check_y + check_height)
            ))
            
            # 轉換為RGB數組
            img_array = np.array(screenshot)
            
            # 提取RGB通道
            r_channel = img_array[:, :, 0]
            g_channel = img_array[:, :, 1]
            b_channel = img_array[:, :, 2]
            
            # 檢查像素是否接近配置的背景顏色（允許容差）
            tolerance = self.dialog_bg_tolerance
            color_match = (
                (np.abs(r_channel - self.dialog_bg_r) <= tolerance) &
                (np.abs(g_channel - self.dialog_bg_g) <= tolerance) &
                (np.abs(b_channel - self.dialog_bg_b) <= tolerance)
            )
            
            # 計算匹配的像素比例
            total_pixels = check_width * check_height
            matched_pixels = np.sum(color_match)
            match_ratio = matched_pixels / total_pixels if total_pixels > 0 else 0
            
            # 計算實際檢測區域的平均RGB值
            avg_r = int(np.mean(r_channel))
            avg_g = int(np.mean(g_channel))
            avg_b = int(np.mean(b_channel))
            
            # 保存檢測結果供測試使用
            self.last_dialog_rgb = (avg_r, avg_g, avg_b)
            self.last_dialog_match_ratio = match_ratio
            
            # 如果匹配比例超過50%，認為檢測到提示視窗
            threshold = 0.5
            detected = match_ratio >= threshold
            
            if detected:
                self.logger.info(f"檢測到提示視窗 (匹配比例: {match_ratio:.2%}, 實際RGB: ({avg_r}, {avg_g}, {avg_b}))")
            else:
                self.logger.debug(f"未檢測到提示視窗 (匹配比例: {match_ratio:.2%}, 實際RGB: ({avg_r}, {avg_g}, {avg_b}))")
            
            return detected
            
        except Exception as e:
            self.logger.error(f"檢測提示視窗失敗: {str(e)}", exc_info=True)
            return False

