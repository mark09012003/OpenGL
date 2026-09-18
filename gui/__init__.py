"""GUI主模組"""
import tkinter as tk
from tkinter import ttk, messagebox
import win32gui
import threading
import time
import logging
import queue
import math
import pyautogui
from datetime import datetime, timedelta

from gui.components import (
    create_window_section, create_skill_section, create_parameter_section,
    create_action_buttons, create_log_section
)
from gui.styles import configure_styles
from gui.layout import LayoutManager
from gui.theme import Theme
from gui.calibration import CalibrationMixin
from gui.window_modes import WindowModesMixin


class MapleStoryAutoPrayerGUI(CalibrationMixin, WindowModesMixin):
    """MapleStory自動化GUI主類"""
    
    def __init__(self, root, config_manager, window_manager, detection_manager, automation_manager, logger):
        self.root = root
        self.config_manager = config_manager
        self.window_manager = window_manager
        self.detection_manager = detection_manager
        self.automation_manager = automation_manager
        self.logger = logger
        self.ui_queue = queue.SimpleQueue()
        self.root.after(50, self._drain_ui_queue)
        
        # 設置視窗
        self.root.title("MapleStory 自動化助手")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = min(1120, max(900, screen_width - 80))
        initial_height = min(900, max(650, screen_height - 80))
        self.root.geometry(f"{initial_width}x{initial_height}")
        self.root.configure(bg=Theme.BACKGROUND_PRIMARY)
        self.root.minsize(900, 650)
        try:
            self.root.attributes('-alpha', 0.97)
        except tk.TclError:
            pass
        
        # 配置樣式
        configure_styles()
        
        # 創建布局管理器
        self.layout_manager = LayoutManager(self.root)
        
        # 控制變數
        self.is_running = False
        self.worker_thread = None
        self.window_map = {}
        self.last_entered_free_market = False
        self.auto_stop_timer = None
        self.start_time = None
        
        # 固定來回移動相關
        self.last_move_direction = None  # 上一次移動方向：'left' 或 'right' 或 None
        self.move_cycle_count = 0  # 移動循環計數器（用於決定是否執行移動）
        
        # 懸浮框相關
        self.overlay_window = None
        self.hp_bar_overlay_window = None
        self.show_overlay = False
        self.overlay_update_job = None
        self.hp_bar_overlay_canvas = None
        self.save_timer = None
        
        # 校準視窗相關
        self.calibration_window = None
        self.calibration_overlay_window = None
        self.calibration_update_thread = None
        self.show_calibration = False
        self.calibration_canvas = None
        self.calibration_dragging = None  # 當前正在拖動的參考線類型：'hp_bar_y', 'exit_target_x', 'fm_button'
        self.calibration_drag_start_pos = None
        self.show_hp_bar_y_line = False  # 是否顯示血條Y軸參考線
        self.show_exit_target_x_line = False  # 是否顯示退出目標X軸參考線
        self.show_fm_button_marker = False  # 是否顯示自由市場按鈕標記
        self.show_fm_button_x_line = False  # 是否顯示自由市場按鈕X軸參考線
        self.show_fm_button_y_line = False  # 是否顯示自由市場按鈕Y軸參考線
        self.show_dialog_close_x_line = False  # 是否顯示提示框關閉按鈕X軸參考線
        self.show_dialog_close_y_line = False  # 是否顯示提示框關閉按鈕Y軸參考線
        self.show_dialog_check_x_line = False  # 是否顯示檢測區域X軸參考線
        self.show_dialog_check_y_line = False  # 是否顯示檢測區域Y軸參考線
        
        # 懸浮視窗狀態
        self.floating_window = None
        self.log_floating_window = None  # Log懸浮視窗
        self.log_floating_text = None  # Log懸浮視窗的文字顯示組件
        self.countdown_label = None
        self.next_cycle_label = None
        self.countdown_update_job = None
        self.is_floating = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_window_x = 0
        self.drag_window_y = 0
        self.is_dragging = False
        
        # 設定pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 建立GUI
        self.create_widgets()
        
        # 載入配置
        self.load_config()
        
        # 綁定所有變數的自動保存
        self.setup_auto_save_bindings()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化時刷新視窗列表
        self.refresh_windows()
    
    def create_widgets(self):
        """建立所有GUI組件 - 使用新的布局系統"""
        # 創建主布局
        self.layout_manager.create_main_layout()
        
        # 獲取面板
        left_panel = self.layout_manager.get_left_panel()
        right_panel = self.layout_manager.get_right_panel()
        bottom_panel = self.layout_manager.get_bottom_panel()
        
        # 創建各個區域
        create_window_section(left_panel, self)
        create_skill_section(left_panel, self)
        create_parameter_section(left_panel, self)
        create_action_buttons(right_panel, self)
        create_log_section(bottom_panel, self)
        
        # 設置日誌處理器
        self.setup_log_handler()
        
    
    def setup_log_handler(self):
        """設定日誌處理器"""
        ui_queue = self.ui_queue
        class TextHandler(logging.Handler):
            def __init__(self, text_widget, log_floating_text=None):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
                self.log_floating_text = log_floating_text
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    # 更新主視窗的日誌
                    self.text_widget.config(state="normal")
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state="disabled")
                    
                    # 更新Log懸浮視窗的日誌（如果存在）
                    if self.log_floating_text:
                        try:
                            self.log_floating_text.config(state="normal")
                            self.log_floating_text.insert(tk.END, msg + '\n')
                            self.log_floating_text.see(tk.END)
                            self.log_floating_text.config(state="disabled")
                            
                            # 限制日誌行數（保留最近500行）
                            lines = int(self.log_floating_text.index('end-1c').split('.')[0])
                            if lines > 500:
                                self.log_floating_text.config(state="normal")
                                self.log_floating_text.delete('1.0', f'{lines-500}.0')
                                self.log_floating_text.config(state="disabled")
                        except Exception:
                            pass  # 忽略更新失敗
                ui_queue.put(append)
        
        text_handler = TextHandler(self.log_text, None)  # 初始時log_floating_text為None
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(text_handler)
        
        # 保存text_handler引用，以便後續更新log_floating_text
        self.text_handler = text_handler

    def _drain_ui_queue(self):
        """Run worker notifications only on Tk's owning thread."""
        try:
            for _ in range(100):
                try:
                    callback = self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    callback()
                except Exception:
                    self.logger.exception("GUI 回呼失敗")
            self.root.after(50, self._drain_ui_queue)
        except tk.TclError:
            pass
    
    def enum_windows_callback(self, hwnd, windows):
        """列舉視窗回調"""
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title:
                windows.append((hwnd, window_title))
        return True
    
    def refresh_windows(self):
        """刷新視窗列表"""
        windows = []
        win32gui.EnumWindows(self.enum_windows_callback, windows)
        
        window_titles = []
        self.window_map = {}
        
        target_prefix = "MapleStory Worlds"
        for hwnd, title in windows:
            if title.startswith(target_prefix):
                window_titles.append(title)
                self.window_map[title] = hwnd
        
        self.window_combo['values'] = window_titles
        
        if window_titles:
            selected_title = window_titles[0]
            self.window_var.set(selected_title)
            self.on_window_selected()
        else:
            self.window_var.set("")
            self.resolution_label.config(text="解析度: 未找到視窗", fg=Theme.STATUS_ERROR)
            self.logger.warning("未找到以 MapleStory Worlds 開頭的視窗")
            messagebox.showwarning("警告", "未找到以 MapleStory Worlds 開頭的視窗")
    
    def on_window_selected(self, event=None):
        """視窗選擇事件"""
        title = self.window_var.get()
        if title and not title.startswith("MapleStory Worlds"):
            messagebox.showerror("錯誤", "只能選擇以 MapleStory Worlds 開頭的視窗")
            return
        self.select_window_by_title(title)
    
    def select_window_by_title(self, title):
        """根據標題選擇視窗"""
        if title in self.window_map:
            hwnd = self.window_map[title]
            self.window_manager.set_window(hwnd)
            rect = self.window_manager.get_window_rect()
            if rect:
                width, height = rect[2], rect[3]
                self.resolution_label.config(text=f"解析度: {width}×{height}", fg=Theme.TEXT_PRIMARY)
                self.logger.info(f"已選擇視窗: {title} ({width}×{height})")
    
    def toggle_custom_skill1(self):
        """切換自訂技能1"""
        if self.custom_skill1_var.get():
            self.custom_skill1_entry.pack(side="left", padx=5)
        else:
            self.custom_skill1_entry.pack_forget()
        self.auto_save_config()
    
    def toggle_custom_skill2(self):
        """切換自訂技能2"""
        if self.custom_skill2_var.get():
            self.custom_skill2_entry.pack(side="left", padx=5)
        else:
            self.custom_skill2_entry.pack_forget()
        self.auto_save_config()
    
    def toggle_auto_stop_entry(self):
        """切換定時停止輸入欄位狀態"""
        if hasattr(self, 'auto_stop_time_entry'):
            if self.auto_stop_enabled_var.get():
                self.auto_stop_time_entry.config(state="normal")
            else:
                self.auto_stop_time_entry.config(state="disabled")
        self.auto_save_config()
    
    def test_free_market(self):
        """測試是否進入自由市場"""
        if not self.window_manager.is_valid():
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        self.logger.info("開始測試自由市場檢測...")
        
        # 隱藏 GUI 視窗，避免遮擋遊戲畫面
        self.root.withdraw()
        try:
            # 等待一小段時間確保視窗已隱藏
            self.root.update()
            time.sleep(0.2)
            
            # 先檢測血條位置（這會更新 last_hp_bar_info 和 all_candidates）
            character_pos = self.detection_manager.detect_hp_bar_position()
            
            # 直接根據檢測結果判斷，避免重複檢測
            entered = (character_pos is not None)
        finally:
            # 恢復顯示 GUI 視窗
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        
        # 獲取血條信息和所有候選
        hp_bar_info = self.detection_manager.last_hp_bar_info
        all_candidates = self.detection_manager.all_candidates
        candidate_hint = "\n\n候選血條左端 X: " + ", ".join(
            str(c["x_start"]) for c in all_candidates
        ) if all_candidates else ""
        # 從檢測管理器讀取配置的閾值
        min_threshold = self.detection_manager.hp_bar_min_width
        max_threshold = self.detection_manager.hp_bar_max_width
        result_text = ""
        
        if entered:
            if hp_bar_info:
                width = hp_bar_info.get('width', 0)
                result_text = f"✓ 檢測到已進入自由市場\n\n血條信息：\n- 連續紅色區間長度: {width}px\n- 血條位置: ({hp_bar_info['x_start']:.0f}, {hp_bar_info['y']:.0f})\n- 人物位置: ({hp_bar_info['character_x']:.0f}, {hp_bar_info['character_y']:.0f})"
            else:
                result_text = "✓ 檢測到已進入自由市場\n\n（未獲取到血條詳細信息）"
            
            # 顯示所有候選（包括不在範圍內的）
            if all_candidates:
                out_of_range = [c for c in all_candidates if c['width'] < min_threshold or c['width'] > max_threshold]
                if out_of_range:
                    result_text += f"\n\n不在範圍內的候選 ({len(out_of_range)} 個，寬度 < {min_threshold}px 或 > {max_threshold}px):"
                    for c in out_of_range:
                        result_text += f"\n- 位置: ({c['x_start']:.0f}, {c['y']:.0f}), 寬度: {c['width']}px"
            
            messagebox.showinfo("測試結果", result_text + candidate_hint)
            self.logger.info(f"測試結果：已進入自由市場，血條寬度: {hp_bar_info['width'] if hp_bar_info else '未知'}px")
        else:
            if hp_bar_info:
                width = hp_bar_info.get('width', 0)
                result_text = f"✗ 未檢測到自由市場\n\n血條信息：\n- 連續紅色區間長度: {width}px\n- 血條位置: ({hp_bar_info['x_start']:.0f}, {hp_bar_info['y']:.0f})\n\n請確認是否已進入自由市場"
            else:
                result_text = "✗ 未檢測到自由市場\n\n（未檢測到血條）\n請確認是否已進入自由市場"
            
            # 顯示所有候選（包括不在範圍內的）
            if all_candidates:
                out_of_range = [c for c in all_candidates if c['width'] < min_threshold or c['width'] > max_threshold]
                if out_of_range:
                    result_text += f"\n\n不在範圍內的候選 ({len(out_of_range)} 個，寬度 < {min_threshold}px 或 > {max_threshold}px):"
                    for c in out_of_range:
                        result_text += f"\n- 位置: ({c['x_start']:.0f}, {c['y']:.0f}), 寬度: {c['width']}px"
            
            if self.detection_manager.tracker.status == "ambiguous":
                result_text += "\n\n多人血條無法自動識別，請將自身血條左端 X 填入主畫面的欄位。"
            messagebox.showinfo("測試結果", result_text + candidate_hint)
            self.logger.info(f"測試結果：未進入自由市場，血條寬度: {hp_bar_info['width'] if hp_bar_info else '未檢測到'}px")
    
    def test_dialog_detection(self):
        """測試提示視窗檢測"""
        if not self.window_manager.is_valid():
            messagebox.showwarning("警告", "請先選擇遊戲視窗")
            return
        
        try:
            # 確保檢測管理器使用最新的配置值
            config = self.config_manager.load()
            detection_config = config.get("detection", {})
            
            # 更新檢測管理器的參數
            self.detection_manager.dialog_check_x = int(detection_config.get("dialog_check_x", 500))
            self.detection_manager.dialog_check_y = int(detection_config.get("dialog_check_y", 300))
            self.detection_manager.dialog_check_width = int(detection_config.get("dialog_check_width", 200))
            self.detection_manager.dialog_check_height = int(detection_config.get("dialog_check_height", 100))
            self.detection_manager.dialog_bg_r = int(detection_config.get("dialog_bg_r", 200))
            self.detection_manager.dialog_bg_g = int(detection_config.get("dialog_bg_g", 200))
            self.detection_manager.dialog_bg_b = int(detection_config.get("dialog_bg_b", 200))
            self.detection_manager.dialog_bg_tolerance = int(detection_config.get("dialog_bg_tolerance", 30))
            
            # 執行檢測
            detected = self.detection_manager.detect_dialog_window()
            
            # 獲取視窗信息
            rect = self.window_manager.get_window_rect()
            if rect:
                window_x, window_y, window_width, window_height = rect
                check_x = self.detection_manager.dialog_check_x
                check_y = self.detection_manager.dialog_check_y
                check_width = self.detection_manager.dialog_check_width
                check_height = self.detection_manager.dialog_check_height
                
                # 構建結果訊息
                if detected:
                    result_text = "✓ 檢測到提示視窗\n\n"
                else:
                    result_text = "✗ 未檢測到提示視窗\n\n"
                
                result_text += f"檢測區域: X={check_x}, Y={check_y}, 寬度={check_width}, 高度={check_height}\n"
                result_text += f"設定顏色: RGB({self.detection_manager.dialog_bg_r}, {self.detection_manager.dialog_bg_g}, {self.detection_manager.dialog_bg_b})\n"
                result_text += f"顏色容差: {self.detection_manager.dialog_bg_tolerance}\n"
                
                # 顯示實際檢測到的RGB值
                if self.detection_manager.last_dialog_rgb:
                    actual_r, actual_g, actual_b = self.detection_manager.last_dialog_rgb
                    result_text += f"\n實際檢測到的RGB: ({actual_r}, {actual_g}, {actual_b})\n"
                    
                    # 計算與設定值的差異
                    diff_r = abs(actual_r - self.detection_manager.dialog_bg_r)
                    diff_g = abs(actual_g - self.detection_manager.dialog_bg_g)
                    diff_b = abs(actual_b - self.detection_manager.dialog_bg_b)
                    result_text += f"與設定值的差異: R差{diff_r}, G差{diff_g}, B差{diff_b}\n"
                    
                    # 顯示匹配比例
                    if self.detection_manager.last_dialog_match_ratio is not None:
                        match_ratio = self.detection_manager.last_dialog_match_ratio
                        result_text += f"匹配比例: {match_ratio:.2%} (需要 ≥50%)\n"
                
                result_text += f"\n視窗大小: {window_width}x{window_height}"
                
                if not detected:
                    result_text += "\n\n提示：\n"
                    result_text += "- 請確認提示視窗是否已顯示\n"
                    result_text += "- 檢查檢測區域是否正確覆蓋提示視窗\n"
                    if self.detection_manager.last_dialog_rgb:
                        result_text += f"- 建議將背景顏色RGB改為: ({actual_r}, {actual_g}, {actual_b})\n"
                    result_text += "- 或嘗試調整顏色容差值（當前容差可能太小）"
            else:
                result_text = "無法獲取視窗信息"
            
            messagebox.showinfo("測試結果", result_text)
            self.logger.info(f"提示視窗檢測測試結果: {'檢測到' if detected else '未檢測到'}")
            
        except Exception as e:
            error_msg = f"測試失敗: {str(e)}"
            messagebox.showerror("錯誤", error_msg)
            self.logger.error(f"測試提示視窗檢測失敗: {str(e)}", exc_info=True)
    
    def start_automation(self):
        """開始自動化"""
        if self.is_running or (self.worker_thread and self.worker_thread.is_alive()):
            return
        if not self.window_manager.is_valid():
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        selected_title = self.window_var.get()
        if not selected_title or not selected_title.startswith("MapleStory Worlds"):
            messagebox.showerror("錯誤", "只能選擇以 MapleStory Worlds 開頭的視窗")
            return

        reference = self.self_bar_x_var.get().strip()
        try:
            seed_x = float(reference) if reference else None
            if seed_x is not None and (not math.isfinite(seed_x) or seed_x < 0):
                raise ValueError("X 必須大於或等於 0")
        except ValueError:
            messagebox.showerror("錯誤", "自身血條 X 請填入非負數，或留空")
            return
        self.detection_manager.reference_x = seed_x
        self.detection_manager.reset_tracking(seed_x)
        try:
            self.runtime_options = {
                "prayer_key": self.prayer_key_var.get(),
                "angel_key": self.angel_blessing_var.get(),
                "skill3_key": self.custom_skill1_key_var.get(),
                "skill4_key": self.custom_skill2_key_var.get(),
                "skill2": self.skill2_enabled_var.get(),
                "skill3": self.custom_skill1_var.get(),
                "skill4": self.custom_skill2_var.get(),
                "interval": max(0.0, float(self.blessing_interval_var.get())),
                "fm_wait": max(1.0, float(self.fm_wait_var.get())),
                "fm_check_time": max(0.0, float(self.fm_check_time_var.get())),
                "enter_fm": self.enter_fm_var.get(),
                "fixed_move": self.fixed_move_var.get(),
                "anti_detect": self.anti_detect_after_fm_var.get(),
                "direction": self.move_direction_var.get(),
                "left_time": max(0.0, float(self.left_move_time_var.get())),
                "right_time": max(0.0, float(self.right_move_time_var.get())),
            }
        except ValueError:
            messagebox.showerror("錯誤", "時間欄位請填入有效數字")
            return
        
        # 調整視窗大小
        try:
            target_width = int(self.target_width_var.get())
            target_height = int(self.target_height_var.get())
            if target_width > 0 and target_height > 0:
                self.window_manager.resize(target_width, target_height)
                self.window_manager.bring_to_front()
                time.sleep(0.3)
        except Exception as e:
            self.logger.error(f"調整視窗大小失敗: {str(e)}")
        
        self.is_running = True
        self.automation_manager.is_running = True
        self.automation_manager.on_hp_bar_detection_failed = self.on_hp_bar_detection_failed
        self.automation_manager.on_enter_free_market_failed = self.on_enter_free_market_failed
        
        # 重置上次進入自由市場的標誌，確保開始時直接施放技能
        self.last_entered_free_market = False
        self.automation_manager.just_exited_free_market = False  # 重置剛剛離開自由市場的標記
        # 重置移動相關狀態
        self.last_move_direction = None
        self.move_cycle_count = 0
        
        # 更新按鈕狀態（如果不在懸浮視窗模式）
        if not self.is_floating:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        
        self.logger.info("開始自動化流程")
        
        # 根據選項決定是否轉換為半透明懸浮視窗
        if hasattr(self, 'use_floating_window_var') and self.use_floating_window_var.get():
            # 使用懸浮視窗：轉換為半透明懸浮視窗，隱藏主視窗
            self.convert_to_floating_window()
        else:
            # 不使用懸浮視窗：保持主視窗顯示，讓用戶可以通過主視窗控制
            # 不隱藏主視窗，確保用戶可以點擊停止按鈕
            self.logger.info("未使用懸浮視窗，保持主視窗顯示")
        
        # 設置定時停止
        self.start_time = time.time()
        self.setup_auto_stop()
        
        self.worker_thread = threading.Thread(target=self.automation_loop, daemon=True)
        self.worker_thread.start()
    
    def stop_automation(self):
        """停止自動化"""
        self.logger.info("收到停止請求，正在終止自動化流程...")
        # 立即設置停止標誌（這是最重要的，必須立即執行）
        self.is_running = False
        self.automation_manager.is_running = False
        self.show_overlay = False
        
        # 取消定時停止
        try:
            self.cancel_auto_stop()
        except:
            pass
        
        # 確保所有按鍵都被釋放（使用 try-except 避免阻塞，在後台線程執行）
        def release_keys():
            try:
                pyautogui.keyUp('left')
                pyautogui.keyUp('right')
                pyautogui.keyUp('up')
                pyautogui.keyUp('down')
            except:
                pass
        
        # 在後台線程中釋放按鍵，避免阻塞
        import threading
        release_thread = threading.Thread(target=release_keys, daemon=True)
        release_thread.start()
        
        self.logger.info("停止標誌已設置，自動化循環將在下次檢查時退出")
        
        # 使用 after() 延遲執行可能阻塞的操作，避免卡死 GUI
        # 使用較短的延遲（10ms），確保操作能盡快執行
        self.root.after(10, self._finish_stop_automation)
    
    def _finish_stop_automation(self):
        """完成停止自動化的後續操作（在 GUI 線程中執行，避免阻塞）"""
        if self.worker_thread and self.worker_thread.is_alive():
            self.root.after(100, self._finish_stop_automation)
            return
        try:
            # 更新按鈕狀態（如果不在懸浮視窗模式）
            if not self.is_floating:
                if hasattr(self, 'stop_btn'):
                    self.stop_btn.config(state="disabled")
                if hasattr(self, 'start_btn'):
                    self.start_btn.config(state="normal")
            
            # 取消保存定時器（如果存在）
            if hasattr(self, 'save_timer') and self.save_timer:
                try:
                    if self.is_floating and hasattr(self, 'floating_window') and self.floating_window:
                        self.floating_window.after_cancel(self.save_timer)
                    else:
                        self.root.after_cancel(self.save_timer)
                except:
                    pass
                self.save_timer = None
            
            # 恢復正常視窗（如果使用了懸浮視窗）- 使用 after 延遲執行，避免阻塞
            if self.is_floating:
                self.root.after(50, self._restore_window_async)
            else:
                # 如果沒有使用懸浮視窗，主視窗應該一直顯示，不需要恢復
                # 但確保主視窗在最前面，方便用戶操作
                try:
                    self.root.lift()
                    self.root.focus_force()
                except:
                    pass
            
            # 最後保存一次配置（使用 after 延遲執行，避免阻塞）
            self.root.after(200, lambda: self._save_config_async())
        except Exception as e:
            self.logger.error(f"完成停止自動化時發生錯誤: {str(e)}")
    
    def _restore_window_async(self):
        """異步恢復正常視窗（避免阻塞）"""
        try:
            # 檢查是否仍在停止狀態，避免重複執行
            if not self.is_running:
                self.restore_normal_window()
        except Exception as e:
            self.logger.error(f"恢復正常視窗失敗: {str(e)}")
    
    def _save_config_async(self):
        """異步保存配置（避免阻塞）"""
        try:
            self.save_config()
        except Exception as e:
            self.logger.error(f"最後保存配置失敗: {str(e)}")
    
    def setup_auto_stop(self):
        """設置定時停止（根據指定時間點）"""
        try:
            # 檢查是否啟用定時停止
            if not (hasattr(self, 'auto_stop_enabled_var') and self.auto_stop_enabled_var.get()):
                return
            
            time_str = self.auto_stop_time_var.get() if hasattr(self, 'auto_stop_time_var') else "23:59"
            
            # 解析時間字串 (時:分)
            try:
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("時間格式錯誤")
            except (ValueError, AttributeError):
                self.logger.error(f"定時停止時間格式錯誤: {time_str}，應為 時:分 (例如 14:30)")
                messagebox.showerror("錯誤", f"定時停止時間格式錯誤: {time_str}\n請使用 時:分 格式 (例如 14:30)")
                return
            
            # 計算目標時間
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 如果目標時間已過，則設為明天
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # 計算等待時間（秒）
            wait_seconds = (target_time - now).total_seconds()
            
            if wait_seconds > 0:
                self.logger.info(f"已設置定時停止：將於 {target_time.strftime('%H:%M')} 自動停止 (還有 {wait_seconds/60:.1f} 分鐘)")
                self.auto_stop_timer = threading.Timer(wait_seconds, self.auto_stop_callback)
                self.auto_stop_timer.daemon = True
                self.auto_stop_timer.start()
            else:
                self.logger.warning("定時停止時間計算錯誤")
        except Exception as e:
            self.logger.error(f"設置定時停止失敗: {str(e)}")
            messagebox.showerror("錯誤", f"設置定時停止失敗: {str(e)}")
    
    def cancel_auto_stop(self):
        """取消定時停止"""
        if self.auto_stop_timer:
            self.auto_stop_timer.cancel()
            self.auto_stop_timer = None
    
    def auto_stop_callback(self):
        """定時停止回調"""
        current_time = datetime.now().strftime('%H:%M')
        self.logger.info(f"定時停止時間到達 ({current_time})，自動停止程式")
        self.ui_queue.put(self.stop_automation)
        self.ui_queue.put(lambda: messagebox.showinfo("定時停止", f"已到達指定時間 ({current_time})，程式已自動停止"))
    
    def on_hp_bar_detection_failed(self):
        """血條檢測失敗回調"""
        if threading.current_thread() is not threading.main_thread():
            self.ui_queue.put(self.on_hp_bar_detection_failed)
            return
        self.logger.error("血條檢測失敗，終止程式")
        
        # 立即設置停止標誌，確保自動化循環能及時退出
        self.is_running = False
        self.automation_manager.is_running = False
        
        # 使用 after() 延遲執行停止操作和消息框，避免阻塞
        # 先停止自動化，再顯示消息框（使用較長的延遲，確保停止操作先完成）
        if self.is_floating and self.floating_window:
            # 先停止自動化
            self.floating_window.after(10, self.stop_automation)
            # 延遲顯示消息框，避免阻塞停止操作
            self.floating_window.after(100, lambda: messagebox.showerror("錯誤", "無法檢測到血條，程式已終止\n請檢查遊戲視窗是否正確顯示"))
        else:
            # 先停止自動化
            self.root.after(10, self.stop_automation)
            # 延遲顯示消息框，避免阻塞停止操作
            self.root.after(100, lambda: messagebox.showerror("錯誤", "無法檢測到血條，程式已終止\n請檢查遊戲視窗是否正確顯示"))
    
    def on_enter_free_market_failed(self):
        """進入自由市場失敗回調"""
        if threading.current_thread() is not threading.main_thread():
            self.ui_queue.put(self.on_enter_free_market_failed)
            return
        self.logger.error("進入自由市場失敗，終止程式")
        
        # 立即設置停止標誌，確保自動化循環能及時退出
        self.is_running = False
        self.automation_manager.is_running = False
        
        # 使用 after() 延遲執行停止操作和消息框，避免阻塞
        if self.is_floating and self.floating_window:
            # 先停止自動化
            self.floating_window.after(10, self.stop_automation)
            # 延遲顯示消息框
            self.floating_window.after(100, lambda: messagebox.showerror("錯誤", "無法進入自由市場，已重試3次仍失敗\n程式已終止"))
        else:
            # 先停止自動化
            self.root.after(10, self.stop_automation)
            # 延遲顯示消息框
            self.root.after(100, lambda: messagebox.showerror("錯誤", "無法進入自由市場，已重試3次仍失敗\n程式已終止"))
    
    def automation_loop(self):
        """Run the cycle from a GUI-thread snapshot; only post UI work to queue."""
        options = self.runtime_options
        manager = self.automation_manager
        try:
            while self.is_running and manager.is_running:
                if self.last_entered_free_market:
                    self.last_entered_free_market = False
                    if not manager.exit_free_market_with_position_check(manager.exit_target_x):
                        self.logger.warning("無法安全確認離開自由市場，停止循環")
                        break
                    if options["anti_detect"]:
                        direction = options["direction"]
                        duration = options["left_time"] if direction == "left" else options["right_time"]
                        manager.execute_anti_detection_movement(direction, duration)
                elif options["enter_fm"]:
                    in_market = self.detection_manager.check_free_market_entered()
                    if in_market:
                        if not manager.exit_free_market_with_position_check(manager.exit_target_x):
                            break
                    elif self.detection_manager.tracker.status in ("ambiguous", "occluded"):
                        self.logger.warning("無法辨識自身血條，請在介面指定自身血條 X")
                        break

                if options["fixed_move"] and not options["enter_fm"]:
                    if self.move_cycle_count % 3 == 0:
                        direction = "left" if self.last_move_direction == "right" else "right"
                        duration = options["left_time"] if direction == "left" else options["right_time"]
                        try:
                            pyautogui.keyDown(direction)
                            if not manager._sleep_with_check(duration):
                                break
                        finally:
                            pyautogui.keyUp(direction)
                        self.last_move_direction = direction
                    self.move_cycle_count += 1

                skills = [(options["prayer_key"], "技能1")]
                if options["skill2"]:
                    skills.append((options["angel_key"], "技能2"))
                if options["skill3"]:
                    skills.append((options["skill3_key"], "技能3"))
                if options["skill4"]:
                    skills.append((options["skill4_key"], "技能4"))
                for index, (key, label) in enumerate(skills):
                    if not self.is_running or not manager.send_key_press(key, label):
                        break
                    if index < len(skills) - 1 and not manager._sleep_with_check(options["interval"]):
                        break
                else:
                    if options["enter_fm"]:
                        if not manager.handle_dialog_window(max_retries=3):
                            self.logger.warning("無法處理提示視窗，停止循環")
                            break
                        if not manager.enter_free_market(max_retries=3, check_time=options["fm_check_time"]):
                            break
                        self.last_entered_free_market = True
                    if not self.is_running:
                        break
                    wait = manager.get_skill_interval(options["fm_wait"])
                    self.logger.info("等待 %.1f 秒後進行下一輪", wait)
                    if not manager._sleep_with_check(wait, update_countdown=True):
                        break
                    continue
                break
        except Exception:
            self.logger.exception("自動化循環錯誤")
        finally:
            self.is_running = False
            manager.is_running = False
            for key in ("left", "right", "up", "down"):
                try:
                    pyautogui.keyUp(key)
                except Exception:
                    pass
            self.ui_queue.put(self._finish_stop_automation)
            self.logger.info("自動化循環已結束")

    def setup_auto_save_bindings(self):
        """為所有變數綁定自動保存"""
        try:
            # 定義需要綁定自動保存的變數列表
            string_vars = [
                'window_var', 'prayer_key_var', 'angel_blessing_var',
                'custom_skill1_key_var', 'custom_skill2_key_var',
                'blessing_interval_var', 'fm_wait_var', 'fm_check_time_var',
                'auto_stop_time_var', 'target_width_var', 'target_height_var',
                'left_move_time_var', 'right_move_time_var', 'move_direction_var',
                'self_bar_x_var'
            ]
            
            boolean_vars = [
                'custom_skill1_var', 'custom_skill2_var', 'skill2_enabled_var',
                'auto_stop_enabled_var', 'enter_fm_var',
                'use_floating_window_var', 'anti_detect_after_fm_var', 'fixed_move_var'
            ]
            
            # 為所有 StringVar 綁定 trace
            for var_name in string_vars:
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    var.trace_add('write', lambda *args, vn=var_name: self.auto_save_config())
            
            # 為所有 BooleanVar 綁定 trace
            for var_name in boolean_vars:
                if hasattr(self, var_name):
                    var = getattr(self, var_name)
                    var.trace_add('write', lambda *args, vn=var_name: self.auto_save_config())
            
            self.logger.info("已為所有變數綁定自動保存")
        except Exception as e:
            self.logger.error(f"綁定自動保存失敗: {str(e)}")
    
    def auto_save_config(self):
        """自動保存配置"""
        # 取消之前的定時器
        if self.save_timer:
            # 根據當前模式選擇正確的視窗來取消定時器
            if self.is_floating and self.floating_window:
                try:
                    self.floating_window.after_cancel(self.save_timer)
                except:
                    pass
            else:
                try:
                    self.root.after_cancel(self.save_timer)
                except:
                    pass
            self.save_timer = None
        
        # 根據當前模式選擇正確的視窗來設置新的定時器
        if self.is_floating and self.floating_window:
            self.save_timer = self.floating_window.after(1000, self.save_config)
        else:
            self.save_timer = self.root.after(1000, self.save_config)
    
    def save_config(self):
        """Save GUI-owned fields without dropping calibration or future keys."""
        try:
            config = self.config_manager.load()
            skills = config.setdefault("skills", {})
            parameters = config.setdefault("parameters", {})
            detection = config.setdefault("detection", {})
            config["window"] = self.window_var.get()
            for key, var in (
                ("prayer_key", self.prayer_key_var),
                ("blessing_interval", self.blessing_interval_var),
                ("angel_blessing", self.angel_blessing_var),
                ("custom_skill1_key", self.custom_skill1_key_var),
                ("custom_skill2_key", self.custom_skill2_key_var),
                ("custom_skill1_enabled", self.custom_skill1_var),
                ("custom_skill2_enabled", self.custom_skill2_var),
                ("skill2_enabled", self.skill2_enabled_var),
            ):
                skills[key] = var.get()
            for key, var in (
                ("fm_wait", self.fm_wait_var),
                ("target_width", self.target_width_var),
                ("target_height", self.target_height_var),
                ("left_move_time", self.left_move_time_var),
                ("right_move_time", self.right_move_time_var),
                ("fm_check_time", self.fm_check_time_var),
                ("auto_stop_enabled", self.auto_stop_enabled_var),
                ("auto_stop_time", self.auto_stop_time_var),
                ("enter_fm", self.enter_fm_var),
                ("use_floating_window", self.use_floating_window_var),
                ("move_direction", self.move_direction_var),
                ("fixed_move", self.fixed_move_var),
                ("anti_detect_after_fm", self.anti_detect_after_fm_var),
            ):
                parameters[key] = var.get()
            reference = self.self_bar_x_var.get().strip()
            try:
                value = float(reference) if reference else None
                if value is not None and (not math.isfinite(value) or value < 0):
                    return
                detection["self_bar_x"] = value
            except ValueError:
                return
            self.config_manager.save(config)
        except Exception:
            self.logger.exception("保存配置失敗")

    def load_config(self):
        """載入配置"""
        config = self.config_manager.load()
        
        if "window" in config and config["window"]:
            if hasattr(self, 'window_var'):
                self.window_var.set(config["window"])
        
        if "skills" in config:
            skills = config["skills"]
            if "skill2_enabled" in skills:
                self.skill2_enabled_var.set(skills["skill2_enabled"])
            if hasattr(self, 'prayer_key_var') and "prayer_key" in skills:
                self.prayer_key_var.set(skills["prayer_key"])
            if hasattr(self, 'blessing_interval_var') and "blessing_interval" in skills:
                self.blessing_interval_var.set(skills["blessing_interval"])
            if hasattr(self, 'custom_skill1_var') and "custom_skill1_enabled" in skills:
                self.custom_skill1_var.set(skills["custom_skill1_enabled"])
                if skills["custom_skill1_enabled"]:
                    self.toggle_custom_skill1()
            if hasattr(self, 'custom_skill1_key_var') and "custom_skill1_key" in skills:
                self.custom_skill1_key_var.set(skills["custom_skill1_key"])
            if hasattr(self, 'angel_blessing_var') and "angel_blessing" in skills:
                self.angel_blessing_var.set(skills["angel_blessing"])
            if hasattr(self, 'custom_skill2_var') and "custom_skill2_enabled" in skills:
                self.custom_skill2_var.set(skills["custom_skill2_enabled"])
                if skills["custom_skill2_enabled"]:
                    self.toggle_custom_skill2()
            if hasattr(self, 'custom_skill2_key_var') and "custom_skill2_key" in skills:
                self.custom_skill2_key_var.set(skills["custom_skill2_key"])
        
        if "detection" in config:
            reference = config["detection"].get("self_bar_x")
            self.self_bar_x_var.set("" if reference is None else str(reference))

        if "parameters" in config:
            params = config["parameters"]
            for key, var_name in [
                ("fm_wait", "fm_wait_var"),
                ("target_width", "target_width_var"),
                ("target_height", "target_height_var"),
                ("left_move_time", "left_move_time_var"),
                ("right_move_time", "right_move_time_var"),
                ("fm_check_time", "fm_check_time_var"),
                ("auto_stop_time", "auto_stop_time_var"),
            ]:
                if key in params and hasattr(self, var_name):
                    getattr(self, var_name).set(params[key])
            
            if "enter_fm" in params and hasattr(self, 'enter_fm_var'):
                self.enter_fm_var.set(params["enter_fm"])
            if "use_floating_window" in params and hasattr(self, 'use_floating_window_var'):
                self.use_floating_window_var.set(params["use_floating_window"])
            if "move_direction" in params and hasattr(self, 'move_direction_var'):
                self.move_direction_var.set(params["move_direction"])
            if "fixed_move" in params and hasattr(self, 'fixed_move_var'):
                self.fixed_move_var.set(params["fixed_move"])
            if "anti_detect_after_fm" in params and hasattr(self, 'anti_detect_after_fm_var'):
                self.anti_detect_after_fm_var.set(params["anti_detect_after_fm"])
            
            # 載入定時停止設定
            if "auto_stop_enabled" in params and hasattr(self, 'auto_stop_enabled_var'):
                self.auto_stop_enabled_var.set(params["auto_stop_enabled"])
                self.toggle_auto_stop_entry()  # 更新輸入欄位狀態
            if "auto_stop_time" in params and hasattr(self, 'auto_stop_time_var'):
                self.auto_stop_time_var.set(params["auto_stop_time"])
    
    def on_closing(self):
        """視窗關閉事件"""
        self.is_running = False
        self.automation_manager.is_running = False
        self.show_overlay = False
        
        # 恢復正常視窗狀態
        self.restore_normal_window()
        
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
        if self.hp_bar_overlay_window:
            try:
                self.hp_bar_overlay_window.destroy()
            except:
                pass
        if self.calibration_window:
            try:
                self.calibration_window.destroy()
            except:
                pass
        if self.calibration_overlay_window:
            try:
                self.calibration_overlay_window.destroy()
            except:
                pass
        self.show_calibration = False
        self.save_config()
        self.root.destroy()
