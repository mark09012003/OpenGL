"""自動化邏輯模組"""
import pyautogui
import time
import random
import logging
from typing import Optional, Callable, Tuple


def get_automation_config_value(config, key, default_value):
    """從配置中獲取自動化參數值"""
    if config and "automation" in config:
        automation_config = config["automation"]
        return automation_config.get(key, default_value)
    return default_value


def configure_pyautogui_safety():
    """配置pyautogui安全模式"""
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1


def validate_key(key):
    """驗證按鍵是否有效"""
    return key is not None and key != ""


def press_key_down(key):
    """按下按鍵"""
    pyautogui.keyDown(key)


def press_key_up(key):
    """釋放按鍵"""
    pyautogui.keyUp(key)


def calculate_sleep_chunks(sleep_time, chunk_size=0.1):
    """計算睡眠分塊數量"""
    return max(1, int(sleep_time / chunk_size))


def calculate_chunk_duration(sleep_time, sleep_chunks):
    """計算每個分塊的持續時間"""
    return sleep_time / sleep_chunks


def calculate_remaining_time(duration, elapsed):
    """計算剩餘時間"""
    return max(0.0, duration - elapsed)


def calculate_button_absolute_position(window_x, window_y, button_x, button_y):
    """計算按鈕的絕對座標"""
    absolute_x = window_x + button_x
    absolute_y = window_y + button_y
    return absolute_x, absolute_y


def click_button(button_x, button_y):
    """點擊按鈕"""
    pyautogui.click(button_x, button_y)


def calculate_exclude_range(target_x, tolerance):
    """計算排除範圍"""
    exclude_x_min = target_x - tolerance
    exclude_x_max = target_x + tolerance
    return exclude_x_min, exclude_x_max


def calculate_distance_to_target(current_x, target_x):
    """計算到目標位置的距離"""
    return abs(current_x - target_x)


def is_position_reached(current_x, target_x, tolerance):
    """檢查是否已到達目標位置"""
    return calculate_distance_to_target(current_x, target_x) <= tolerance


def determine_movement_direction(current_x, target_x):
    """判斷移動方向"""
    if current_x < target_x:
        return 'right'
    elif current_x > target_x:
        return 'left'
    else:
        return None


def release_all_movement_keys():
    """釋放所有移動按鍵"""
    pyautogui.keyUp('left')
    pyautogui.keyUp('right')


def calculate_skill_interval(base_interval, random_range):
    """計算技能執行間隔（基礎間隔 ±隨機範圍）"""
    random_offset = random.uniform(-random_range, random_range)
    interval = max(1.0, base_interval + random_offset)
    return interval


def generate_random_move_count(min_moves, max_moves):
    """生成隨機移動次數"""
    return random.randint(min_moves, max_moves)


def get_move_key_for_direction(direction):
    """根據方向獲取移動按鍵"""
    return 'left' if direction == "left" else 'right'


def calculate_dialog_button_absolute_position(window_x, window_y, button_x, button_y):
    """計算對話框按鈕的絕對座標"""
    absolute_x = int(window_x + button_x)
    absolute_y = int(window_y + button_y)
    return absolute_x, absolute_y


