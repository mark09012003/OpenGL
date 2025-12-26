"""自動化邏輯模組"""
import pyautogui
import time
import random
import logging
from typing import Optional, Callable


class AutomationManager:
    """自動化管理器"""
    
    def __init__(self, window_manager, detection_manager, config=None, logger=None):
        self.window_manager = window_manager
        self.detection_manager = detection_manager
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.last_entered_free_market = False
        
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
            self.exit_animation_wait = float(automation_config.get("exit_animation_wait", 2.0))
            self.enter_retry_wait = float(automation_config.get("enter_retry_wait", 3.0))
            self.move_tolerance = int(automation_config.get("move_tolerance", 20))
            self.move_max_duration = int(automation_config.get("move_max_duration", 30))
            self.skill_interval_random_range = float(automation_config.get("skill_interval_random_range", 20))
            self.anti_detect_min_moves = int(automation_config.get("anti_detect_min_moves", 0))
            self.anti_detect_max_moves = int(automation_config.get("anti_detect_max_moves", 2))
            self.anti_detect_interval = float(automation_config.get("anti_detect_interval", 0.1))
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
            self.move_check_interval = 0.3
            self.exit_wait = 0.5
            self.exit_key_duration = 0.3
            self.exit_animation_wait = 2.0
            self.enter_retry_wait = 3.0
            self.move_tolerance = 20
            self.move_max_duration = 30
            self.skill_interval_random_range = 20
            self.anti_detect_min_moves = 0
            self.anti_detect_max_moves = 2
            self.anti_detect_interval = 0.1
        
        # 設定pyautogui安全模式
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
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
            
            if not key:
                return False
            
            # 按壓按鍵後放開（使用配置的持續時間，可中斷）
            pyautogui.keyDown(key)
            if not self._sleep_with_check(self.key_press_duration):
                pyautogui.keyUp(key)
                return False
            pyautogui.keyUp(key)
            
            if skill_name:
                self.logger.info(f"已執行{skill_name}")
            
            return True
        except Exception as e:
            self.logger.error(f"發送按鍵失敗: {str(e)}")
            return False
    
    def _sleep_with_check(self, duration: float, check_interval: float = None) -> bool:
        """可中斷的sleep，返回False表示被中斷"""
        if check_interval is None:
            check_interval = self.sleep_check_interval
        elapsed = 0.0
        while elapsed < duration:
            if not self.is_running:
                return False
            sleep_time = min(check_interval, duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
        return True
    
    def click_free_market_button(self) -> bool:
        """點擊自由市場按鈕"""
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            if not self._sleep_with_check(self.button_click_wait):
                return False
            
            # 獲取視窗位置
            rect = self.window_manager.get_window_rect()
            if not rect:
                return False
            
            window_x, window_y, _, _ = rect
            
            # 使用配置的自由市場按鈕位置
            button_x = window_x + self.fm_button_x
            button_y = window_y + self.fm_button_y
            
            # 點擊按鈕（點擊兩次，使用配置的延遲）
            self.logger.info(f"準備點擊自由市場按鈕 (按鈕位置: {button_x:.0f}, {button_y:.0f})")
            pyautogui.click(button_x, button_y)
            if not self._sleep_with_check(self.button_click_delay):
                return False
            pyautogui.click(button_x, button_y)
            self.logger.info("已點擊自由市場按鈕（兩次）")
            
            return True
        except Exception as e:
            self.logger.error(f"點擊自由市場按鈕失敗: {str(e)}")
            return False
    
    def move_to_target_position(self, target_x: float, tolerance: int = None, 
                                max_duration: int = None, check_hp_bar_on_fail: bool = False) -> bool:
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
            
            self.logger.info(f"開始移動到目標位置 X={target_x:.0f} (誤差範圍: ±{tolerance}像素)")
            
            while (time.time() - start_time) < max_duration:
                if not self.is_running:
                    break
                
                # 檢測當前人物位置
                character_pos = self.detection_manager.detect_hp_bar_position()
                
                if character_pos is None:
                    # 只有在 check_hp_bar_on_fail=True 時才終止程式（用於離開自由市場時）
                    if check_hp_bar_on_fail:
                        self.logger.error("無法檢測到血條，終止程式")
                        self.is_running = False
                        # 通知GUI顯示錯誤訊息
                        if hasattr(self, 'on_hp_bar_detection_failed'):
                            self.on_hp_bar_detection_failed()
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
                distance = abs(current_x - target_x)
                
                # 如果已經到達目標位置
                if distance <= tolerance:
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    pyautogui.keyUp('left')
                    pyautogui.keyUp('right')
                    self.logger.info(f"已到達目標位置 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                    return True
                
                # 判斷移動方向
                if current_x < target_x:
                    if current_key != 'right':
                        if current_key:
                            pyautogui.keyUp(current_key)
                        pyautogui.keyDown('right')
                        current_key = 'right'
                elif current_x > target_x:
                    if current_key != 'left':
                        if current_key:
                            pyautogui.keyUp(current_key)
                        pyautogui.keyDown('left')
                        current_key = 'left'
                else:
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                
                if not self._sleep_with_check(self.move_check_interval):
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
    
    def exit_free_market(self) -> bool:
        """離開自由市場（移動到定點後按上鍵）"""
        if not self.window_manager.is_valid():
            return False
        
        try:
            if not self.window_manager.bring_to_front():
                return False
            
            self.logger.info("準備離開自由市場（移動到定點後按上鍵）")
            
            # 使用配置的目標位置（使用配置的容差）
            target_x = self.exit_target_x
            
            # 移動到目標位置（離開自由市場時，檢測不到血條要終止）
            self.logger.info(f"移動到目標位置 X={target_x} 以離開自由市場")
            if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True):
                self.logger.warning("移動到目標位置失敗")
                return False
            
            # 等待一小段時間（使用配置的等待時間）
            if not self._sleep_with_check(self.exit_wait):
                return False
            
            # 按上鍵離開自由市場（使用配置的按鍵持續時間）
            self.logger.info("按上鍵離開自由市場")
            pyautogui.keyDown('up')
            if not self._sleep_with_check(self.exit_key_duration):
                pyautogui.keyUp('up')
                return False
            pyautogui.keyUp('up')
            
            # 等待離開動畫完成（使用配置的動畫等待時間）
            if not self._sleep_with_check(self.exit_animation_wait):
                return False
            
            # 檢查是否已離開自由市場
            still_in_fm = self.detection_manager.check_free_market_entered()
            if not still_in_fm:
                self.logger.info("已成功離開自由市場")
                return True
            else:
                self.logger.warning("按上鍵後仍在自由市場，可能移動位置不正確")
                return False
            
        except Exception as e:
            self.logger.error(f"離開自由市場失敗: {str(e)}")
            return False
    
    def enter_free_market(self, max_retries: int = 5, check_time: float = 3.0) -> bool:
        """進入自由市場，如果失敗則重試"""
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            if not self.click_free_market_button():
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"點擊失敗，{self.enter_retry_wait}秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(self.enter_retry_wait):
                        return False
                continue
            
            self.logger.info(f"等待 {check_time} 秒檢查是否進入自由市場")
            if not self._sleep_with_check(check_time):
                return False
            
            # 檢查是否成功進入
            entered = self.detection_manager.check_free_market_entered()
            if entered:
                self.logger.info("成功進入自由市場")
                self.last_entered_free_market = True
                return True
            else:
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.warning(f"未成功進入自由市場，{self.enter_retry_wait}秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(self.enter_retry_wait):
                        return False
                else:
                    self.logger.error(f"進入自由市場失敗，已重試 {max_retries} 次")
                    return False
        
        return False
    
    def get_skill_interval(self, base_interval: float) -> float:
        """獲取技能執行間隔（基礎間隔 ±配置的隨機範圍）"""
        random_offset = random.uniform(-self.skill_interval_random_range, self.skill_interval_random_range)
        interval = max(1.0, base_interval + random_offset)
        return interval
    
    def execute_anti_detection_movement(self, direction: str, move_time: float, 
                                        num_moves: int = None) -> None:
        """執行防偵測移動（使用配置的移動次數範圍）"""
        if num_moves is None:
            num_moves = random.randint(self.anti_detect_min_moves, self.anti_detect_max_moves)
        
        if num_moves == 0:
            return
        
        # 始終使用指定的方向，不交替
        move_key = 'left' if direction == "left" else 'right'
        
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

