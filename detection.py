"""圖像檢測模組"""
import logging
import threading
import numpy as np
from PIL import ImageGrab
from typing import Optional, Tuple
from hp_tracking import PlayerBarTracker, red_intervals
from config import create_default_config


class DetectionManager:
    """圖像檢測管理器"""
    
    def __init__(self, window_manager, config=None, logger=None):
        self.window_manager = window_manager
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()
        self.last_hp_bar_info = None  # 保存最後一次檢測到的血條信息
        self.all_candidates = []  # 保存所有檢測到的候選（包括未達門檻的）
        self.last_dialog_rgb = None  # 保存最後一次檢測到的對話框RGB平均值
        self.last_dialog_match_ratio = None  # 保存最後一次檢測到的匹配比例
        self.last_character_x = None  # 保存上一次檢測到的角色X位置，用於驗證位置變化
        
        settings = create_default_config()["detection"]
        if config:
            settings.update(config.get("detection", {}))
        integer_keys = (
            "hp_bar_y", "hp_bar_min_width", "hp_bar_max_width",
            "color_r_min", "color_r_max", "color_g_max", "color_b_max",
            "pixel_gap_tolerance", "character_y_offset", "character_x_tolerance",
            "dialog_check_x", "dialog_check_y", "dialog_check_width",
            "dialog_check_height", "dialog_bg_r", "dialog_bg_g", "dialog_bg_b",
            "dialog_bg_tolerance",
        )
        for key in integer_keys:
            setattr(self, key, int(settings[key]))
        self.color_r_g_ratio = float(settings["color_r_g_ratio"])
        self.color_r_b_ratio = float(settings["color_r_b_ratio"])
        reference_x = None
        if config:
            reference_x = config.get("detection", {}).get("self_bar_x")
        self.tracker = PlayerBarTracker(
            self.hp_bar_min_width, self.hp_bar_max_width,
            self.character_x_tolerance,
            float(reference_x) if reference_x not in (None, "") else None,
        )
        self.reference_x = self.tracker.seed_x

    def reset_tracking(self, seed_x=None):
        """Start a new scene or explicitly select the player's bar."""
        with self._lock:
            if seed_x is not None:
                self.reference_x = seed_x
            self.tracker.reset(seed_x)
            self.last_character_x = None
            self.last_hp_bar_info = None

    def detection_uncertain(self):
        return self.tracker.status in ("ambiguous", "occluded", "missing")

    def detect_hp_bar_position(self, exclude_x_range: Optional[Tuple[float, float]] = None) -> Optional[Tuple[float, float]]:
        with self._lock:
            return self._detect_hp_bar_position(exclude_x_range)

    def _detect_hp_bar_position(self, exclude_x_range: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
        """Return only a confidently tracked player position, never another bar.

        Capture an 11-pixel strip instead of the whole window. Keeping a track
        across missed frames avoids selecting a different player after overlap
        or clipping at a screen edge.
        """
        if not self.window_manager.get_window_handle():
            return None
        try:
            rect = self.window_manager.get_window_rect()
            if not rect:
                return None
            window_x, window_y, window_width, window_height = rect
            if not 0 <= self.hp_bar_y < window_height:
                self.logger.warning("血條 Y 座標超出視窗範圍")
                return None
            top = max(0, self.hp_bar_y - 5)
            bottom = min(window_height, self.hp_bar_y + 6)
            image = np.asarray(ImageGrab.grab(bbox=(
                int(window_x), int(window_y + top),
                int(window_x + window_width), int(window_y + bottom)
            )).convert("RGB"))
            # Prefer the calibrated row; other rows compensate for a small
            # window offset. Inspect at most eleven narrow rows.
            rows = sorted(range(top, bottom), key=lambda y: abs(y - self.hp_bar_y))
            bars = []
            best_score = (-1, -float("inf"))
            for y in rows:
                row_bars = red_intervals(
                    image[y - top], y, r_min=self.color_r_min,
                    r_max=self.color_r_max, g_max=self.color_g_max,
                    b_max=self.color_b_max, rg_ratio=self.color_r_g_ratio,
                    rb_ratio=self.color_r_b_ratio, gap=self.pixel_gap_tolerance
                )
                complete_count = sum(
                    not bar.clipped and self.hp_bar_min_width <= bar.width <= self.hp_bar_max_width
                    for bar in row_bars
                )
                score = (complete_count, -abs(y - self.hp_bar_y))
                if score > best_score:
                    bars, best_score = row_bars, score
            self.all_candidates = [bar.as_dict() for bar in bars]
            self.tracker.min_width = self.hp_bar_min_width
            self.tracker.max_width = self.hp_bar_max_width
            self.tracker.tolerance = self.character_x_tolerance
            chosen = self.tracker.observe(bars, exclude_x_range)
            if chosen is None:
                self.last_hp_bar_info = None
                self.logger.debug("自身血條位置不確定：%s", self.tracker.status)
                return None
            x = chosen.x_start
            character_y = chosen.y + self.character_y_offset
            self.last_character_x = x
            self.last_hp_bar_info = {
                **chosen.as_dict(), "character_x": x,
                "character_y": character_y,
            }
            return float(x), float(character_y)
        except Exception:
            self.logger.exception("偵測自身血條失敗")
            self.last_hp_bar_info = None
            return None

    def check_free_market_entered(self, exclude_x_range: Optional[Tuple[float, float]] = None) -> bool:
        """A missing or occluded bar is unknown, never proof of another player."""
        return self.detect_hp_bar_position(exclude_x_range) is not None

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