class AutomationManager:
    """自動化管理器"""
    
    def __init__(self, window_manager, detection_manager, config=None, logger=None):
        self.window_manager = window_manager
        self.detection_manager = detection_manager
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.last_entered_free_market = False
        self.just_exited_free_market = False  # 標記：剛剛離開自由市場（跳過重新執行邏輯）
        
        # 從配置中讀取自動化參數
        if config and "automation" in config:
            automation_config = config["automation"]
            self.exit_target_x = int(automation_config.get("exit_target_x", 250))
            self.fm_button_x = int(automation_config.get("fm_button_x", 980))
            self.fm_button_y = int(automation_config.get("fm_button_y", 720))
            self.key_press_wait = float(automation_config.get("key_press_wait", 0.2))
            self.key_press_duration = float(automation_config.get("key_press_duration", 0.3))
            self.sleep_check_interval = float(automation_config.get("sleep_check_interval", 0.1))
            self.button_click_wait = float(automation_config.get("button_click_wait", 0.2))
            self.button_click_delay = float(automation_config.get("button_click_delay", 0.1))
            self.retry_wait = float(automation_config.get("retry_wait", 0.5))
            self.move_check_interval = float(automation_config.get("move_check_interval", 0.3))
            self.exit_wait = float(automation_config.get("exit_wait", 0.5))
            self.exit_key_duration = float(automation_config.get("exit_key_duration", 0.3))
            self.exit_animation_wait = float(automation_config.get("exit_animation_wait", 1.0))
            self.enter_retry_wait = float(automation_config.get("enter_retry_wait", 3.0))
            self.move_tolerance = int(automation_config.get("move_tolerance", 20))
            self.move_max_duration = int(automation_config.get("move_max_duration", 30))
            self.skill_interval_random_range = float(automation_config.get("skill_interval_random_range", 20))
            self.anti_detect_min_moves = int(automation_config.get("anti_detect_min_moves", 0))
            self.anti_detect_max_moves = int(automation_config.get("anti_detect_max_moves", 1))
            self.anti_detect_interval = float(automation_config.get("anti_detect_interval", 0.1))
            self.dialog_close_button_x = int(automation_config.get("dialog_close_button_x", 600))
            self.dialog_close_button_y = int(automation_config.get("dialog_close_button_y", 400))
        else:
            # 預設值
            self.exit_target_x = 250
            self.fm_button_x = 980
            self.fm_button_y = 720
            self.key_press_wait = 0.2
            self.key_press_duration = 0.3
            self.sleep_check_interval = 0.1
            self.button_click_wait = 0.2
            self.button_click_delay = 0.1
            self.retry_wait = 0.5
            self.move_check_interval = 0.1
            self.exit_wait = 0.5
            self.exit_key_duration = 0.3
            self.exit_animation_wait = 1.0
            self.enter_retry_wait = 3.0
            self.move_tolerance = 20
            self.move_max_duration = 30
            self.skill_interval_random_range = 20
            self.anti_detect_min_moves = 0
            self.anti_detect_max_moves = 1
            self.anti_detect_interval = 0.1
            self.dialog_close_button_x = 600
            self.dialog_close_button_y = 400
            self.dialog_close_button_x = 600
            self.dialog_close_button_y = 400
        
        # 設定pyautogui安全模式
        configure_pyautogui_safety()
        
        # 跳過等待標誌
        self.skip_wait = False
        self.current_wait_remaining = None  # 當前剩餘等待時間（None表示沒有在等待）
    
    def send_key_press(self, key: str, skill_name: str = "") -> bool:
        """發送按鍵（按壓0.3秒後放開）"""
        if not self.is_running:
            return False
            
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            # 使用可中斷的sleep（使用配置的等待時間）
            if not self._sleep_with_check(self.key_press_wait):
                return False
            
            if not validate_key(key):
                return False
            
            # 按壓按鍵後放開（使用配置的持續時間，可中斷）
            press_key_down(key)
            if not self._sleep_with_check(self.key_press_duration):
                press_key_up(key)
                return False
            press_key_up(key)
            
            if skill_name:
                self.logger.info(f"已執行{skill_name}")
            
            return True
        except Exception as e:
            self.logger.error(f"發送按鍵失敗: {str(e)}")
            return False
    
    def _sleep_with_check(self, duration: float, check_interval: float = None, update_countdown: bool = False) -> bool:
        """可中斷的sleep，返回False表示被中斷"""
        if check_interval is None:
            check_interval = self.sleep_check_interval
        elapsed = 0.0
        
        # 只有當 update_countdown=True 時才更新倒數時間（用於主要循環等待）
        if update_countdown:
            self.current_wait_remaining = duration  # 初始化剩餘時間
            self.logger.info(f"開始循環等待倒數：{duration:.1f} 秒，current_wait_remaining={self.current_wait_remaining}")
        
        while elapsed < duration:
            if not self.is_running:
                if update_countdown:
                    self.current_wait_remaining = None
                return False
            
            # 計算本次 sleep 的時間
            sleep_time = min(check_interval, duration - elapsed)
            
            # 在 sleep 之前更新剩餘時間，讓 GUI 能及時看到
            if update_countdown:
                remaining = max(0.0, duration - elapsed)
                self.current_wait_remaining = remaining
                # 每5秒記錄一次，避免日誌過多
                if int(elapsed) % 5 == 0:
                    self.logger.debug(f"循環等待中，剩餘時間: {remaining:.1f} 秒")
            
            # 在 sleep 期間分段檢查，以便及時響應 skip_wait
            sleep_chunks = calculate_sleep_chunks(sleep_time, chunk_size=0.1)  # 每0.1秒檢查一次
            chunk_duration = calculate_chunk_duration(sleep_time, sleep_chunks)
            
            for _ in range(sleep_chunks):
                # 檢查是否要跳過等待
                if self.skip_wait:
                    self.skip_wait = False
                    if update_countdown:
                        self.current_wait_remaining = None
                    self.logger.info("已跳過剩餘等待時間")
                    return True
                
                if not self.is_running:
                    if update_countdown:
                        self.current_wait_remaining = None
                    return False
                
                time.sleep(chunk_duration)
                elapsed += chunk_duration
                
                # 更新剩餘時間
                if update_countdown:
                    remaining = calculate_remaining_time(duration, elapsed)
                    self.current_wait_remaining = remaining
        
        if update_countdown:
            self.current_wait_remaining = None  # 等待完成，清除倒數
            self.logger.info("循環等待完成")
        return True
    
    def skip_current_wait(self):
        """跳過當前等待時間"""
        self.skip_wait = True
        self.logger.info("請求跳過當前等待時間")
    
    def click_free_market_button(self) -> str:
        """點擊自由市場按鈕一次，並檢測結果
        
        Returns:
            'success': 檢測到血條（成功進入自由市場）
            'dialog': 檢測到確認視窗（角色已在自由市場）
            'failed': 未檢測到血條也沒檢測到確認視窗（沒有成功進入）
        """
        if not self.window_manager.is_valid():
            return 'failed'
        
        try:
            if not self.window_manager.bring_to_front():
                return 'failed'
            
            if not self._sleep_with_check(self.button_click_wait):
                return 'failed'
            
            # 獲取視窗位置
            rect = self.window_manager.get_window_rect()
            if not rect:
                return 'failed'
            
            window_x, window_y, _, _ = rect
            
            # 使用配置的自由市場按鈕位置
            button_x, button_y = calculate_button_absolute_position(
                window_x, window_y, self.fm_button_x, self.fm_button_y
            )
            
            # 點擊按鈕一次
            self.logger.info(f"準備點擊自由市場按鈕 (按鈕位置: {button_x:.0f}, {button_y:.0f})")
            click_button(button_x, button_y)
            
            # 點擊後等待，讓過場動畫有緩衝時間，確認視窗有時間出現
            self.logger.info("等待2秒讓過場動畫完成")
            if not self._sleep_with_check(2.0):
                return 'failed'
            
            # 檢測結果1：檢查是否有確認視窗出現
            detected_dialog = self.detection_manager.detect_dialog_window()
            if detected_dialog:
                self.logger.warning("點擊自由市場按鈕後檢測到確認視窗，代表角色已在自由市場內")
                return 'dialog'
            
            # 檢測結果2：檢查是否檢測到血條（成功進入自由市場）
            character_pos = self.detection_manager.detect_hp_bar_position()
            if character_pos is not None:
                self.logger.info("點擊自由市場按鈕後檢測到血條，成功進入自由市場")
                return 'success'
            
            # 檢測結果3：未檢測到血條也沒檢測到確認視窗
            self.logger.warning("點擊自由市場按鈕後未檢測到血條也沒檢測到確認視窗，沒有成功進入自由市場")
            return 'failed'
            
        except Exception as e:
            self.logger.error(f"點擊自由市場按鈕失敗: {str(e)}")
            return 'failed'
    
    def move_to_target_position(self, target_x: float, tolerance: int = None, 
                                max_duration: int = None, check_hp_bar_on_fail: bool = False,
                                exclude_x_range: Optional[Tuple[float, float]] = None) -> bool:
        """使用方向鍵移動角色直到到達目標X位置（使用配置的容差和最大持續時間）"""
        if tolerance is None:
            tolerance = self.move_tolerance
        if max_duration is None:
            max_duration = self.move_max_duration
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            start_time = time.time()
            current_key = None
            last_character_x = None  # 記錄上一次檢測到的角色X位置
            stuck_count = 0  # 記錄血條位置不變的次數
            no_change_count = 0  # 記錄連續多少次位置沒有變化（用於判斷是否到達最左邊或誤判）
            
            self.logger.info(f"開始移動到目標位置 X={target_x:.0f} (誤差範圍: ±{tolerance}像素)")
            
            while (time.time() - start_time) < max_duration:
                if not self.is_running:
                    break
                
                # 檢測當前人物位置（提高判斷頻率，使用更短的間隔）
                character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=exclude_x_range)
                
                if character_pos is None:
                    # 如果檢測失敗（可能是位置變化過大，系統拒絕選擇錯誤的血條），等待一小段時間後重試
                    if last_character_x is not None:
                        self.logger.warning("檢測到血條位置變化過大，可能是其他玩家的血條，等待後重試")
                        if not self._sleep_with_check(0.2):
                            break
                        continue
                    # 如果沒有上次位置記錄，可能是剛進入自由市場或第一次檢測，清除位置記錄後重試
                    if self.detection_manager.last_character_x is None:
                        self.logger.warning("無法檢測到血條，且沒有上次位置記錄，可能是剛進入自由市場，清除位置記錄後重試")
                        self.detection_manager.last_character_x = None
                        self.detection_manager.last_hp_bar_info = None
                        if not self._sleep_with_check(0.2):
                            break
                        continue
                    # 只有在 check_hp_bar_on_fail=True 時才終止程式（用於離開自由市場時）
                    if check_hp_bar_on_fail:
                        # 但在終止前，先嘗試清除位置記錄並重新檢測一次
                        self.logger.warning("無法檢測到血條，清除位置記錄並重新檢測一次")
                        self.detection_manager.last_character_x = None
                        self.detection_manager.last_hp_bar_info = None
                        if not self._sleep_with_check(0.2):
                            break
                        # 重新檢測一次
                        character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=exclude_x_range)
                        if character_pos is None:
                            # 重新檢測仍然失敗，終止流程（可能是角色離開隊伍或檢測錯誤，這是正常終止條件）
                            self.logger.info("重新檢測後仍無法檢測到血條，可能是角色離開隊伍（正常終止）")
                            self.is_running = False
                            if current_key:
                                pyautogui.keyUp(current_key)
                                current_key = None
                            pyautogui.keyUp('left')
                            pyautogui.keyUp('right')
                            return False
                        else:
                            # 重新檢測成功，繼續執行
                            self.logger.info("清除位置記錄後重新檢測成功，繼續移動")
                            current_x, _ = character_pos
                            last_character_x = current_x
                            continue
                    else:
                        # 其他情況下，只記錄警告並繼續嘗試
                        self.logger.warning("無法檢測到血條，繼續嘗試...")
                    
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    pyautogui.keyUp('left')
                    pyautogui.keyUp('right')
                    
                    if check_hp_bar_on_fail:
                        return False
                    else:
                        # 繼續嘗試，等待後重試（使用配置的重試等待時間）
                        if not self._sleep_with_check(self.retry_wait):
                            break
                        continue
                
                current_x, _ = character_pos
                
                # 驗證血條是否正確：當執行角色移動時，正確的血條應該會向目標x靠近而非遠離
                if last_character_x is not None:
                    # 計算位置變化
                    position_change = abs(current_x - last_character_x)
                    # 允許小的位置變化（±2像素）視為正常（可能是檢測誤差或角色剛開始移動）
                    position_change_threshold = 2
                    
                    # 檢查位置是否長時間沒有變化
                    if position_change < position_change_threshold:
                        no_change_count += 1
                    else:
                        no_change_count = 0  # 位置有變化，重置計數
                    
                    # 如果位置長時間沒有變化（連續5次檢測，約0.5秒），判斷是到達最左邊還是誤判
                    if no_change_count >= 5:
                        if current_x < 20:  # 如果血條在很左邊的位置（x < 20），可能是已經到達最左邊
                            self.logger.info(f"血條位置長時間不變且在最左邊 (x={current_x:.0f})，可能是已經到達最左邊，停止移動")
                            if current_key:
                                pyautogui.keyUp(current_key)
                                current_key = None
                            pyautogui.keyUp('left')
                            pyautogui.keyUp('right')
                            # 檢查是否已經到達目標位置（或接近）
                            distance = abs(current_x - target_x)
                            if distance <= tolerance:
                                self.logger.info(f"已到達目標位置 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                                return True
                            else:
                                self.logger.warning(f"已到達最左邊但未到達目標位置 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})，可能無法繼續移動")
                                return False
                        else:
                            # 如果不在最左邊，且位置長時間不變，可能是錯誤的血條
                            self.logger.warning(f"血條位置長時間不變 (x={current_x:.0f})，且不在最左邊，可能是其他玩家的血條，清除位置記錄並重新檢測")
                            # 清除當前檢測到的血條信息，強制重新檢測
                            self.detection_manager.last_character_x = None
                            self.detection_manager.last_hp_bar_info = None
                            no_change_count = 0
                            
                            # 排除當前檢測到的血條位置（±30像素範圍），強制選擇其他血條
                            exclude_current_x_min = current_x - 30
                            exclude_current_x_max = current_x + 30
                            
                            # 合併原有的排除範圍和當前血條位置的排除範圍
                            if exclude_x_range is not None:
                                exclude_x_min = min(exclude_x_range[0], exclude_current_x_min)
                                exclude_x_max = max(exclude_x_range[1], exclude_current_x_max)
                            else:
                                exclude_x_min = exclude_current_x_min
                                exclude_x_max = exclude_current_x_max
                            
                            # 等待一小段時間，讓角色移動後再檢測
                            if not self._sleep_with_check(0.2):
                                break
                            
                            # 重新檢測，排除當前錯誤的血條位置
                            character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
                            if character_pos:
                                new_x, _ = character_pos
                                if abs(new_x - current_x) > 10:  # 如果重新檢測到明顯不同的位置（至少10像素差異）
                                    self.logger.info(f"重新檢測到新的血條位置: x={new_x:.0f} (原位置: {current_x:.0f})")
                                    current_x = new_x
                                    last_character_x = current_x
                                else:
                                    # 重新檢測到的位置和之前太接近，可能是同一個錯誤的血條
                                    self.logger.warning(f"重新檢測到的血條位置 ({new_x:.0f}) 與原位置 ({current_x:.0f}) 太接近，可能仍是錯誤的血條")
                                    # 清除位置記錄，下次檢測時會選擇最左邊的血條
                                    self.detection_manager.last_character_x = None
                                    self.detection_manager.last_hp_bar_info = None
                            else:
                                # 如果重新檢測失敗，清除位置記錄，下次檢測時會選擇最左邊的血條
                                self.logger.warning("重新檢測未找到血條，清除位置記錄")
                                self.detection_manager.last_character_x = None
                                self.detection_manager.last_hp_bar_info = None
                            continue  # 重新開始循環
                    
                    # 原有的移動方向驗證邏輯
                    if current_key:
                        # 計算血條應該移動的方向
                        if current_key == 'right':
                            # 向右移動時，血條X應該增加（向目標靠近）
                            expected_direction = 1  # 應該增加
                            if current_x < 10 and position_change < position_change_threshold:
                                # 特殊情況：血條在 x<10 且位置幾乎不變，可能是錯誤的血條
                                stuck_count += 1
                            elif position_change < position_change_threshold:
                                # 位置幾乎沒有變化，可能是角色還沒開始移動，暫時不計入卡住
                                # 只有在連續多次都沒有變化時才視為卡住
                                if stuck_count > 0:
                                    stuck_count += 1
                                # 否則保持 stuck_count 不變，給角色一些時間開始移動
                            elif current_x <= last_character_x:
                                # 血條沒有向右移動（甚至向左移動），可能是錯誤的血條
                                stuck_count += 1
                            else:
                                stuck_count = 0  # 血條正確移動，重置計數
                        elif current_key == 'left':
                            # 向左移動時，血條X應該減少（向目標靠近）
                            expected_direction = -1  # 應該減少
                            if position_change < position_change_threshold:
                                # 位置幾乎沒有變化，可能是角色還沒開始移動，暫時不計入卡住
                                # 只有在連續多次都沒有變化時才視為卡住
                                if stuck_count > 0:
                                    stuck_count += 1
                                # 否則保持 stuck_count 不變，給角色一些時間開始移動
                            elif current_x >= last_character_x:
                                # 血條沒有向左移動（甚至向右移動），可能是錯誤的血條
                                stuck_count += 1
                            else:
                                stuck_count = 0  # 血條正確移動，重置計數
                        else:
                            stuck_count = 0
                    
                    # 如果連續多次檢測到血條沒有向目標方向移動，重新檢測
                    if stuck_count >= 2:
                        self.logger.warning(f"檢測到血條在移動時沒有向目標方向靠近（當前X: {current_x:.0f}, 上次X: {last_character_x:.0f}, 移動方向: {current_key}），可能不是自己的血條，清除位置記錄並重新檢測")
                        # 清除當前檢測到的血條信息，強制重新檢測
                        self.detection_manager.last_character_x = None
                        self.detection_manager.last_hp_bar_info = None
                        
                        # 排除當前檢測到的血條位置（±30像素範圍），強制選擇其他血條
                        exclude_current_x_min = current_x - 30
                        exclude_current_x_max = current_x + 30
                        
                        # 合併原有的排除範圍和當前血條位置的排除範圍
                        if exclude_x_range is not None:
                            exclude_x_min = min(exclude_x_range[0], exclude_current_x_min)
                            exclude_x_max = max(exclude_x_range[1], exclude_current_x_max)
                        else:
                            exclude_x_min = exclude_current_x_min
                            exclude_x_max = exclude_current_x_max
                        
                        # 等待一小段時間，讓角色移動後再檢測
                        if not self._sleep_with_check(0.2):
                            break
                        
                        # 重新檢測，排除當前錯誤的血條位置
                        character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
                        if character_pos:
                            new_x, _ = character_pos
                            if abs(new_x - current_x) > 10:  # 如果重新檢測到明顯不同的位置（至少10像素差異）
                                self.logger.info(f"重新檢測到新的血條位置: x={new_x:.0f} (原位置: {current_x:.0f})")
                                current_x = new_x
                                stuck_count = 0
                                last_character_x = current_x
                            else:
                                # 重新檢測到的位置和之前太接近，可能是同一個錯誤的血條
                                self.logger.warning(f"重新檢測到的血條位置 ({new_x:.0f}) 與原位置 ({current_x:.0f}) 太接近，可能仍是錯誤的血條")
                                # 清除位置記錄，下次檢測時會選擇最左邊的血條
                                self.detection_manager.last_character_x = None
                                self.detection_manager.last_hp_bar_info = None
                                stuck_count = 0
                        else:
                            # 如果重新檢測失敗，清除位置記錄，下次檢測時會選擇最左邊的血條
                            self.logger.warning("重新檢測未找到血條，清除位置記錄")
                            self.detection_manager.last_character_x = None
                            self.detection_manager.last_hp_bar_info = None
                            stuck_count = 0
                else:
                    stuck_count = 0  # 第一次檢測或沒有移動，重置計數
                
                last_character_x = current_x
                distance = calculate_distance_to_target(current_x, target_x)
                
                # 如果已經到達目標位置
                if is_position_reached(current_x, target_x, tolerance):
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    pyautogui.keyUp('left')
                    pyautogui.keyUp('right')
                    self.logger.info(f"已到達目標位置 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                    return True
                
                # 判斷移動方向
                direction = determine_movement_direction(current_x, target_x)
                if direction == 'right':
                    if current_key != 'right':
                        if current_key:
                            press_key_up(current_key)
                        press_key_down('right')
                        current_key = 'right'
                        self.logger.debug(f"向右移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                elif direction == 'left':
                    if current_key != 'left':
                        if current_key:
                            press_key_up(current_key)
                        press_key_down('left')
                        current_key = 'left'
                        self.logger.debug(f"向左移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                else:
                    if current_key:
                        press_key_up(current_key)
                        current_key = None
                
                # 提高判斷頻率，使用更短的間隔（0.1秒）避免移動過頭
                if not self._sleep_with_check(0.1):
                    break
            
            # 確保所有按鍵都已釋放
            if current_key:
                pyautogui.keyUp(current_key)
            pyautogui.keyUp('left')
            pyautogui.keyUp('right')
            
            return False
            
        except Exception as e:
            self.logger.error(f"移動到目標位置失敗: {str(e)}")
            try:
                if current_key:
                    pyautogui.keyUp(current_key)
                pyautogui.keyUp('left')
                pyautogui.keyUp('right')
            except:
                pass
            return False
    
    def exit_free_market_with_position_check(self, target_x: float) -> bool:
        """離開自由市場（新邏輯：按上鍵一次，檢查血條位置變化）
        
        Args:
            target_x: 離開目標位置
            
        Returns:
            True 如果成功離開，False 如果失敗
        """
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            self.logger.info("準備離開自由市場（新邏輯：按上鍵一次並檢查位置變化）")
            
            # 計算排除的X範圍（離開位置 ±50像素）
            exclude_tolerance = 50
            exclude_x_min, exclude_x_max = calculate_exclude_range(target_x, exclude_tolerance)
            
            # 移動到目標位置
            self.logger.info(f"移動到目標位置 X={target_x} 以離開自由市場")
            if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True, exclude_x_range=(exclude_x_min, exclude_x_max)):
                # 移動失敗可能是因為檢測不到血條（角色離開隊伍或檢測錯誤）
                # 這是正常終止條件，不是錯誤
                self.logger.info("移動到目標位置失敗：未檢測到血條，可能是角色離開隊伍（正常終止）")
                self.is_running = False
                return False
            
            # 等待一小段時間
            if not self._sleep_with_check(self.exit_wait):
                return False
            
            # 記錄按上鍵前的位置
            before_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
            if before_pos is None:
                # 檢測不到血條可能是角色離開隊伍或檢測錯誤，這是正常終止條件
                self.logger.info("無法檢測到血條位置，可能是角色離開隊伍（正常終止）")
                self.is_running = False
                return False
            
            before_x, _ = before_pos
            self.logger.info(f"按上鍵前血條位置: x={before_x:.0f}")
            
            # 按上鍵一次
            self.logger.info("按上鍵離開自由市場（第一次）")
            press_key_down('up')
            if not self._sleep_with_check(self.exit_key_duration):
                press_key_up('up')
                return False
            press_key_up('up')
            
            # 等待0.5秒後檢查血條位置是否有變化
            if not self._sleep_with_check(0.5):
                return False
            
            # 檢查血條位置是否變化
            after_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
            if after_pos is None:
                # 檢測不到血條，可能已離開自由市場
                self.logger.info("檢測不到血條，可能已成功離開自由市場")
                # 再次確認是否在自由市場內
                still_in_fm = self.detection_manager.check_free_market_entered()
                if not still_in_fm:
                    self.logger.info("確認已成功離開自由市場")
                    return True
                else:
                    self.logger.warning("檢測不到血條但仍在自由市場，可能是血條檢測問題")
                    return False
            
            after_x, _ = after_pos
            position_change = abs(after_x - before_x)
            position_tolerance = 5  # 位置變化容差（像素）
            
            self.logger.info(f"按上鍵後血條位置: x={after_x:.0f}，位置變化: {position_change:.0f}px")
            
            # 如果位置沒有變化（仍在原地）
            if position_change <= position_tolerance:
                self.logger.warning(f"血條位置沒有變化（仍在 x={after_x:.0f}），可能原因：1.向上鍵沒有執行完成 2.血條並非玩家位置")
                
                # 判斷原因1：再次執行一次向上鍵
                self.logger.info("判斷原因1：再次執行一次向上鍵")
                press_key_down('up')
                if not self._sleep_with_check(self.exit_key_duration):
                    press_key_up('up')
                    return False
                press_key_up('up')
                
                # 再次等待0.5秒後檢查
                if not self._sleep_with_check(0.5):
                    return False
                
                # 再次檢查血條位置
                after_pos2 = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
                if after_pos2 is None:
                    # 檢測不到血條，可能已離開
                    still_in_fm = self.detection_manager.check_free_market_entered()
                    if not still_in_fm:
                        self.logger.info("再次按上鍵後確認已成功離開自由市場（原因1解決）")
                        return True
                    else:
                        self.logger.warning("檢測不到血條但仍在自由市場")
                        # 繼續判斷原因2
                else:
                    after_x2, _ = after_pos2
                    position_change2 = abs(after_x2 - before_x)
                    self.logger.info(f"再次按上鍵後血條位置: x={after_x2:.0f}，位置變化: {position_change2:.0f}px")
                    
                    if position_change2 > position_tolerance:
                        # 位置有變化，可能已離開或正在離開
                        still_in_fm = self.detection_manager.check_free_market_entered()
                        if not still_in_fm:
                            self.logger.info("再次按上鍵後確認已成功離開自由市場（原因1解決）")
                            return True
                        else:
                            self.logger.warning("位置有變化但仍在自由市場，繼續判斷原因2")
                    else:
                        # 位置仍然沒有變化，判斷為原因2
                        self.logger.warning("再次按上鍵後位置仍然沒有變化，判斷為原因2：血條並非玩家位置")
                
                # 判斷原因2：血條並非玩家位置，尋找下一個目標血條位置
                self.logger.warning("判斷原因2：血條並非玩家位置，尋找下一個目標血條位置")
                
                # 排除當前血條位置（±30像素範圍）
                exclude_current_x_min = after_x - 30
                exclude_current_x_max = after_x + 30
                
                # 合併原有的排除範圍和當前血條位置的排除範圍
                combined_exclude_min = min(exclude_x_min, exclude_current_x_min)
                combined_exclude_max = max(exclude_x_max, exclude_current_x_max)
                
                # 清除位置記錄，強制重新檢測
                self.detection_manager.last_character_x = None
                self.detection_manager.last_hp_bar_info = None
                
                # 等待一小段時間後重新檢測
                if not self._sleep_with_check(0.2):
                    return False
                
                # 尋找下一個目標血條位置（排除當前位置）
                next_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(combined_exclude_min, combined_exclude_max))
                
                if next_pos is None:
                    # 沒有下一個目標血條位置，終止執行流程
                    self.logger.error("無法離開自由市場：沒有找到下一個目標血條位置")
                    self.is_running = False
                    # 通知GUI顯示錯誤訊息
                    if hasattr(self, 'on_hp_bar_detection_failed'):
                        self.on_hp_bar_detection_failed()
                    return False
                else:
                    # 找到下一個血條位置，更新位置記錄
                    next_x, _ = next_pos
                    self.logger.info(f"找到下一個目標血條位置: x={next_x:.0f}，更新位置記錄")
                    # 位置記錄已在 detect_hp_bar_position 中更新
                    
                    # 檢查新血條位置是否在離開位置附近
                    position_tolerance = 30  # 位置容差（像素）
                    distance_to_target = abs(next_x - target_x)
                    
                    if distance_to_target > position_tolerance:
                        # 新血條位置不在離開位置，需要先移動到新血條位置，再移動回離開位置
                        self.logger.info(f"新血條位置 (x={next_x:.0f}) 不在離開位置 (x={target_x:.0f})，距離: {distance_to_target:.0f}px")
                        self.logger.info("先移動到新血條位置，再移動回離開位置")
                        
                        # 移動到新血條位置
                        if not self.move_to_target_position(next_x, check_hp_bar_on_fail=True):
                            self.logger.warning(f"移動到新血條位置 (x={next_x:.0f}) 失敗")
                            return False
                        
                        # 等待一小段時間
                        if not self._sleep_with_check(0.2):
                            return False
                        
                        # 移動回離開位置
                        self.logger.info(f"移動回離開位置 (x={target_x:.0f})")
                        if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True, exclude_x_range=(exclude_x_min, exclude_x_max)):
                            self.logger.warning(f"移動回離開位置 (x={target_x:.0f}) 失敗")
                            return False
                        
                        # 等待一小段時間
                        if not self._sleep_with_check(self.exit_wait):
                            return False
                    else:
                        # 新血條位置在離開位置附近，不需要移動
                        self.logger.info(f"新血條位置 (x={next_x:.0f}) 在離開位置附近 (x={target_x:.0f})，距離: {distance_to_target:.0f}px，不需要移動")
                    
                    # 再次按上鍵嘗試離開
                    self.logger.info("在找到新血條位置後，再次按上鍵嘗試離開")
                    press_key_down('up')
                    if not self._sleep_with_check(self.exit_key_duration):
                        press_key_up('up')
                        return False
                    press_key_up('up')
                    
                    # 等待後檢查
                    if not self._sleep_with_check(0.5):
                        return False
                    
                    # 檢查是否已離開
                    still_in_fm = self.detection_manager.check_free_market_entered()
                    if not still_in_fm:
                        self.logger.info("找到新血條位置後成功離開自由市場")
                        return True
                    else:
                        self.logger.error("找到新血條位置後仍然無法離開自由市場")
                        return False
            else:
                # 位置有變化，檢查是否已離開自由市場
                still_in_fm = self.detection_manager.check_free_market_entered()
                if not still_in_fm:
                    self.logger.info("按上鍵後位置有變化且已成功離開自由市場")
                    return True
                else:
                    self.logger.warning("按上鍵後位置有變化但仍在自由市場，可能需要等待動畫完成")
                    # 等待離開動畫完成
                    if not self._sleep_with_check(self.exit_animation_wait):
                        return False
                    
                    # 再次檢查
                    still_in_fm = self.detection_manager.check_free_market_entered()
                    if not still_in_fm:
                        self.logger.info("等待動畫完成後確認已成功離開自由市場")
                        return True
                    else:
                        self.logger.warning("等待動畫完成後仍在自由市場")
                        return False
            
        except Exception as e:
            self.logger.error(f"離開自由市場失敗: {str(e)}")
            return False
    
    def exit_free_market(self, skip_check=False) -> bool:
        """離開自由市場（移動到定點後按上鍵）
        
        Args:
            skip_check: 如果為 True，跳過離開驗證（用於確認視窗場景）
        """
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            self.logger.info("準備離開自由市場（移動到定點後按上鍵）")
            
            # 使用配置的目標位置（使用配置的容差）
            target_x = self.exit_target_x
            
            # 計算排除的X範圍（離開位置 ±50像素），在第一次移動時就將離開位置附近的血條優先級設為最低
            exclude_tolerance = 50  # 排除範圍容差（像素）
            exclude_x_min, exclude_x_max = calculate_exclude_range(target_x, exclude_tolerance)
            
            # 移動到目標位置（離開自由市場時，檢測不到血條要終止）
            # 在移動時就將離開位置附近的血條優先級設為最低，避免誤判其他人的血條
            self.logger.info(f"移動到目標位置 X={target_x} 以離開自由市場（離開位置附近的血條優先級設為最低）")
            if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True, exclude_x_range=(exclude_x_min, exclude_x_max)):
                self.logger.warning("移動到目標位置失敗")
                return False
            
            # 等待一小段時間（使用配置的等待時間）
            if not self._sleep_with_check(self.exit_wait):
                return False
            
            # 按上鍵離開自由市場（點擊兩次，使用配置的按鍵持續時間）
            self.logger.info("按上鍵離開自由市場（第一次）")
            pyautogui.keyDown('up')
            if not self._sleep_with_check(self.exit_key_duration):
                pyautogui.keyUp('up')
                return False
            pyautogui.keyUp('up')

            self.logger.info("按上鍵離開自由市場（第二次）")
            pyautogui.keyDown('up')
            if not self._sleep_with_check(self.exit_key_duration):
                pyautogui.keyUp('up')
                return False
            pyautogui.keyUp('up')
            
            # 等待離開動畫完成（使用配置的動畫等待時間）
            if not self._sleep_with_check(self.exit_animation_wait):
                return False
            
            # 如果 skip_check 為 True，跳過離開驗證（用於確認視窗場景）
            if skip_check:
                self.logger.info("已執行離開自由市場操作（跳過驗證）")
                return True
            
            # 檢查是否已離開自由市場
            still_in_fm = self.detection_manager.check_free_market_entered()
            if not still_in_fm:
                self.logger.info("已成功離開自由市場")
                return True
            else:
                self.logger.warning("按上鍵後仍在自由市場，可能是檢測到其他角色的血條，清除位置記錄並重試")
                # 清除位置記錄，讓下次檢測可以選擇其他血條（可能是自己的血條）
                self.detection_manager.last_character_x = None
                self.detection_manager.last_hp_bar_info = None
                
                # 等待一小段時間後重新檢測
                if not self._sleep_with_check(0.5):
                    return False
                
                # 重新檢測是否已離開自由市場
                still_in_fm = self.detection_manager.check_free_market_entered()
                if not still_in_fm:
                    self.logger.info("重新檢測後確認已成功離開自由市場")
                    return True
                else:
                    # 重新檢測後仍在自由市場，代表有其他人站在離開位置上
                    # 排除離開位置附近的X範圍，重新檢測並選擇其他血條
                    self.logger.warning("重新檢測後仍在自由市場，可能有其他人站在離開位置上，排除離開位置附近的X範圍並重新檢測")
                    
                    # 計算排除的X範圍（離開位置 ±50像素）
                    exclude_tolerance = 50  # 排除範圍容差（像素）
                    exclude_x_min = target_x - exclude_tolerance
                    exclude_x_max = target_x + exclude_tolerance
                    
                    # 清除位置記錄
                    self.detection_manager.last_character_x = None
                    self.detection_manager.last_hp_bar_info = None
                    
                    # 等待一小段時間後，使用排除範圍重新檢測
                    if not self._sleep_with_check(0.5):
                        return False
                    
                    # 使用排除範圍重新檢測血條位置
                    character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=(exclude_x_min, exclude_x_max))
                    if character_pos is None:
                        # 排除離開位置後未檢測到血條，視為已離開自由市場
                        self.logger.info("排除離開位置後未檢測到血條，視為已成功離開自由市場")
                        return True
                    else:
                        # 仍然檢測到血條，但已經排除了離開位置，可能是自己的血條在其他位置
                        new_x, _ = character_pos
                        self.logger.info(f"排除離開位置後檢測到新血條位置: x={new_x:.0f}，移動到離開位置 ({target_x:.0f}) 並重新嘗試離開自由市場")
                        
                        # 移動到離開位置（不是移動到新血條位置，而是移動到離開位置）
                        if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True):
                            self.logger.warning(f"移動到離開位置 ({target_x:.0f}) 失敗")
                            return False
                        
                        # 等待一小段時間
                        if not self._sleep_with_check(self.exit_wait):
                            return False
                        
                        # 再次按上鍵離開自由市場（點擊兩次）
                        self.logger.info("在離開位置按上鍵離開自由市場（第一次）")
                        pyautogui.keyDown('up')
                        if not self._sleep_with_check(self.exit_key_duration):
                            pyautogui.keyUp('up')
                            return False
                        pyautogui.keyUp('up')
                        
                        if not self._sleep_with_check(self.exit_wait):
                            return False
                        
                        self.logger.info("在離開位置按上鍵離開自由市場（第二次）")
                        pyautogui.keyDown('up')
                        if not self._sleep_with_check(self.exit_key_duration):
                            pyautogui.keyUp('up')
                            return False
                        pyautogui.keyUp('up')
                        
                        # 等待離開動畫完成
                        if not self._sleep_with_check(self.exit_animation_wait):
                            return False
                        
                        # 再次檢查是否已離開自由市場
                        still_in_fm = self.detection_manager.check_free_market_entered()
                        if not still_in_fm:
                            self.logger.info("在離開位置按上鍵後成功離開自由市場")
                            return True
                        else:
                            self.logger.warning("在離開位置按上鍵後仍在自由市場，可能移動位置不正確")
                            return False
            
        except Exception as e:
            self.logger.error(f"離開自由市場失敗: {str(e)}")
            return False
    
    def enter_free_market(self, max_retries: int = 3, check_time: float = 3.0) -> bool:
        """進入自由市場，點擊一次按鈕後檢測結果，如果失敗則重試（最多3次）
        
        Args:
            max_retries: 最大重試次數（預設3次）
            check_time: 檢查時間（保留用於向後兼容，但不再使用）
        
        Returns:
            True 如果成功進入，False 如果失敗
        """
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            # 點擊一次按鈕
            click_result = self.click_free_market_button()
            
            # 結果1：檢測到血條（成功進入自由市場）
            if click_result == 'success':
                self.logger.info("成功進入自由市場")
                self.last_entered_free_market = True
                return True
            
            # 結果2：檢測到確認視窗（角色已在自由市場）
            elif click_result == 'dialog':
                self.logger.warning("檢測到確認視窗，代表角色已在自由市場內")
                # 關閉確認視窗
                if self.handle_dialog_window(max_retries=3):
                    self.logger.info("已關閉確認視窗")
                    # 設置標記，表示角色已在自由市場內，下一輪應該執行離開自由市場
                    self.last_entered_free_market = True
                    return True  # 返回 True 表示已在自由市場內
                else:
                    self.logger.error("關閉確認視窗失敗")
                    return False
            
            # 結果3：未檢測到血條也沒檢測到確認視窗（沒有成功進入）
            elif click_result == 'failed':
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.warning(f"未成功進入自由市場，{self.enter_retry_wait}秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(self.enter_retry_wait):
                        return False
                else:
                    # 3次沒有成功進入自由，中斷流程
                    self.logger.error(f"進入自由市場失敗，已重試 {max_retries} 次，中斷流程")
                    self.is_running = False
                    # 通知GUI顯示錯誤訊息
                    if hasattr(self, 'on_enter_free_market_failed'):
                        self.on_enter_free_market_failed()
                    return False
            else:
                # 未知結果
                self.logger.error(f"點擊自由市場按鈕返回未知結果: {click_result}")
                retry_count += 1
                if retry_count < max_retries:
                    if not self._sleep_with_check(self.enter_retry_wait):
                        return False
                else:
                    self.logger.error(f"進入自由市場失敗，已重試 {max_retries} 次，中斷流程")
                    self.is_running = False
                    return False
        
        return False
    
    def get_skill_interval(self, base_interval: float) -> float:
        """獲取技能執行間隔（基礎間隔 ±配置的隨機範圍）"""
        return calculate_skill_interval(base_interval, self.skill_interval_random_range)
    
    def execute_anti_detection_movement(self, direction: str, move_time: float, 
                                        num_moves: int = None) -> None:
        """執行防偵測移動（使用配置的移動次數範圍）"""
        if num_moves is None:
            num_moves = generate_random_move_count(self.anti_detect_min_moves, self.anti_detect_max_moves)
        
        if num_moves == 0:
            return
        
        # 始終使用指定的方向，不交替
        move_key = get_move_key_for_direction(direction)
        
        self.logger.info(f"防偵測移動：執行 {num_moves} 次，方向：{direction}")
        
        for i in range(num_moves):
            if not self.is_running:
                break
                
            self.logger.info(f"執行防偵測移動 ({i+1}/{num_moves})：長押方向鍵{move_key} {move_time}秒")
            pyautogui.keyDown(move_key)
            if not self._sleep_with_check(move_time):
                pyautogui.keyUp(move_key)
                break
            pyautogui.keyUp(move_key)
            self.logger.info(f"防偵測移動完成，已釋放方向鍵{move_key}")
            
            if i < num_moves - 1:
                if not self._sleep_with_check(self.anti_detect_interval):
                    break
    
    def handle_dialog_window(self, max_retries: int = 3) -> bool:
        """處理提示視窗：檢測並點擊關閉按鈕，重複直到沒有提示視窗
        
        返回 True 如果成功處理（沒有提示視窗或已關閉），False 如果處理失敗
        """
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            # 檢測是否有提示視窗
            if not self.detection_manager.detect_dialog_window():
                # 沒有提示視窗，處理成功
                if retry_count > 0:
                    self.logger.info("提示視窗已關閉")
                return True
            
            # 檢測到提示視窗，點擊關閉按鈕
            self.logger.info(f"檢測到提示視窗，點擊關閉按鈕 (嘗試 {retry_count + 1}/{max_retries})")
            
            if not self.window_manager.is_valid():
                return False
            
            if not self.window_manager.bring_to_front():
                return False
            
            # 等待一小段時間確保視窗已顯示
            if not self._sleep_with_check(0.3):
                return False
            
            # 獲取視窗位置
            rect = self.window_manager.get_window_rect()
            if not rect:
                return False
            
            window_x, window_y, _, _ = rect
            
            # 計算絕對座標
            absolute_x, absolute_y = calculate_dialog_button_absolute_position(
                window_x, window_y, self.dialog_close_button_x, self.dialog_close_button_y
            )
            
            # 點擊關閉按鈕
            try:
                pyautogui.click(absolute_x, absolute_y)
                self.logger.info(f"已點擊關閉按鈕 ({self.dialog_close_button_x}, {self.dialog_close_button_y})")
            except Exception as e:
                self.logger.error(f"點擊關閉按鈕失敗: {str(e)}")
                return False
            
            # 等待一小段時間讓視窗關閉
            if not self._sleep_with_check(0.5):
                return False
            
            retry_count += 1
        
        # 如果達到最大重試次數，再次檢查是否還有提示視窗
        if self.detection_manager.detect_dialog_window():
            self.logger.warning(f"處理提示視窗失敗，已重試 {max_retries} 次，提示視窗仍然存在")
            return False
        
        return True

