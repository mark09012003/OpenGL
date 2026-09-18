"""自動化邏輯模組"""
import pyautogui
import time
import random
import logging
from typing import Optional, Tuple
from config import create_default_config


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
        
        defaults = create_default_config()["automation"]
        settings = defaults.copy()
        if config:
            settings.update(config.get("automation", {}))
        integer_keys = (
            "exit_target_x", "fm_button_x", "fm_button_y", "move_tolerance",
            "anti_detect_min_moves", "anti_detect_max_moves",
            "dialog_close_button_x", "dialog_close_button_y",
        )
        for key in integer_keys:
            setattr(self, key, int(settings[key]))
        for key in defaults:
            if key not in integer_keys:
                setattr(self, key, float(settings[key]))

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
            # 場景切換後位置座標可能重設；重新建立追蹤，且多人時只用使用者指定的座標鎖定。
            self.detection_manager.reset_tracking(self.detection_manager.reference_x)
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
        """Move in short pulses; never keep a direction held without a valid track."""
        tolerance = self.move_tolerance if tolerance is None else tolerance
        max_duration = self.move_max_duration if max_duration is None else max_duration
        if not self.window_manager.is_valid() or not self.window_manager.bring_to_front():
            return False
        deadline = time.monotonic() + max_duration
        missing_since = None
        while self.is_running and time.monotonic() < deadline:
            position = self.detection_manager.detect_hp_bar_position(exclude_x_range)
            if position is None:
                # A merged or clipped bar must stop movement immediately.
                release_all_movement_keys()
                if missing_since is None:
                    missing_since = time.monotonic()
                if time.monotonic() - missing_since >= 2.0:
                    self.logger.warning("自身血條暫時無法辨識，停止移動：%s",
                                        self.detection_manager.tracker.status)
                    return False
                if not self._sleep_with_check(0.15):
                    return False
                continue
            missing_since = None
            x, _ = position
            error = target_x - x
            if abs(error) <= tolerance:
                release_all_movement_keys()
                return True
            direction = "right" if error > 0 else "left"
            try:
                pyautogui.keyDown(direction)
                # Short pulses bound blind travel if the next frame is occluded.
                if not self._sleep_with_check(min(0.12, max(0.04, abs(error) / 500))):
                    return False
            finally:
                pyautogui.keyUp(direction)
            if not self._sleep_with_check(self.move_check_interval):
                return False
        release_all_movement_keys()
        self.logger.warning("移動逾時，未能確認到達目標位置")
        return False

    def _confirm_bar_absent(self, samples=3):
        """Require repeated empty frames, not an ambiguous/merged observation."""
        for _ in range(samples):
            position = self.detection_manager.detect_hp_bar_position()
            if (position is not None or self.detection_manager.all_candidates
                    or self.detection_manager.tracker.status != "missing"):
                return False
            if not self._sleep_with_check(0.2):
                return False
        return True

    def exit_free_market_with_position_check(self, target_x: float) -> bool:
        """Leave the market while preserving the identity of the player's bar."""
        if not self.move_to_target_position(target_x, check_hp_bar_on_fail=True):
            return False
        for attempt in range(2):
            if not self.is_running:
                return False
            try:
                pyautogui.keyDown("up")
                if not self._sleep_with_check(self.exit_key_duration):
                    return False
            finally:
                pyautogui.keyUp("up")
            if not self._sleep_with_check(self.exit_animation_wait):
                return False
            if self._confirm_bar_absent():
                self.detection_manager.reset_tracking()
                self.logger.info("血條連續消失，已離開自由市場")
                return True
            if self.detection_manager.detection_uncertain():
                self.logger.warning("血條被遮擋或與他人重疊，無法確認離開自由市場")
                return False
            self.logger.warning("第 %s 次離開嘗試後仍檢測到自身血條", attempt + 1)
        return False

    def exit_free_market(self, skip_check=False) -> bool:
        """Compatibility entry point for the previous GUI flow."""
        if not self.window_manager.is_valid() or not self.window_manager.bring_to_front():
            return False
        if skip_check:
            try:
                pyautogui.keyDown("up")
                return self._sleep_with_check(self.exit_key_duration)
            finally:
                pyautogui.keyUp("up")
        return self.exit_free_market_with_position_check(self.exit_target_x)

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
