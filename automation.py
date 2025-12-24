"""自動化邏輯模組"""
import pyautogui
import time
import random
import logging
from typing import Optional, Callable


class AutomationManager:
    """自動化管理器"""
    
    def __init__(self, window_manager, detection_manager, logger=None):
        self.window_manager = window_manager
        self.detection_manager = detection_manager
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.last_entered_free_market = False
        
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
            
            # 使用可中斷的sleep
            if not self._sleep_with_check(0.2):
                return False
            
            if not key:
                return False
            
            # 按壓按鍵0.3秒後放開（可中斷）
            pyautogui.keyDown(key)
            if not self._sleep_with_check(0.3):
                pyautogui.keyUp(key)
                return False
            pyautogui.keyUp(key)
            
            if skill_name:
                self.logger.info(f"已執行{skill_name}")
            
            return True
        except Exception as e:
            self.logger.error(f"發送按鍵失敗: {str(e)}")
            return False
    
    def _sleep_with_check(self, duration: float, check_interval: float = 0.1) -> bool:
        """可中斷的sleep，返回False表示被中斷"""
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
            
            if not self._sleep_with_check(0.2):
                return False
            
            # 獲取視窗位置
            rect = self.window_manager.get_window_rect()
            if not rect:
                return False
            
            window_x, window_y, _, _ = rect
            
            # 自由市場按鈕位置（X和Y軸都固定）
            button_x_offset = 980
            button_y_offset = 720
            button_x = window_x + button_x_offset
            button_y = window_y + button_y_offset
            
            # 點擊按鈕（點擊兩次）
            self.logger.info(f"準備點擊自由市場按鈕 (按鈕位置: {button_x:.0f}, {button_y:.0f})")
            pyautogui.click(button_x, button_y)
            if not self._sleep_with_check(0.1):
                return False
            pyautogui.click(button_x, button_y)
            self.logger.info("已點擊自由市場按鈕（兩次）")
            
            return True
        except Exception as e:
            self.logger.error(f"點擊自由市場按鈕失敗: {str(e)}")
            return False
    
    def move_to_target_position(self, target_x: float, tolerance: int = 20, 
                                max_duration: int = 30) -> bool:
        """使用方向鍵移動角色直到到達目標X位置（容許值：±20px）"""
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
                    self.logger.warning("無法檢測到血條，繼續嘗試...")
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    if not self._sleep_with_check(0.5):
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
                
                if not self._sleep_with_check(0.3):
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
    
    def enter_free_market(self, max_retries: int = 5, check_time: float = 3.0) -> bool:
        """進入自由市場，如果失敗則重試"""
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            if not self.click_free_market_button():
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"點擊失敗，3秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(3.0):
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
                    self.logger.warning(f"未成功進入自由市場，3秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(3.0):
                        return False
                else:
                    self.logger.error(f"進入自由市場失敗，已重試 {max_retries} 次")
                    return False
        
        return False
    
    def get_skill_interval(self, base_interval: float) -> float:
        """獲取技能執行間隔（基礎間隔 ±20秒）"""
        random_offset = random.uniform(-20, 20)
        interval = max(1.0, base_interval + random_offset)
        return interval
    
    def execute_anti_detection_movement(self, direction: str, move_time: float, 
                                        num_moves: int = None) -> None:
        """執行防偵測移動"""
        if num_moves is None:
            num_moves = random.randint(0, 2)
        
        if num_moves == 0:
            return
        
        self.logger.info(f"防偵測移動：執行 {num_moves} 次")
        
        for i in range(num_moves):
            # 如果執行兩次，第二次反轉方向
            current_direction = direction
            if num_moves == 2 and i == 1:
                current_direction = "right" if direction == "left" else "left"
            
            move_key = 'left' if current_direction == "left" else 'right'
            
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
                if not self._sleep_with_check(0.1):
                    break

