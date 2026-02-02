"""自動化邏輯模組"""
import pyautogui
import time
import random
import logging
from typing import Optional, Callable, Tuple


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
            self.exit_animation_wait = float(automation_config.get("exit_animation_wait", 2.0))
            self.enter_retry_wait = float(automation_config.get("enter_retry_wait", 3.0))
            self.move_tolerance = int(automation_config.get("move_tolerance", 20))
            self.move_max_duration = int(automation_config.get("move_max_duration", 30))
            self.skill_interval_random_range = float(automation_config.get("skill_interval_random_range", 20))
            self.anti_detect_min_moves = int(automation_config.get("anti_detect_min_moves", 0))
            self.anti_detect_max_moves = int(automation_config.get("anti_detect_max_moves", 2))
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
            self.exit_animation_wait = 2.0
            self.enter_retry_wait = 3.0
            self.move_tolerance = 20
            self.move_max_duration = 30
            self.skill_interval_random_range = 20
            self.anti_detect_min_moves = 0
            self.anti_detect_max_moves = 2
            self.anti_detect_interval = 0.1
            self.dialog_close_button_x = 600
            self.dialog_close_button_y = 400
            self.dialog_close_button_x = 600
            self.dialog_close_button_y = 400
        
        # 設定pyautogui安全模式
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
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
            sleep_chunks = max(1, int(sleep_time / 0.1))  # 每0.1秒檢查一次
            chunk_duration = sleep_time / sleep_chunks
            
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
                    remaining = max(0.0, duration - elapsed)
                    self.current_wait_remaining = remaining
        
        if update_countdown:
            self.current_wait_remaining = None  # 等待完成，清除倒數
            self.logger.info("循環等待完成")
        return True
    
    def skip_current_wait(self):
        """跳過當前等待時間"""
        self.skip_wait = True
        self.logger.info("請求跳過當前等待時間")
    
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
            
            # 點擊後等待1秒，讓過場動畫有緩衝時間，確認視窗有時間出現
            self.logger.info("等待1秒讓過場動畫完成")
            if not self._sleep_with_check(1.0):
                return False
            
            # 檢查是否有確認視窗出現（如果出現代表這輪執行失敗）
            detected_dialog = self.detection_manager.detect_dialog_window()
            if detected_dialog:
                self.logger.warning("點擊自由市場按鈕後檢測到確認視窗，代表角色已在自由市場內")
                # 關閉確認視窗
                self.handle_dialog_window(max_retries=3)
                # 設置標記，表示角色已在自由市場內，下一輪應該執行離開自由市場
                self.last_entered_free_market = True
                return False  # 返回 False 表示檢測到確認視窗（已在自由市場內）
            
            return True
        except Exception as e:
            self.logger.error(f"點擊自由市場按鈕失敗: {str(e)}")
            return False
    
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
            
            self.logger.info(f"開始移動到目標位置 X={target_x:.0f} (誤差範圍: ±{tolerance}像素)")
            
            while (time.time() - start_time) < max_duration:
                if not self.is_running:
                    break
                
                # 檢測當前人物位置（提高判斷頻率，使用更短的間隔）
                character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=exclude_x_range)
                
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
                
                # 驗證血條是否正確：當執行角色移動時，正確的血條應該會向目標x靠近而非遠離
                if last_character_x is not None and current_key:
                    # 計算血條應該移動的方向
                    if current_key == 'right':
                        # 向右移動時，血條X應該增加（向目標靠近）
                        expected_direction = 1  # 應該增加
                        if current_x < 10 and abs(current_x - last_character_x) < 2:
                            # 特殊情況：血條在 x<10 且位置不變，可能是錯誤的血條
                            stuck_count += 1
                        elif current_x <= last_character_x:
                            # 血條沒有向右移動（甚至向左移動），可能是錯誤的血條
                            stuck_count += 1
                        else:
                            stuck_count = 0  # 血條正確移動，重置計數
                    elif current_key == 'left':
                        # 向左移動時，血條X應該減少（向目標靠近）
                        expected_direction = -1  # 應該減少
                        if current_x >= last_character_x:
                            # 血條沒有向左移動（甚至向右移動），可能是錯誤的血條
                            stuck_count += 1
                        else:
                            stuck_count = 0  # 血條正確移動，重置計數
                    else:
                        stuck_count = 0
                    
                    # 如果連續多次檢測到血條沒有向目標方向移動，重新檢測
                    if stuck_count >= 2:
                        self.logger.warning(f"檢測到血條在移動時沒有向目標方向靠近（當前X: {current_x:.0f}, 上次X: {last_character_x:.0f}, 移動方向: {current_key}），可能不是自己的血條，重新檢測")
                        # 重新檢測，嘗試找到正確的血條
                        character_pos = self.detection_manager.detect_hp_bar_position(exclude_x_range=exclude_x_range)
                        if character_pos:
                            new_x, _ = character_pos
                            if new_x != current_x:  # 如果重新檢測到不同的位置
                                self.logger.info(f"重新檢測到血條位置: x={new_x:.0f} (原位置: {current_x:.0f})")
                                current_x = new_x
                            stuck_count = 0
                            last_character_x = current_x
                        else:
                            # 如果重新檢測失敗，繼續使用當前位置
                            stuck_count = 0
                else:
                    stuck_count = 0  # 第一次檢測或沒有移動，重置計數
                
                last_character_x = current_x
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
                        self.logger.debug(f"向右移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                elif current_x > target_x:
                    if current_key != 'left':
                        if current_key:
                            pyautogui.keyUp(current_key)
                        pyautogui.keyDown('left')
                        current_key = 'left'
                        self.logger.debug(f"向左移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f})")
                else:
                    if current_key:
                        pyautogui.keyUp(current_key)
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
            
            # 計算排除的X範圍（離開位置 ±50像素），在第一次移動時就將離開位置附近的血條優先級設為最低
            exclude_tolerance = 50  # 排除範圍容差（像素）
            exclude_x_min = target_x - exclude_tolerance
            exclude_x_max = target_x + exclude_tolerance
            
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
            
            # 等待一小段時間後再次按上鍵
            if not self._sleep_with_check(self.exit_wait):
                return False
            
            self.logger.info("按上鍵離開自由市場（第二次）")
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
    
    def enter_free_market(self, max_retries: int = 5, check_time: float = 3.0) -> bool:
        """進入自由市場，如果失敗則重試"""
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            click_result = self.click_free_market_button()
            if not click_result:
                # 如果點擊失敗是因為檢測到確認視窗（已在 click_free_market_button 中設置 last_entered_free_market = True），
                # 立即執行離開自由市場，然後返回 False，讓循環繼續執行技能和進入自由市場的流程
                if self.last_entered_free_market:
                    self.logger.info("檢測到確認視窗，代表角色已在自由市場內，立即執行離開自由市場")
                    # 立即執行離開自由市場
                    if self.exit_free_market():
                        self.logger.info("已成功離開自由市場，將重新執行整輪邏輯（離開 -> 施放技能 -> 進入）")
                        self.last_entered_free_market = False
                        self.just_exited_free_market = True  # 設置標記，表示剛剛離開，需要重新執行整輪
                        return False  # 返回 False，觸發重新執行整輪邏輯
                    else:
                        self.logger.error("離開自由市場失敗")
                        return False
                
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"點擊失敗，{self.enter_retry_wait}秒後重試 ({retry_count}/{max_retries})")
                    if not self._sleep_with_check(self.enter_retry_wait):
                        return False
                continue
            
            # 點擊按鈕後，確認視窗的檢測已經在 click_free_market_button 中完成
            # 如果 click_free_market_button 返回 False，代表檢測到確認視窗，這輪失敗
            # 這裡只需要等待並檢查是否成功進入自由市場
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
            absolute_x = int(window_x + self.dialog_close_button_x)
            absolute_y = int(window_y + self.dialog_close_button_y)
            
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

