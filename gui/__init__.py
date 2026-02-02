"""GUI主模組"""
import tkinter as tk
from tkinter import ttk, messagebox
import win32gui
import win32con
import threading
import time
import random
import logging
import pyautogui
from datetime import datetime, timedelta

from gui.components import (
    create_window_section, create_skill_section, create_parameter_section,
    create_action_buttons, create_log_section
)
from gui.styles import configure_styles
from gui.layout import LayoutManager
from gui.theme import Theme
from gui.widgets import ThemedLabel, SectionFrame


class MapleStoryAutoPrayerGUI:
    """MapleStory自動化GUI主類"""
    
    def __init__(self, root, config_manager, window_manager, detection_manager, automation_manager, logger):
        self.root = root
        self.config_manager = config_manager
        self.window_manager = window_manager
        self.detection_manager = detection_manager
        self.automation_manager = automation_manager
        self.logger = logger
        
        # 設置視窗
        self.root.title("MapleStory 自動化助手")
        self.root.geometry("1100x900")
        self.root.configure(bg=Theme.BACKGROUND_PRIMARY)
        self.root.minsize(1000, 800)
        
        # 配置樣式
        configure_styles()
        
        # 創建布局管理器
        self.layout_manager = LayoutManager(self.root)
        
        # 控制變數
        self.is_running = False
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
        self.overlay_update_thread = None
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
        
        # 強制刷新所有LabelFrame的背景色
        self.root.after(200, self._refresh_all_frame_bg)
    
    def _refresh_all_frame_bg(self):
        """刷新所有Frame的背景色"""
        def _set_all_bg(widget):
            try:
                if isinstance(widget, ttk.LabelFrame):
                    # ttk.LabelFrame內部有一個Frame，需要直接訪問並設置
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.configure(bg=Theme.BACKGROUND_PRIMARY)
                            # 遞歸設置所有子Frame
                            _set_all_bg(child)
                        else:
                            _set_all_bg(child)
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg=Theme.BACKGROUND_PRIMARY)
                    for child in widget.winfo_children():
                        _set_all_bg(child)
            except Exception:
                pass
        
        # 多次刷新確保所有Frame都被設置
        _set_all_bg(self.root)
        self.root.after(10, lambda: _set_all_bg(self.root))
        self.root.after(50, lambda: _set_all_bg(self.root))
        self.root.after(100, lambda: _set_all_bg(self.root))
    
    def setup_log_handler(self):
        """設定日誌處理器"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state="normal")
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state="disabled")
                self.text_widget.after(0, append)
        
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(text_handler)
    
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
            
            messagebox.showinfo("測試結果", result_text)
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
            
            messagebox.showinfo("測試結果", result_text)
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
    
    def toggle_overlay(self):
        """切換懸浮框顯示"""
        self.show_overlay = not self.show_overlay
        if self.show_overlay:
            self.overlay_btn.config(text="隱藏位置")
            if not self.overlay_update_thread or not self.overlay_update_thread.is_alive():
                self.overlay_update_thread = threading.Thread(target=self.update_overlay_position, daemon=True)
                self.overlay_update_thread.start()
        else:
            self.overlay_btn.config(text="顯示位置")
            if self.overlay_window:
                try:
                    self.overlay_window.withdraw()
                except:
                    pass
            if self.hp_bar_overlay_window:
                try:
                    self.hp_bar_overlay_window.withdraw()
                except:
                    pass
    
    def toggle_calibration(self):
        """切換校準視窗顯示"""
        self.show_calibration = not self.show_calibration
        if self.show_calibration:
            self.calibration_btn.config(text="關閉校準")
            self.create_calibration_window()
            # 立即更新一次 overlay
            self._schedule_calibration_overlay_update()
        else:
            self.calibration_btn.config(text="校準")
            if self.calibration_window:
                try:
                    self.calibration_window.destroy()
                except:
                    pass
                self.calibration_window = None
            if self.calibration_overlay_window:
                try:
                    self.calibration_overlay_window.destroy()
                except:
                    pass
                self.calibration_overlay_window = None
    
    def update_overlay_position(self):
        """更新懸浮框位置，顯示所有檢測到的候選"""
        while self.show_overlay:
            if not self.window_manager.is_valid():
                if self.hp_bar_overlay_window:
                    try:
                        self.hp_bar_overlay_window.withdraw()
                    except:
                        pass
                time.sleep(0.5)
                continue
            
            try:
                rect = self.window_manager.get_window_rect()
                if not rect:
                    time.sleep(0.5)
                    continue
                
                window_x, window_y, window_width, window_height = rect
                
                # 檢測血條位置（這會更新 all_candidates）
                self.detection_manager.detect_hp_bar_position()
                all_candidates = self.detection_manager.all_candidates
                
                # 創建或更新懸浮框
                if not self.hp_bar_overlay_window:
                    self._create_hp_bar_overlay_window()
                
                if self.hp_bar_overlay_window:
                    try:
                        # 更新懸浮框位置和內容
                        self._update_hp_bar_overlay(all_candidates, window_x, window_y)
                        self.hp_bar_overlay_window.deiconify()
                        self.hp_bar_overlay_window.lift()
                    except Exception as e:
                        self.logger.error(f"更新懸浮框失敗: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"更新懸浮框位置失敗: {str(e)}")
            
            time.sleep(0.3)  # 每0.3秒更新一次
    
    def _create_hp_bar_overlay_window(self):
        """創建血條懸浮框視窗"""
        try:
            self.hp_bar_overlay_window = tk.Toplevel(self.root)
            self.hp_bar_overlay_window.overrideredirect(True)  # 移除標題欄
            self.hp_bar_overlay_window.attributes("-topmost", True)  # 置頂
            self.hp_bar_overlay_window.attributes("-transparentcolor", "black")  # 黑色透明
            self.hp_bar_overlay_window.configure(bg="black")
            self.hp_bar_overlay_window.geometry("1x1+0+0")  # 初始大小
        except Exception as e:
            self.logger.error(f"創建懸浮框視窗失敗: {str(e)}")
            self.hp_bar_overlay_window = None
    
    def _update_hp_bar_overlay(self, all_candidates, window_x, window_y):
        """更新血條懸浮框，顯示所有檢測到的候選"""
        if not self.hp_bar_overlay_window:
            return
        
        try:
            rect = self.window_manager.get_window_rect()
            if not rect:
                return
            
            window_x, window_y, window_width, window_height = rect
            
            # 清除舊的內容
            for widget in self.hp_bar_overlay_window.winfo_children():
                widget.destroy()
            
            if not all_candidates:
                self.hp_bar_overlay_window.withdraw()
                return
            
            # 從檢測管理器讀取配置的閾值
            min_threshold = self.detection_manager.hp_bar_min_width
            max_threshold = self.detection_manager.hp_bar_max_width
            
            # 創建Canvas來繪製箭頭
            canvas = tk.Canvas(
                self.hp_bar_overlay_window,
                bg="black",
                highlightthickness=0,
                width=window_width,
                height=window_height
            )
            canvas.pack()
            
            # 為每個候選繪製箭頭
            for i, candidate in enumerate(all_candidates):
                x_start = candidate['x_start']
                y = candidate['y']
                width = candidate['width']
                is_valid = min_threshold <= width <= max_threshold
                
                # 計算箭頭位置（相對於懸浮框視窗，不是絕對位置）
                arrow_x = x_start + width / 2  # 血條中心X
                arrow_y = y - 20  # 箭頭在血條上方20像素
                
                # 箭頭顏色：達到門檻用綠色，未達門檻用黃色
                arrow_color = "#00FF00" if is_valid else "#FFFF00"
                
                # 繪製箭頭（向下指向血條）
                points = [
                    arrow_x, arrow_y,
                    arrow_x - 10, arrow_y + 15,
                    arrow_x + 10, arrow_y + 15
                ]
                canvas.create_polygon(points, fill=arrow_color, outline=arrow_color, width=2)
                
                # 繪製寬度標籤
                label_text = f"{width}px"
                canvas.create_text(
                    arrow_x, arrow_y - 15,
                    text=label_text,
                    fill=arrow_color,
                    font=("Consolas", 10, "bold")
                )
            
            # 設置懸浮框位置和大小
            self.hp_bar_overlay_window.geometry(f"{window_width}x{window_height}+{int(window_x)}+{int(window_y)}")
            
        except Exception as e:
            self.logger.error(f"更新懸浮框內容失敗: {str(e)}")
    
    def create_calibration_window(self):
        """創建校準視窗"""
        if self.calibration_window:
            self.calibration_window.lift()
            return
        
        self.calibration_window = tk.Toplevel(self.root)
        self.calibration_window.title("校準設定")
        self.calibration_window.geometry("900x700")
        self.calibration_window.configure(bg=Theme.BACKGROUND_PRIMARY)
        self.calibration_window.protocol("WM_DELETE_WINDOW", self.toggle_calibration)
        
        # 創建滾動框架
        canvas = tk.Canvas(self.calibration_window, bg=Theme.BACKGROUND_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.calibration_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Theme.BACKGROUND_PRIMARY)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 載入當前配置
        config = self.config_manager.load()
        detection_config = config.get("detection", {})
        automation_config = config.get("automation", {})
        
        # 創建變數字典
        self.calibration_vars = {}
        
        # Detection 參數區塊 - 使用兩列布局
        detection_frame = SectionFrame(scrollable_frame, "檢測參數")
        detection_frame.get_frame().pack(fill="x", padx=10, pady=3)
        detection_inner = detection_frame.get_frame()
        
        # 創建兩列容器
        detection_left = tk.Frame(detection_inner, bg=Theme.BACKGROUND_PRIMARY)
        detection_left.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        detection_right = tk.Frame(detection_inner, bg=Theme.BACKGROUND_PRIMARY)
        detection_right.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        
        def create_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_PRIMARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_PRIMARY, fg=Theme.TEXT_PRIMARY, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(detection_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = tk.Entry(row, textvariable=var, width=8)
            entry.pack(side="left", padx=3)
            var.trace("w", lambda *args, key=param_key, v=var: self.on_calibration_change(key, v))
            if has_button and button_cmd:
                btn = tk.Button(row, text="顯示", command=button_cmd,
                              bg=Theme.BUTTON_SECONDARY, fg=Theme.BUTTON_SECONDARY_TEXT,
                              activebackground=Theme.BUTTON_SECONDARY_HOVER, activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                              font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'normal'), relief='flat', cursor='hand2', width=5)
                btn.pack(side="left", padx=3)
                return btn
            return None
        
        # 左列：血條相關參數
        self.show_hp_bar_y_btn = create_param_row(detection_left, "血條Y軸", "hp_bar_y", 445, True, self.toggle_hp_bar_y_line)
        create_param_row(detection_left, "血條最小寬度", "hp_bar_min_width", 40)
        create_param_row(detection_left, "血條最大寬度", "hp_bar_max_width", 45)
        create_param_row(detection_left, "R最小值", "color_r_min", 150)
        create_param_row(detection_left, "R最大值", "color_r_max", 255)
        create_param_row(detection_left, "G最大值", "color_g_max", 100)
        create_param_row(detection_left, "B最大值", "color_b_max", 100)
        
        # 右列：顏色檢測參數
        create_param_row(detection_right, "R/G比例", "color_r_g_ratio", 1.5)
        create_param_row(detection_right, "R/B比例", "color_r_b_ratio", 1.5)
        create_param_row(detection_right, "像素間隙容差", "pixel_gap_tolerance", 2)
        create_param_row(detection_right, "角色Y偏移", "character_y_offset", 15)
        
        # 提示視窗檢測參數 - 使用兩列布局
        dialog_section = SectionFrame(scrollable_frame, "提示視窗檢測參數")
        dialog_section.get_frame().pack(fill="x", padx=10, pady=3)
        dialog_inner = dialog_section.get_frame()
        
        # 創建兩列容器
        dialog_left = tk.Frame(dialog_inner, bg=Theme.BACKGROUND_PRIMARY)
        dialog_left.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        dialog_right = tk.Frame(dialog_inner, bg=Theme.BACKGROUND_PRIMARY)
        dialog_right.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        
        def create_dialog_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建對話框參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_PRIMARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_PRIMARY, fg=Theme.TEXT_PRIMARY, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(detection_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = tk.Entry(row, textvariable=var, width=8)
            entry.pack(side="left", padx=3)
            var.trace("w", lambda *args, key=param_key, v=var: self.on_calibration_change(key, v))
            if has_button and button_cmd:
                btn = tk.Button(row, text="顯示", command=button_cmd,
                              bg=Theme.BUTTON_SECONDARY, fg=Theme.BUTTON_SECONDARY_TEXT,
                              activebackground=Theme.BUTTON_SECONDARY_HOVER, activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                              font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'normal'), relief='flat', cursor='hand2', width=5)
                btn.pack(side="left", padx=3)
                return btn
            return None
        
        # 左列
        self.show_dialog_check_x_btn = create_dialog_param_row(dialog_left, "檢測區域X", "dialog_check_x", 500, True, self.toggle_dialog_check_x_line)
        create_dialog_param_row(dialog_left, "檢測區域寬度", "dialog_check_width", 200)
        create_dialog_param_row(dialog_left, "背景顏色R", "dialog_bg_r", 64)
        create_dialog_param_row(dialog_left, "背景顏色B", "dialog_bg_b", 223)
        
        # 右列
        self.show_dialog_check_y_btn = create_dialog_param_row(dialog_right, "檢測區域Y", "dialog_check_y", 300, True, self.toggle_dialog_check_y_line)
        create_dialog_param_row(dialog_right, "檢測區域高度", "dialog_check_height", 100)
        create_dialog_param_row(dialog_right, "背景顏色G", "dialog_bg_g", 164)
        create_dialog_param_row(dialog_right, "顏色容差", "dialog_bg_tolerance", 30)
        
        # 測試按鈕
        test_btn_row = tk.Frame(dialog_inner, bg=Theme.BACKGROUND_PRIMARY)
        test_btn_row.pack(fill="x", padx=5, pady=5)
        test_dialog_btn = tk.Button(test_btn_row, text="測試檢測提示視窗", command=self.test_dialog_detection,
                                    bg=Theme.BUTTON_SECONDARY, fg=Theme.BUTTON_SECONDARY_TEXT,
                                    activebackground=Theme.BUTTON_SECONDARY_HOVER, activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'), relief='flat', cursor='hand2')
        test_dialog_btn.pack(pady=3)
        
        # Automation 參數區塊 - 使用兩列布局
        automation_frame = SectionFrame(scrollable_frame, "自動化參數")
        automation_frame.get_frame().pack(fill="x", padx=10, pady=3)
        automation_inner = automation_frame.get_frame()
        
        # 創建兩列容器
        automation_left = tk.Frame(automation_inner, bg=Theme.BACKGROUND_PRIMARY)
        automation_left.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        automation_right = tk.Frame(automation_inner, bg=Theme.BACKGROUND_PRIMARY)
        automation_right.pack(side="left", fill="both", expand=True, padx=5, pady=3)
        
        def create_automation_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建自動化參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_PRIMARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_PRIMARY, fg=Theme.TEXT_PRIMARY, width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(automation_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = tk.Entry(row, textvariable=var, width=8)
            entry.pack(side="left", padx=3)
            var.trace("w", lambda *args, key=param_key, v=var: self.on_calibration_change(key, v))
            if has_button and button_cmd:
                btn = tk.Button(row, text="顯示", command=button_cmd,
                              bg=Theme.BUTTON_SECONDARY, fg=Theme.BUTTON_SECONDARY_TEXT,
                              activebackground=Theme.BUTTON_SECONDARY_HOVER, activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                              font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'normal'), relief='flat', cursor='hand2', width=5)
                btn.pack(side="left", padx=3)
                return btn
            return None
        
        # 左列：位置和按鈕相關
        self.show_exit_target_x_btn = create_automation_param_row(automation_left, "退出目標X", "exit_target_x", 250, True, self.toggle_exit_target_x_line)
        self.show_fm_button_x_btn = create_automation_param_row(automation_left, "自由市場按鈕X", "fm_button_x", 980, True, self.toggle_fm_button_x_line)
        self.show_fm_button_y_btn = create_automation_param_row(automation_left, "自由市場按鈕Y", "fm_button_y", 720, True, self.toggle_fm_button_y_line)
        self.show_dialog_close_x_btn = create_automation_param_row(automation_left, "提示框關閉按鈕X", "dialog_close_button_x", 600, True, self.toggle_dialog_close_x_line)
        self.show_dialog_close_y_btn = create_automation_param_row(automation_left, "提示框關閉按鈕Y", "dialog_close_button_y", 400, True, self.toggle_dialog_close_y_line)
        create_automation_param_row(automation_left, "移動容差", "move_tolerance", 20)
        create_automation_param_row(automation_left, "最大移動時間(秒)", "move_max_duration", 30)
        create_automation_param_row(automation_left, "防偵測最小移動", "anti_detect_min_moves", 0)
        create_automation_param_row(automation_left, "防偵測最大移動", "anti_detect_max_moves", 2)
        create_automation_param_row(automation_left, "防偵測間隔(秒)", "anti_detect_interval", 0.1)
        
        # 右列：時間和等待相關
        create_automation_param_row(automation_right, "按鍵等待(秒)", "key_press_wait", 0.2)
        create_automation_param_row(automation_right, "按鍵持續(秒)", "key_press_duration", 0.3)
        create_automation_param_row(automation_right, "按鈕點擊等待(秒)", "button_click_wait", 0.2)
        create_automation_param_row(automation_right, "按鈕點擊延遲(秒)", "button_click_delay", 0.1)
        create_automation_param_row(automation_right, "重試等待(秒)", "retry_wait", 0.5)
        create_automation_param_row(automation_right, "退出等待(秒)", "exit_wait", 0.5)
        create_automation_param_row(automation_right, "退出按鍵持續(秒)", "exit_key_duration", 0.3)
        create_automation_param_row(automation_right, "退出動畫等待(秒)", "exit_animation_wait", 2.0)
        create_automation_param_row(automation_right, "進入重試等待(秒)", "enter_retry_wait", 3.0)
        create_automation_param_row(automation_right, "技能間隔隨機範圍(%)", "skill_interval_random_range", 20)
        
        # 保存按鈕
        btn_frame = tk.Frame(scrollable_frame, bg=Theme.BACKGROUND_PRIMARY)
        btn_frame.pack(fill="x", padx=10, pady=5)
        save_btn = tk.Button(btn_frame, text="保存校準數值", command=self.save_calibration_config, 
                            bg=Theme.BUTTON_PRIMARY, fg=Theme.BUTTON_PRIMARY_TEXT,
                            activebackground=Theme.BUTTON_PRIMARY_HOVER, activeforeground=Theme.BUTTON_PRIMARY_TEXT,
                            font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'), relief='flat', cursor='hand2')
        save_btn.pack(pady=3)
    
    def on_calibration_change(self, param_key, var):
        """當校準參數改變時的回調 - 只更新屬性值，不重新初始化管理器"""
        try:
            value = var.get()
            
            # 判斷參數類型並直接更新管理器屬性
            if param_key in ["hp_bar_y", "hp_bar_min_width", "hp_bar_max_width", "color_r_min", "color_r_max", 
                        "color_g_max", "color_b_max", "pixel_gap_tolerance", "character_y_offset",
                        "dialog_check_x", "dialog_check_y", "dialog_check_width", "dialog_check_height",
                        "dialog_bg_r", "dialog_bg_g", "dialog_bg_b", "dialog_bg_tolerance"]:
                # Detection 參數（整數）
                if param_key in ["color_r_g_ratio", "color_r_b_ratio"]:
                    setattr(self.detection_manager, param_key, float(value))
                else:
                    setattr(self.detection_manager, param_key, int(float(value)))
            elif param_key in ["exit_target_x", "fm_button_x", "fm_button_y", "move_tolerance", 
                            "anti_detect_min_moves", "anti_detect_max_moves", "dialog_close_button_x", "dialog_close_button_y"]:
                # Automation 參數（整數）
                setattr(self.automation_manager, param_key, int(float(value)))
            elif param_key in ["color_r_g_ratio", "color_r_b_ratio"]:
                # Detection 參數（浮點數）
                setattr(self.detection_manager, param_key, float(value))
            else:
                # Automation 參數（浮點數）
                setattr(self.automation_manager, param_key, float(value))
            
            # 觸發overlay更新
            if self.show_calibration:
                self.root.after(10, self._schedule_calibration_overlay_update)
            
        except (ValueError, TypeError) as e:
            # 無效值，忽略（可能是用戶正在輸入中）
            pass
    
    def save_calibration_config(self):
        """保存校準配置"""
        try:
            if not hasattr(self, 'calibration_vars') or not self.calibration_vars:
                messagebox.showwarning("警告", "沒有可保存的配置")
                return
            
            config = self.config_manager.load()
            
            # 更新所有參數到配置
            for param_key, var in self.calibration_vars.items():
                value = var.get()
                try:
                    if param_key in ["hp_bar_y", "hp_bar_min_width", "hp_bar_max_width", "color_r_min", "color_r_max", 
                                    "color_g_max", "color_b_max", "pixel_gap_tolerance", "character_y_offset",
                                    "dialog_check_x", "dialog_check_y", "dialog_check_width", "dialog_check_height",
                                    "dialog_bg_r", "dialog_bg_g", "dialog_bg_b", "dialog_bg_tolerance"]:
                        # Detection 參數（整數）
                        if param_key in ["color_r_g_ratio", "color_r_b_ratio"]:
                            config.setdefault("detection", {})[param_key] = float(value)
                        else:
                            config.setdefault("detection", {})[param_key] = int(float(value))
                    elif param_key in ["exit_target_x", "fm_button_x", "fm_button_y", "move_tolerance", 
                                    "anti_detect_min_moves", "anti_detect_max_moves", "dialog_close_button_x", "dialog_close_button_y"]:
                        # Automation 參數（整數）
                        config.setdefault("automation", {})[param_key] = int(float(value))
                    elif param_key in ["color_r_g_ratio", "color_r_b_ratio"]:
                        # Detection 參數（浮點數）
                        config.setdefault("detection", {})[param_key] = float(value)
                    else:
                        # Automation 參數（浮點數）
                        config.setdefault("automation", {})[param_key] = float(value)
                except (ValueError, TypeError):
                    continue
            
            self.config_manager.save(config)
            messagebox.showinfo("成功", "校準數值已保存")
        except Exception as e:
            self.logger.error(f"保存校準配置失敗: {str(e)}")
            messagebox.showerror("錯誤", f"保存配置失敗: {str(e)}")
    
    def _schedule_calibration_overlay_update(self):
        """安排校準overlay更新（按需更新，不持續循環）"""
        if not self.show_calibration:
            return
        
        if not self.window_manager.is_valid():
            if self.calibration_overlay_window:
                try:
                    self.calibration_overlay_window.withdraw()
                except:
                    pass
            return
        
        try:
            rect = self.window_manager.get_window_rect()
            if not rect:
                return
            
            window_x, window_y, window_width, window_height = rect
            
            # 創建或更新overlay視窗
            if not self.calibration_overlay_window:
                self._create_calibration_overlay_window()
            
            if self.calibration_overlay_window:
                try:
                    self._update_calibration_overlay(window_x, window_y, window_width, window_height)
                    self.calibration_overlay_window.deiconify()
                    self.calibration_overlay_window.lift()
                except Exception as e:
                    self.logger.error(f"更新校準overlay失敗: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"更新校準overlay位置失敗: {str(e)}")
    
    def _create_calibration_overlay_window(self):
        """創建校準overlay視窗"""
        try:
            self.calibration_overlay_window = tk.Toplevel(self.root)
            self.calibration_overlay_window.overrideredirect(True)  # 移除標題欄
            self.calibration_overlay_window.attributes("-topmost", True)  # 置頂
            self.calibration_overlay_window.attributes("-transparentcolor", "black")  # 黑色透明
            self.calibration_overlay_window.configure(bg="black")
            self.calibration_overlay_window.geometry("1x1+0+0")  # 初始大小
        except Exception as e:
            self.logger.error(f"創建校準overlay視窗失敗: {str(e)}")
            self.calibration_overlay_window = None
    
    def _update_calibration_overlay(self, window_x, window_y, window_width, window_height):
        """更新校準overlay內容"""
        if not self.calibration_overlay_window:
            return
        
        try:
            # 清除舊的內容
            for widget in self.calibration_overlay_window.winfo_children():
                widget.destroy()
            
            # 如果沒有任何參考線需要顯示，隱藏overlay
            if not (self.show_hp_bar_y_line or self.show_exit_target_x_line or self.show_fm_button_marker or 
                    self.show_fm_button_x_line or self.show_fm_button_y_line or 
                    self.show_dialog_close_x_line or self.show_dialog_close_y_line or
                    self.show_dialog_check_x_line or self.show_dialog_check_y_line):
                self.calibration_overlay_window.withdraw()
                return
            
            # 創建Canvas來繪製參考線
            canvas = tk.Canvas(
                self.calibration_overlay_window,
                bg="black",
                highlightthickness=0,
                width=window_width,
                height=window_height,
                cursor="crosshair"
            )
            canvas.pack()
            self.calibration_canvas = canvas
            
            # 從管理器的當前屬性值獲取（優先），如果沒有則從配置讀取
            # 這樣可以反映用戶在輸入框中修改但尚未保存的值
            
            # 根據狀態繪製參考線
            if self.show_hp_bar_y_line:
                # 繪製血條Y軸參考線（可拖動）
                # 優先從管理器屬性讀取，如果沒有則從配置讀取
                hp_bar_y = getattr(self.detection_manager, 'hp_bar_y', None)
                if hp_bar_y is None:
                    config = self.config_manager.load()
                    detection_config = config.get("detection", {})
                    hp_bar_y = detection_config.get("hp_bar_y", 445)
                line_id = canvas.create_line(0, hp_bar_y, window_width, hp_bar_y, fill="#FF0000", width=4, dash=(5, 5), tags="hp_bar_y_line")
                text_id = canvas.create_text(10, hp_bar_y - 15, text=f"Y={hp_bar_y} (可拖動)", fill="#FF0000", font=("Consolas", 10, "bold"), anchor="w", tags="hp_bar_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, hp_bar_y - 5, window_width, hp_bar_y + 5, 
                                 outline="#FF0000", fill="#FF0000", width=2, tags="hp_bar_y_handle")
            
            if self.show_exit_target_x_line:
                # 繪製退出目標X軸參考線（可拖動）
                exit_target_x = getattr(self.automation_manager, 'exit_target_x', None)
                if exit_target_x is None:
                    config = self.config_manager.load()
                    automation_config = config.get("automation", {})
                    exit_target_x = automation_config.get("exit_target_x", 250)
                line_id = canvas.create_line(exit_target_x, 0, exit_target_x, window_height, fill="#00FF00", width=4, dash=(5, 5), tags="exit_target_x_line")
                text_id = canvas.create_text(exit_target_x + 5, 10, text=f"X={exit_target_x} (可拖動)", fill="#00FF00", font=("Consolas", 10, "bold"), anchor="w", tags="exit_target_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(exit_target_x - 5, window_height - 20, exit_target_x + 5, window_height, 
                                 outline="#00FF00", fill="#00FF00", width=2, tags="exit_target_x_handle")
            
            # 繪製自由市場按鈕相關參考線
            fm_button_x = getattr(self.automation_manager, 'fm_button_x', None)
            if fm_button_x is None:
                config = self.config_manager.load()
                automation_config = config.get("automation", {})
                fm_button_x = automation_config.get("fm_button_x", 980)
            
            fm_button_y = getattr(self.automation_manager, 'fm_button_y', None)
            if fm_button_y is None:
                if 'config' not in locals():
                    config = self.config_manager.load()
                    automation_config = config.get("automation", {})
                fm_button_y = automation_config.get("fm_button_y", 720)
            
            if self.show_fm_button_x_line:
                # 繪製自由市場按鈕X軸參考線（可拖動）
                canvas.create_line(fm_button_x, 0, fm_button_x, window_height, fill="#00FFFF", width=3, dash=(3, 3), tags="fm_button_x_line")
                canvas.create_text(fm_button_x + 5, 10, text=f"按鈕X={fm_button_x} (可拖動)", fill="#00FFFF", font=("Consolas", 9, "bold"), anchor="w", tags="fm_button_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(fm_button_x - 5, window_height - 20, fm_button_x + 5, window_height, 
                                 outline="#00FFFF", fill="#00FFFF", width=2, tags="fm_button_x_handle")
            
            if self.show_fm_button_y_line:
                # 繪製自由市場按鈕Y軸參考線（可拖動）
                canvas.create_line(0, fm_button_y, window_width, fm_button_y, fill="#00FFFF", width=3, dash=(3, 3), tags="fm_button_y_line")
                canvas.create_text(10, fm_button_y - 15, text=f"按鈕Y={fm_button_y} (可拖動)", fill="#00FFFF", font=("Consolas", 9, "bold"), anchor="w", tags="fm_button_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, fm_button_y - 5, window_width, fm_button_y + 5, 
                                 outline="#00FFFF", fill="#00FFFF", width=2, tags="fm_button_y_handle")
            
            if self.show_fm_button_marker:
                # 繪製自由市場按鈕位置標記（可拖動）
                canvas.create_oval(fm_button_x - 8, fm_button_y - 8, fm_button_x + 8, fm_button_y + 8, 
                                 outline="#00FFFF", width=3, fill="", tags="fm_button_circle")
                canvas.create_text(fm_button_x + 15, fm_button_y, text=f"({fm_button_x}, {fm_button_y}) (可拖動)", 
                                 fill="#00FFFF", font=("Consolas", 10, "bold"), anchor="w", tags="fm_button_text")
            
            # 繪製提示框關閉按鈕參考線
            dialog_close_x = getattr(self.automation_manager, 'dialog_close_button_x', None)
            if dialog_close_x is None:
                if 'config' not in locals():
                    config = self.config_manager.load()
                    automation_config = config.get("automation", {})
                dialog_close_x = automation_config.get("dialog_close_button_x", 600)
            
            dialog_close_y = getattr(self.automation_manager, 'dialog_close_button_y', None)
            if dialog_close_y is None:
                if 'config' not in locals():
                    config = self.config_manager.load()
                    automation_config = config.get("automation", {})
                dialog_close_y = automation_config.get("dialog_close_button_y", 400)
            
            if self.show_dialog_close_x_line:
                # 繪製提示框關閉按鈕X軸參考線（可拖動）
                canvas.create_line(dialog_close_x, 0, dialog_close_x, window_height, fill="#FF00FF", width=3, dash=(3, 3), tags="dialog_close_x_line")
                canvas.create_text(dialog_close_x + 5, 30, text=f"關閉X={dialog_close_x} (可拖動)", fill="#FF00FF", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_close_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(dialog_close_x - 5, window_height - 20, dialog_close_x + 5, window_height, 
                                 outline="#FF00FF", fill="#FF00FF", width=2, tags="dialog_close_x_handle")
            
            if self.show_dialog_close_y_line:
                # 繪製提示框關閉按鈕Y軸參考線（可拖動）
                canvas.create_line(0, dialog_close_y, window_width, dialog_close_y, fill="#FF00FF", width=3, dash=(3, 3), tags="dialog_close_y_line")
                canvas.create_text(10, dialog_close_y - 15, text=f"關閉Y={dialog_close_y} (可拖動)", fill="#FF00FF", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_close_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, dialog_close_y - 5, window_width, dialog_close_y + 5, 
                                 outline="#FF00FF", fill="#FF00FF", width=2, tags="dialog_close_y_handle")
            
            # 繪製檢測區域參考線
            dialog_check_x = getattr(self.detection_manager, 'dialog_check_x', None)
            dialog_check_y = getattr(self.detection_manager, 'dialog_check_y', None)
            dialog_check_width = getattr(self.detection_manager, 'dialog_check_width', None)
            dialog_check_height = getattr(self.detection_manager, 'dialog_check_height', None)
            
            if dialog_check_x is None or dialog_check_y is None:
                if 'config' not in locals():
                    config = self.config_manager.load()
                    detection_config = config.get("detection", {})
                dialog_check_x = dialog_check_x or detection_config.get("dialog_check_x", 500)
                dialog_check_y = dialog_check_y or detection_config.get("dialog_check_y", 300)
                dialog_check_width = dialog_check_width or detection_config.get("dialog_check_width", 200)
                dialog_check_height = dialog_check_height or detection_config.get("dialog_check_height", 100)
            
            if self.show_dialog_check_x_line:
                # 繪製檢測區域X軸參考線（可拖動，顯示區域的左右邊界）
                canvas.create_line(dialog_check_x, 0, dialog_check_x, window_height, fill="#FFFF00", width=3, dash=(3, 3), tags="dialog_check_x_line")
                canvas.create_text(dialog_check_x + 5, 50, text=f"檢測X={dialog_check_x} (可拖動)", fill="#FFFF00", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(dialog_check_x - 5, window_height - 20, dialog_check_x + 5, window_height, 
                                 outline="#FFFF00", fill="#FFFF00", width=2, tags="dialog_check_x_handle")
                if dialog_check_width > 0:
                    right_x = dialog_check_x + dialog_check_width
                    canvas.create_line(right_x, 0, right_x, window_height, fill="#FFFF00", width=2, dash=(3, 3), tags="dialog_check_x_right_line")
                    canvas.create_text(right_x + 5, 70, text=f"X+寬={right_x}", fill="#FFFF00", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_x_right_text")
            
            if self.show_dialog_check_y_line:
                # 繪製檢測區域Y軸參考線（可拖動，顯示區域的上下邊界）
                canvas.create_line(0, dialog_check_y, window_width, dialog_check_y, fill="#FFFF00", width=3, dash=(3, 3), tags="dialog_check_y_line")
                canvas.create_text(10, dialog_check_y - 15, text=f"檢測Y={dialog_check_y} (可拖動)", fill="#FFFF00", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, dialog_check_y - 5, window_width, dialog_check_y + 5, 
                                 outline="#FFFF00", fill="#FFFF00", width=2, tags="dialog_check_y_handle")
                if dialog_check_height > 0:
                    bottom_y = dialog_check_y + dialog_check_height
                    canvas.create_line(0, bottom_y, window_width, bottom_y, fill="#FFFF00", width=2, dash=(3, 3), tags="dialog_check_y_bottom_line")
                    canvas.create_text(10, bottom_y + 15, text=f"Y+高={bottom_y}", fill="#FFFF00", font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_y_bottom_text")
            
            # 綁定滑鼠事件
            canvas.bind("<Button-1>", lambda e: self._on_calibration_canvas_click(e, window_x, window_y))
            canvas.bind("<B1-Motion>", lambda e: self._on_calibration_canvas_drag(e, window_x, window_y, window_width, window_height))
            canvas.bind("<ButtonRelease-1>", lambda e: self._on_calibration_canvas_release())
            
            # 只有在顯示任何參考線時才顯示滑鼠座標（按需更新，不持續追蹤）
            if (self.show_hp_bar_y_line or self.show_exit_target_x_line or self.show_fm_button_marker or
                self.show_fm_button_x_line or self.show_fm_button_y_line or
                self.show_dialog_close_x_line or self.show_dialog_close_y_line or
                self.show_dialog_check_x_line or self.show_dialog_check_y_line):
                try:
                    import win32api
                    mouse_x, mouse_y = win32api.GetCursorPos()
                    # 轉換為相對視窗的座標
                    rel_x = mouse_x - int(window_x)
                    rel_y = mouse_y - int(window_y)
                    
                    if 0 <= rel_x <= window_width and 0 <= rel_y <= window_height:
                        # 顯示滑鼠座標
                        canvas.create_text(window_width - 100, 10, 
                                         text=f"滑鼠: ({rel_x}, {rel_y})", 
                                         fill="#FFFF00", font=("Consolas", 10, "bold"), anchor="e")
                except:
                    pass
            
            # 設置overlay位置和大小
            self.calibration_overlay_window.geometry(f"{window_width}x{window_height}+{int(window_x)}+{int(window_y)}")
            
        except Exception as e:
            self.logger.error(f"更新校準overlay內容失敗: {str(e)}")
    
    def _on_calibration_canvas_click(self, event, window_x, window_y):
        """處理校準Canvas的點擊事件"""
        if not self.calibration_canvas:
            return
        
        x, y = event.x, event.y
        drag_tolerance = 10  # 拖動容差範圍
        
        # 獲取當前配置值（優先從管理器屬性讀取）
        hp_bar_y = getattr(self.detection_manager, 'hp_bar_y', None)
        if hp_bar_y is None:
            config = self.config_manager.load()
            detection_config = config.get("detection", {})
            automation_config = config.get("automation", {})
            hp_bar_y = detection_config.get("hp_bar_y", 445)
            exit_target_x = automation_config.get("exit_target_x", 250)
            fm_button_x = automation_config.get("fm_button_x", 980)
            fm_button_y = automation_config.get("fm_button_y", 720)
            dialog_close_x = automation_config.get("dialog_close_button_x", 600)
            dialog_close_y = automation_config.get("dialog_close_button_y", 400)
            dialog_check_x = detection_config.get("dialog_check_x", 500)
            dialog_check_y = detection_config.get("dialog_check_y", 300)
        else:
            exit_target_x = getattr(self.automation_manager, 'exit_target_x', 250)
            fm_button_x = getattr(self.automation_manager, 'fm_button_x', 980)
            fm_button_y = getattr(self.automation_manager, 'fm_button_y', 720)
            dialog_close_x = getattr(self.automation_manager, 'dialog_close_button_x', 600)
            dialog_close_y = getattr(self.automation_manager, 'dialog_close_button_y', 400)
            dialog_check_x = getattr(self.detection_manager, 'dialog_check_x', 500)
            dialog_check_y = getattr(self.detection_manager, 'dialog_check_y', 300)
        
        # 檢查是否點擊在血條Y軸參考線上
        if self.show_hp_bar_y_line and abs(y - hp_bar_y) <= drag_tolerance:
            self.calibration_dragging = 'hp_bar_y'
            self.calibration_drag_start_pos = y
            self.calibration_canvas.config(cursor="sb_v_double_arrow")
            return
        
        # 檢查是否點擊在退出目標X軸參考線上
        if self.show_exit_target_x_line and abs(x - exit_target_x) <= drag_tolerance:
            self.calibration_dragging = 'exit_target_x'
            self.calibration_drag_start_pos = x
            self.calibration_canvas.config(cursor="sb_h_double_arrow")
            return
        
        # 檢查是否點擊在自由市場按鈕位置上
        if self.show_fm_button_marker and abs(x - fm_button_x) <= drag_tolerance * 2 and abs(y - fm_button_y) <= drag_tolerance * 2:
            self.calibration_dragging = 'fm_button'
            self.calibration_drag_start_pos = (x, y)
            self.calibration_canvas.config(cursor="fleur")
            return
        
        # 檢查是否點擊在自由市場按鈕X軸參考線上
        if self.show_fm_button_x_line and abs(x - fm_button_x) <= drag_tolerance:
            self.calibration_dragging = 'fm_button_x'
            self.calibration_drag_start_pos = x
            self.calibration_canvas.config(cursor="sb_h_double_arrow")
            return
        
        # 檢查是否點擊在自由市場按鈕Y軸參考線上
        if self.show_fm_button_y_line and abs(y - fm_button_y) <= drag_tolerance:
            self.calibration_dragging = 'fm_button_y'
            self.calibration_drag_start_pos = y
            self.calibration_canvas.config(cursor="sb_v_double_arrow")
            return
        
        # 檢查是否點擊在提示框關閉按鈕X軸參考線上
        if self.show_dialog_close_x_line and abs(x - dialog_close_x) <= drag_tolerance:
            self.calibration_dragging = 'dialog_close_x'
            self.calibration_drag_start_pos = x
            self.calibration_canvas.config(cursor="sb_h_double_arrow")
            return
        
        # 檢查是否點擊在提示框關閉按鈕Y軸參考線上
        if self.show_dialog_close_y_line and abs(y - dialog_close_y) <= drag_tolerance:
            self.calibration_dragging = 'dialog_close_y'
            self.calibration_drag_start_pos = y
            self.calibration_canvas.config(cursor="sb_v_double_arrow")
            return
        
        # 檢查是否點擊在檢測區域X軸參考線上
        if self.show_dialog_check_x_line and abs(x - dialog_check_x) <= drag_tolerance:
            self.calibration_dragging = 'dialog_check_x'
            self.calibration_drag_start_pos = x
            self.calibration_canvas.config(cursor="sb_h_double_arrow")
            return
        
        # 檢查是否點擊在檢測區域Y軸參考線上
        if self.show_dialog_check_y_line and abs(y - dialog_check_y) <= drag_tolerance:
            self.calibration_dragging = 'dialog_check_y'
            self.calibration_drag_start_pos = y
            self.calibration_canvas.config(cursor="sb_v_double_arrow")
            return
        
        self.calibration_dragging = None
        self.calibration_canvas.config(cursor="crosshair")
    
    def _on_calibration_canvas_drag(self, event, window_x, window_y, window_width, window_height):
        """處理校準Canvas的拖動事件"""
        if not self.calibration_canvas or not self.calibration_dragging:
            return
        
        x, y = event.x, event.y
        
        # 限制在視窗範圍內
        x = max(0, min(x, window_width))
        y = max(0, min(y, window_height))
        
        if self.calibration_dragging == 'hp_bar_y':
            # 拖動血條Y軸
            new_y = int(y)
            # 更新配置和管理器
            self.detection_manager.hp_bar_y = new_y
            # 更新Canvas顯示
            self.calibration_canvas.coords("hp_bar_y_line", 0, new_y, window_width, new_y)
            self.calibration_canvas.coords("hp_bar_y_text", 10, new_y - 15)
            self.calibration_canvas.itemconfig("hp_bar_y_text", text=f"Y={new_y} (可拖動)")
            self.calibration_canvas.coords("hp_bar_y_handle", window_width - 20, new_y - 5, window_width, new_y + 5)
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'hp_bar_y' in self.calibration_vars:
                self.calibration_vars['hp_bar_y'].set(str(new_y))
        
        elif self.calibration_dragging == 'exit_target_x':
            # 拖動退出目標X軸
            new_x = int(x)
            # 更新配置和管理器
            self.automation_manager.exit_target_x = new_x
            # 更新Canvas顯示
            self.calibration_canvas.coords("exit_target_x_line", new_x, 0, new_x, window_height)
            self.calibration_canvas.coords("exit_target_x_text", new_x + 5, 10)
            self.calibration_canvas.itemconfig("exit_target_x_text", text=f"X={new_x} (可拖動)")
            self.calibration_canvas.coords("exit_target_x_handle", new_x - 5, window_height - 20, new_x + 5, window_height)
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'exit_target_x' in self.calibration_vars:
                self.calibration_vars['exit_target_x'].set(str(new_x))
        
        elif self.calibration_dragging == 'fm_button':
            # 拖動自由市場按鈕位置
            new_x = int(x)
            new_y = int(y)
            # 更新配置和管理器
            self.automation_manager.fm_button_x = new_x
            self.automation_manager.fm_button_y = new_y
            # 更新Canvas顯示
            self.calibration_canvas.coords("fm_button_circle", new_x - 8, new_y - 8, new_x + 8, new_y + 8)
            self.calibration_canvas.coords("fm_button_text", new_x + 15, new_y)
            self.calibration_canvas.itemconfig("fm_button_text", text=f"({new_x}, {new_y}) (可拖動)")
            # 更新X/Y軸參考線（如果顯示）
            if self.show_fm_button_x_line:
                self.calibration_canvas.coords("fm_button_x_line", new_x, 0, new_x, window_height)
                self.calibration_canvas.coords("fm_button_x_text", new_x + 5, 10)
                self.calibration_canvas.itemconfig("fm_button_x_text", text=f"按鈕X={new_x} (可拖動)")
                self.calibration_canvas.coords("fm_button_x_handle", new_x - 5, window_height - 20, new_x + 5, window_height)
            if self.show_fm_button_y_line:
                self.calibration_canvas.coords("fm_button_y_line", 0, new_y, window_width, new_y)
                self.calibration_canvas.coords("fm_button_y_text", 10, new_y - 15)
                self.calibration_canvas.itemconfig("fm_button_y_text", text=f"按鈕Y={new_y} (可拖動)")
                self.calibration_canvas.coords("fm_button_y_handle", window_width - 20, new_y - 5, window_width, new_y + 5)
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars'):
                if 'fm_button_x' in self.calibration_vars:
                    self.calibration_vars['fm_button_x'].set(str(new_x))
                if 'fm_button_y' in self.calibration_vars:
                    self.calibration_vars['fm_button_y'].set(str(new_y))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'fm_button_x':
            # 拖動自由市場按鈕X軸
            new_x = int(x)
            # 更新配置和管理器
            self.automation_manager.fm_button_x = new_x
            # 更新Canvas顯示
            self.calibration_canvas.coords("fm_button_x_line", new_x, 0, new_x, window_height)
            self.calibration_canvas.coords("fm_button_x_text", new_x + 5, 10)
            self.calibration_canvas.itemconfig("fm_button_x_text", text=f"按鈕X={new_x} (可拖動)")
            self.calibration_canvas.coords("fm_button_x_handle", new_x - 5, window_height - 20, new_x + 5, window_height)
            # 更新按鈕標記（如果顯示）
            if self.show_fm_button_marker:
                fm_button_y = getattr(self.automation_manager, 'fm_button_y', 720)
                self.calibration_canvas.coords("fm_button_circle", new_x - 8, fm_button_y - 8, new_x + 8, fm_button_y + 8)
                self.calibration_canvas.coords("fm_button_text", new_x + 15, fm_button_y)
                self.calibration_canvas.itemconfig("fm_button_text", text=f"({new_x}, {fm_button_y}) (可拖動)")
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'fm_button_x' in self.calibration_vars:
                self.calibration_vars['fm_button_x'].set(str(new_x))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'fm_button_y':
            # 拖動自由市場按鈕Y軸
            new_y = int(y)
            # 更新配置和管理器
            self.automation_manager.fm_button_y = new_y
            # 更新Canvas顯示
            self.calibration_canvas.coords("fm_button_y_line", 0, new_y, window_width, new_y)
            self.calibration_canvas.coords("fm_button_y_text", 10, new_y - 15)
            self.calibration_canvas.itemconfig("fm_button_y_text", text=f"按鈕Y={new_y} (可拖動)")
            self.calibration_canvas.coords("fm_button_y_handle", window_width - 20, new_y - 5, window_width, new_y + 5)
            # 更新按鈕標記（如果顯示）
            if self.show_fm_button_marker:
                fm_button_x = getattr(self.automation_manager, 'fm_button_x', 980)
                self.calibration_canvas.coords("fm_button_circle", fm_button_x - 8, new_y - 8, fm_button_x + 8, new_y + 8)
                self.calibration_canvas.coords("fm_button_text", fm_button_x + 15, new_y)
                self.calibration_canvas.itemconfig("fm_button_text", text=f"({fm_button_x}, {new_y}) (可拖動)")
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'fm_button_y' in self.calibration_vars:
                self.calibration_vars['fm_button_y'].set(str(new_y))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'dialog_close_x':
            # 拖動提示框關閉按鈕X軸
            new_x = int(x)
            # 更新配置和管理器
            self.automation_manager.dialog_close_button_x = new_x
            # 更新Canvas顯示
            self.calibration_canvas.coords("dialog_close_x_line", new_x, 0, new_x, window_height)
            self.calibration_canvas.coords("dialog_close_x_text", new_x + 5, 30)
            self.calibration_canvas.itemconfig("dialog_close_x_text", text=f"關閉X={new_x} (可拖動)")
            self.calibration_canvas.coords("dialog_close_x_handle", new_x - 5, window_height - 20, new_x + 5, window_height)
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'dialog_close_button_x' in self.calibration_vars:
                self.calibration_vars['dialog_close_button_x'].set(str(new_x))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'dialog_close_y':
            # 拖動提示框關閉按鈕Y軸
            new_y = int(y)
            # 更新配置和管理器
            self.automation_manager.dialog_close_button_y = new_y
            # 更新Canvas顯示
            self.calibration_canvas.coords("dialog_close_y_line", 0, new_y, window_width, new_y)
            self.calibration_canvas.coords("dialog_close_y_text", 10, new_y - 15)
            self.calibration_canvas.itemconfig("dialog_close_y_text", text=f"關閉Y={new_y} (可拖動)")
            self.calibration_canvas.coords("dialog_close_y_handle", window_width - 20, new_y - 5, window_width, new_y + 5)
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'dialog_close_button_y' in self.calibration_vars:
                self.calibration_vars['dialog_close_button_y'].set(str(new_y))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'dialog_check_x':
            # 拖動檢測區域X軸
            new_x = int(x)
            # 更新配置和管理器
            self.detection_manager.dialog_check_x = new_x
            # 更新Canvas顯示
            self.calibration_canvas.coords("dialog_check_x_line", new_x, 0, new_x, window_height)
            self.calibration_canvas.coords("dialog_check_x_text", new_x + 5, 50)
            self.calibration_canvas.itemconfig("dialog_check_x_text", text=f"檢測X={new_x} (可拖動)")
            self.calibration_canvas.coords("dialog_check_x_handle", new_x - 5, window_height - 20, new_x + 5, window_height)
            # 更新右邊界線（如果顯示）
            dialog_check_width = getattr(self.detection_manager, 'dialog_check_width', 200)
            if dialog_check_width > 0:
                right_x = new_x + dialog_check_width
                self.calibration_canvas.coords("dialog_check_x_right_line", right_x, 0, right_x, window_height)
                self.calibration_canvas.coords("dialog_check_x_right_text", right_x + 5, 70)
                self.calibration_canvas.itemconfig("dialog_check_x_right_text", text=f"X+寬={right_x}")
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'dialog_check_x' in self.calibration_vars:
                self.calibration_vars['dialog_check_x'].set(str(new_x))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
        
        elif self.calibration_dragging == 'dialog_check_y':
            # 拖動檢測區域Y軸
            new_y = int(y)
            # 更新配置和管理器
            self.detection_manager.dialog_check_y = new_y
            # 更新Canvas顯示
            self.calibration_canvas.coords("dialog_check_y_line", 0, new_y, window_width, new_y)
            self.calibration_canvas.coords("dialog_check_y_text", 10, new_y - 15)
            self.calibration_canvas.itemconfig("dialog_check_y_text", text=f"檢測Y={new_y} (可拖動)")
            self.calibration_canvas.coords("dialog_check_y_handle", window_width - 20, new_y - 5, window_width, new_y + 5)
            # 更新下邊界線（如果顯示）
            dialog_check_height = getattr(self.detection_manager, 'dialog_check_height', 100)
            if dialog_check_height > 0:
                bottom_y = new_y + dialog_check_height
                self.calibration_canvas.coords("dialog_check_y_bottom_line", 0, bottom_y, window_width, bottom_y)
                self.calibration_canvas.coords("dialog_check_y_bottom_text", 10, bottom_y + 15)
                self.calibration_canvas.itemconfig("dialog_check_y_bottom_text", text=f"Y+高={bottom_y}")
            # 更新校準視窗中的輸入框
            if hasattr(self, 'calibration_vars') and 'dialog_check_y' in self.calibration_vars:
                self.calibration_vars['dialog_check_y'].set(str(new_y))
            # 觸發overlay更新
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def _on_calibration_canvas_release(self):
        """處理校準Canvas的釋放事件"""
        if self.calibration_canvas:
            self.calibration_canvas.config(cursor="crosshair")
        self.calibration_dragging = None
        self.calibration_drag_start_pos = None
    
    def toggle_hp_bar_y_line(self):
        """切換血條Y軸參考線顯示"""
        self.show_hp_bar_y_line = not self.show_hp_bar_y_line
        if hasattr(self, 'show_hp_bar_y_btn'):
            self.show_hp_bar_y_btn.config(text="隱藏" if self.show_hp_bar_y_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_exit_target_x_line(self):
        """切換退出目標X軸參考線顯示"""
        self.show_exit_target_x_line = not self.show_exit_target_x_line
        if hasattr(self, 'show_exit_target_x_btn'):
            self.show_exit_target_x_btn.config(text="隱藏" if self.show_exit_target_x_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_fm_button_marker(self):
        """切換自由市場按鈕標記顯示"""
        self.show_fm_button_marker = not self.show_fm_button_marker
        if hasattr(self, 'show_fm_button_btn'):
            self.show_fm_button_btn.config(text="隱藏" if self.show_fm_button_marker else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_fm_button_x_line(self):
        """切換自由市場按鈕X軸參考線顯示"""
        self.show_fm_button_x_line = not self.show_fm_button_x_line
        if hasattr(self, 'show_fm_button_x_btn'):
            self.show_fm_button_x_btn.config(text="隱藏" if self.show_fm_button_x_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_fm_button_y_line(self):
        """切換自由市場按鈕Y軸參考線顯示"""
        self.show_fm_button_y_line = not self.show_fm_button_y_line
        if hasattr(self, 'show_fm_button_y_btn'):
            self.show_fm_button_y_btn.config(text="隱藏" if self.show_fm_button_y_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_dialog_close_x_line(self):
        """切換提示框關閉按鈕X軸參考線顯示"""
        self.show_dialog_close_x_line = not self.show_dialog_close_x_line
        if hasattr(self, 'show_dialog_close_x_btn'):
            self.show_dialog_close_x_btn.config(text="隱藏" if self.show_dialog_close_x_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_dialog_close_y_line(self):
        """切換提示框關閉按鈕Y軸參考線顯示"""
        self.show_dialog_close_y_line = not self.show_dialog_close_y_line
        if hasattr(self, 'show_dialog_close_y_btn'):
            self.show_dialog_close_y_btn.config(text="隱藏" if self.show_dialog_close_y_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_dialog_check_x_line(self):
        """切換檢測區域X軸參考線顯示"""
        self.show_dialog_check_x_line = not self.show_dialog_check_x_line
        if hasattr(self, 'show_dialog_check_x_btn'):
            self.show_dialog_check_x_btn.config(text="隱藏" if self.show_dialog_check_x_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def toggle_dialog_check_y_line(self):
        """切換檢測區域Y軸參考線顯示"""
        self.show_dialog_check_y_line = not self.show_dialog_check_y_line
        if hasattr(self, 'show_dialog_check_y_btn'):
            self.show_dialog_check_y_btn.config(text="隱藏" if self.show_dialog_check_y_line else "顯示")
        # 觸發overlay更新
        if self.show_calibration:
            self.root.after(10, self._schedule_calibration_overlay_update)
    
    def convert_to_floating_window(self):
        """創建簡化的半透明懸浮視窗，只顯示倒數時間和結束按鈕"""
        try:
            # 隱藏主視窗
            self.root.withdraw()
            
            # 獲取遊戲視窗位置
            game_rect = self.window_manager.get_window_rect()
            if not game_rect:
                self.logger.warning("無法獲取遊戲視窗位置，使用預設位置")
                game_x, game_y = 100, 100
                game_width, game_height = 1295, 759
            else:
                game_x, game_y, game_width, game_height = game_rect
            
            # 創建懸浮視窗
            self.floating_window = tk.Toplevel()
            self.floating_window.title("自動化控制")
            self.floating_window.overrideredirect(True)  # 無邊框
            self.floating_window.attributes('-topmost', True)  # 置頂
            self.floating_window.attributes('-alpha', 0.85)  # 半透明
            self.floating_window.configure(bg=Theme.BACKGROUND_PRIMARY)
            
            # 計算懸浮視窗位置（放在遊戲視窗右上角）
            # 先設置一個初始大小，之後會根據內容自動調整
            initial_width = 220
            initial_height = 160
            floating_x = game_x + game_width - initial_width - 10
            floating_y = game_y + 10
            
            # 確保視窗不會超出螢幕範圍
            screen_width = self.floating_window.winfo_screenwidth()
            screen_height = self.floating_window.winfo_screenheight()
            if floating_x + initial_width > screen_width:
                floating_x = screen_width - initial_width - 10
            if floating_y + initial_height > screen_height:
                floating_y = screen_height - initial_height - 10
            if floating_x < 0:
                floating_x = 10
            if floating_y < 0:
                floating_y = 10
            
            self.floating_window.geometry(f"{initial_width}x{initial_height}+{floating_x}+{floating_y}")
            
            # 綁定拖移事件到整個視窗
            self.floating_window.bind('<Button-1>', self._on_floating_window_drag_start)
            self.floating_window.bind('<B1-Motion>', self._on_floating_window_drag)
            self.floating_window.bind('<ButtonRelease-1>', self._on_floating_window_drag_stop)
            
            # 創建內容框架（使用普通Frame確保可見）
            content_frame = tk.Frame(
                self.floating_window,
                bg=Theme.BACKGROUND_PRIMARY,
                highlightbackground=Theme.BORDER_PRIMARY,
                highlightthickness=1
            )
            content_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 綁定拖移事件到內容框架（讓整個區域可拖移）
            content_frame.bind('<Button-1>', self._on_floating_window_drag_start)
            content_frame.bind('<B1-Motion>', self._on_floating_window_drag)
            content_frame.bind('<ButtonRelease-1>', self._on_floating_window_drag_stop)
            
            # 倒數時間標籤（只在啟用定時停止時顯示剩餘時間）
            self.countdown_label = tk.Label(
                content_frame,
                text="00:00:00",
                bg=Theme.BACKGROUND_PRIMARY,
                fg=Theme.TEXT_PRIMARY,
                font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'),
                width=12,
                anchor='center'
            )
            # 初始狀態：根據是否啟用定時停止來決定是否顯示
            if hasattr(self, 'auto_stop_enabled_var') and self.auto_stop_enabled_var.get():
                self.countdown_label.pack(pady=(5, 3))
            else:
                self.countdown_label.pack_forget()  # 隱藏標籤
            
            # 綁定拖移事件到標籤（讓標籤區域也可拖移）
            self.countdown_label.bind('<Button-1>', self._on_floating_window_drag_start)
            self.countdown_label.bind('<B1-Motion>', self._on_floating_window_drag)
            self.countdown_label.bind('<ButtonRelease-1>', self._on_floating_window_drag_stop)
            
            # 下次循環倒數標籤
            cycle_label_title = tk.Label(
                content_frame,
                text="下次循環:",
                bg=Theme.BACKGROUND_PRIMARY,
                fg=Theme.TEXT_SECONDARY,
                font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'normal'),
                anchor='center'
            )
            cycle_label_title.pack(pady=(0, 2))
            
            self.next_cycle_label = tk.Label(
                content_frame,
                text="--:--",
                bg=Theme.BACKGROUND_PRIMARY,
                fg=Theme.TEXT_HIGHLIGHT,
                font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'),
                width=10,
                anchor='center'
            )
            self.next_cycle_label.pack(pady=(0, 5))
            
            # 綁定拖移事件到標籤（讓標籤區域也可拖移）
            self.next_cycle_label.bind('<Button-1>', self._on_floating_window_drag_start)
            self.next_cycle_label.bind('<B1-Motion>', self._on_floating_window_drag)
            self.next_cycle_label.bind('<ButtonRelease-1>', self._on_floating_window_drag_stop)
            
            # 按鈕框架
            button_frame = tk.Frame(content_frame, bg=Theme.BACKGROUND_PRIMARY)
            button_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            # 跳過等待按鈕
            skip_btn = tk.Button(
                button_frame,
                text="跳過",
                command=self.skip_current_wait,
                bg=Theme.BUTTON_SECONDARY,
                fg=Theme.BUTTON_SECONDARY_TEXT,
                activebackground=Theme.BUTTON_SECONDARY_HOVER,
                activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'bold'),
                relief='flat',
                cursor='hand2',
                bd=0,
                highlightthickness=0,
                width=8,
                height=1
            )
            skip_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)
            
            # 結束按鈕
            stop_btn = tk.Button(
                button_frame,
                text="結束",
                command=self.stop_automation,
                bg=Theme.BUTTON_DANGER,
                fg=Theme.BUTTON_DANGER_TEXT,
                activebackground=Theme.BUTTON_DANGER_HOVER,
                activeforeground=Theme.BUTTON_DANGER_TEXT,
                font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'bold'),
                relief='flat',
                cursor='hand2',
                bd=0,
                highlightthickness=0,
                width=8,
                height=1
            )
            stop_btn.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            # 綁定關閉事件
            self.floating_window.protocol("WM_DELETE_WINDOW", self.stop_automation)
            
            # 更新視窗大小以適應內容
            self.floating_window.update_idletasks()
            actual_width = content_frame.winfo_reqwidth() + 20  # 加上邊距
            actual_height = content_frame.winfo_reqheight() + 20  # 加上邊距
            
            # 確保視窗不會超出螢幕範圍
            if floating_x + actual_width > screen_width:
                floating_x = screen_width - actual_width - 10
            if floating_y + actual_height > screen_height:
                floating_y = screen_height - actual_height - 10
            if floating_x < 0:
                floating_x = 10
            if floating_y < 0:
                floating_y = 10
            
            # 設置實際大小
            self.floating_window.geometry(f"{actual_width}x{actual_height}+{floating_x}+{floating_y}")
            
            # 開始更新倒數時間
            self.update_countdown()
            
            self.is_floating = True
            self.logger.info(f"已創建懸浮視窗，位置: ({floating_x}, {floating_y}), 大小: {actual_width}x{actual_height}")
            
        except Exception as e:
            self.logger.error(f"創建懸浮視窗失敗: {str(e)}")
            # 如果失敗，恢復主視窗
            self.root.deiconify()
    
    def _on_floating_window_drag_start(self, event):
        """開始拖移懸浮視窗"""
        if self.floating_window:
            # 檢查是否點擊在按鈕上
            widget = event.widget
            # 如果點擊的是按鈕，不開始拖移
            if isinstance(widget, tk.Button):
                return
            
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.drag_window_x = self.floating_window.winfo_x()
            self.drag_window_y = self.floating_window.winfo_y()
            self.is_dragging = False  # 標記為未開始拖移（需要移動一定距離才開始）
    
    def _on_floating_window_drag(self, event):
        """拖移懸浮視窗"""
        if not self.floating_window:
            return
        
        # 檢查是否點擊在按鈕上
        widget = event.widget
        if isinstance(widget, tk.Button):
            return
        
        # 計算移動距離
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        # 如果移動距離超過5像素，才開始拖移（避免點擊觸發拖移）
        if not self.is_dragging and (abs(dx) > 5 or abs(dy) > 5):
            self.is_dragging = True
        
        if self.is_dragging:
            # 計算新位置
            x = self.drag_window_x + dx
            y = self.drag_window_y + dy
            
            # 確保視窗不會超出螢幕範圍
            screen_width = self.floating_window.winfo_screenwidth()
            screen_height = self.floating_window.winfo_screenheight()
            window_width = self.floating_window.winfo_width()
            window_height = self.floating_window.winfo_height()
            
            # 限制在螢幕範圍內
            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))
            
            # 更新視窗位置
            self.floating_window.geometry(f"+{x}+{y}")
    
    def _on_floating_window_drag_stop(self, event):
        """停止拖移懸浮視窗"""
        self.is_dragging = False
    
    
    def update_countdown(self):
        """更新倒數時間顯示"""
        if not self.is_floating or not self.floating_window:
            return
        
        # 調試：確認方法被調用
        if not hasattr(self, '_update_countdown_called'):
            self._update_countdown_called = 0
        self._update_countdown_called += 1
        if self._update_countdown_called % 10 == 0:  # 每10次記錄一次
            self.logger.debug(f"update_countdown 被調用 {self._update_countdown_called} 次")
        
        try:
            # 更新定時停止倒數（只在啟用定時停止時顯示）
            if self.countdown_label:
                # 檢查是否啟用定時停止
                if hasattr(self, 'auto_stop_enabled_var') and self.auto_stop_enabled_var.get():
                    # 啟用定時停止，顯示剩餘時間
                    if not self.countdown_label.winfo_viewable():
                        self.countdown_label.pack(pady=(5, 3))  # 顯示標籤
                    
                    # 計算剩餘時間
                    if hasattr(self, 'auto_stop_timer') and self.auto_stop_timer and self.start_time:
                        time_str = self.auto_stop_time_var.get() if hasattr(self, 'auto_stop_time_var') else "23:59"
                        try:
                            hour, minute = map(int, time_str.split(':'))
                            now = datetime.now()
                            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            if target_time <= now:
                                target_time = target_time + timedelta(days=1)
                            
                            remaining = target_time - now
                            total_seconds = int(remaining.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            countdown_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        except:
                            countdown_text = "--:--:--"
                    else:
                        countdown_text = "--:--:--"
                    
                    # 只有當文本改變時才更新，避免不必要的重繪
                    old_text = self.countdown_label.cget("text")
                    if old_text != countdown_text:
                        self.countdown_label.config(text=countdown_text)
                        # 強制立即更新標籤和視窗
                        self.countdown_label.update_idletasks()
                        self.floating_window.update_idletasks()
                else:
                    # 沒有啟用定時停止，隱藏標籤
                    if self.countdown_label.winfo_viewable():
                        self.countdown_label.pack_forget()
            
            # 更新下次循環倒數時間
            if self.next_cycle_label:
                try:
                    if hasattr(self.automation_manager, 'current_wait_remaining'):
                        remaining = self.automation_manager.current_wait_remaining
                        # 調試：記錄剩餘時間值
                        if remaining is not None:
                            self.logger.debug(f"循環倒數剩餘時間: {remaining:.1f} 秒")
                        
                        if remaining is not None and remaining > 0:
                            minutes = int(remaining // 60)
                            seconds = int(remaining % 60)
                            cycle_text = f"{minutes:02d}:{seconds:02d}"
                            # 調試：記錄顯示文本
                            self.logger.debug(f"循環倒數顯示: {cycle_text}")
                        else:
                            # 沒有在等待，顯示 "--:--"
                            cycle_text = "--:--"
                    else:
                        cycle_text = "--:--"
                        self.logger.debug("automation_manager 沒有 current_wait_remaining 屬性")
                    
                    # 強制更新標籤
                    old_text = self.next_cycle_label.cget("text")
                    if old_text != cycle_text:  # 只有當文本改變時才更新
                        self.next_cycle_label.config(text=cycle_text)
                        # 強制立即更新標籤和視窗
                        self.next_cycle_label.update_idletasks()
                        self.floating_window.update_idletasks()
                except Exception as e:
                    self.logger.error(f"更新循環倒數失敗: {str(e)}", exc_info=True)
                    cycle_text = "--:--"
                    if self.next_cycle_label:
                        self.next_cycle_label.config(text=cycle_text)
            
            # 每秒更新一次
            if self.is_floating and self.floating_window:
                try:
                    # 取消之前的更新任務（如果存在）
                    if self.countdown_update_job:
                        self.floating_window.after_cancel(self.countdown_update_job)
                    # 安排下一次更新（確保持續更新）
                    self.countdown_update_job = self.floating_window.after(1000, self.update_countdown)
                except Exception as e:
                    self.logger.error(f"安排倒數更新失敗: {str(e)}")
                    # 即使出錯也要繼續更新
                    try:
                        self.countdown_update_job = self.floating_window.after(1000, self.update_countdown)
                    except:
                        pass
        except Exception as e:
            self.logger.error(f"更新倒數時間失敗: {str(e)}")
            # 即使出錯也要繼續更新
            if self.is_floating and self.floating_window:
                try:
                    if self.countdown_update_job:
                        self.floating_window.after_cancel(self.countdown_update_job)
                    self.countdown_update_job = self.floating_window.after(1000, self.update_countdown)
                except:
                    pass
    
    def skip_current_wait(self):
        """跳過當前等待時間"""
        if hasattr(self.automation_manager, 'skip_current_wait'):
            self.automation_manager.skip_current_wait()
            self.logger.info("已請求跳過當前等待時間")
    
    def restore_normal_window(self):
        """恢復正常視窗狀態"""
        if not self.is_floating:
            return
        
        try:
            # 停止倒數更新
            if self.countdown_update_job and self.floating_window:
                self.floating_window.after_cancel(self.countdown_update_job)
                self.countdown_update_job = None
            
            # 關閉懸浮視窗
            if self.floating_window:
                self.floating_window.destroy()
                self.floating_window = None
            
            # 顯示主視窗
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
            self.is_floating = False
            self.countdown_label = None
            self.next_cycle_label = None
            
            # 取消保存定時器（如果存在）
            if self.save_timer:
                try:
                    self.root.after_cancel(self.save_timer)
                except:
                    pass
                self.save_timer = None
            
            self.logger.info("已恢復正常視窗狀態")
            
        except Exception as e:
            self.logger.error(f"恢復正常視窗失敗: {str(e)}")
    
    def show_faq(self):
        """顯示幫助"""
        faq_text = """使用說明：

1. 選擇視窗：從下拉選單選擇遊戲視窗
2. 設定技能：配置祈禱、天使祝福等技能按鍵
3. 設定參數：配置自由市場待機時間等參數
4. 開始自動化：點擊 START 按鈕開始

注意事項：
- 請確保遊戲視窗已啟動
- 使用時請遵守遊戲規則"""
        messagebox.showinfo("使用說明", faq_text)
    
    def start_automation(self):
        """開始自動化"""
        if not self.window_manager.is_valid():
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        selected_title = self.window_var.get()
        if not selected_title or not selected_title.startswith("MapleStory Worlds"):
            messagebox.showerror("錯誤", "只能選擇以 MapleStory Worlds 開頭的視窗")
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
        
        # 重置上次進入自由市場的標誌，確保開始時直接施放技能
        self.last_entered_free_market = False
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
        
        thread = threading.Thread(target=self.automation_loop, daemon=True)
        thread.start()
    
    def stop_automation(self):
        """停止自動化"""
        self.is_running = False
        self.automation_manager.is_running = False
        self.show_overlay = False
        self.cancel_auto_stop()
        self.logger.info("停止自動化流程")
        
        # 更新按鈕狀態（如果不在懸浮視窗模式）
        if not self.is_floating:
            self.stop_btn.config(state="disabled")
            self.start_btn.config(state="normal")
        
        # 取消保存定時器（如果存在）
        if self.save_timer:
            try:
                if self.is_floating and self.floating_window:
                    self.floating_window.after_cancel(self.save_timer)
                else:
                    self.root.after_cancel(self.save_timer)
            except:
                pass
            self.save_timer = None
        
        # 恢復正常視窗（如果使用了懸浮視窗）
        if self.is_floating:
            self.restore_normal_window()
        else:
            # 如果沒有使用懸浮視窗，主視窗應該一直顯示，不需要恢復
            # 但確保主視窗在最前面，方便用戶操作
            self.root.lift()
            self.root.focus_force()
        
        # 最後保存一次配置
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
        self.root.after(0, lambda: messagebox.showinfo("定時停止", f"已到達指定時間 ({current_time})，程式已自動停止"))
        self.root.after(0, self.stop_automation)
    
    def on_hp_bar_detection_failed(self):
        """血條檢測失敗回調"""
        self.logger.error("血條檢測失敗，終止程式")
        
        # 如果主視窗被隱藏（懸浮視窗模式），使用懸浮視窗來顯示消息和停止
        if self.is_floating and self.floating_window:
            self.floating_window.after(0, lambda: messagebox.showerror("錯誤", "無法檢測到血條，程式已終止\n請檢查遊戲視窗是否正確顯示"))
            self.floating_window.after(0, self.stop_automation)
        else:
            self.root.after(0, lambda: messagebox.showerror("錯誤", "無法檢測到血條，程式已終止\n請檢查遊戲視窗是否正確顯示"))
            self.root.after(0, self.stop_automation)
    
    def automation_loop(self):
        """自動化循環 - 可隨時終止"""
        try:
            while self.is_running and self.automation_manager.is_running:
                # 檢查是否需要移動（上次循環進入自由市場）
                if self.last_entered_free_market:
                    self.last_entered_free_market = False
                    
                    # 移動到目標位置（使用配置的目標位置和容差）
                    if self.is_running:
                        target_x = self.automation_manager.exit_target_x
                        result = self.automation_manager.move_to_target_position(target_x)
                        if not result:
                            # 移動失敗（可能是血條檢測失敗）
                            break
                    
                    # 向上按鍵（點擊兩次）
                    if self.is_running:
                        self.automation_manager.send_key_press('up', "向上移動（第一次）")
                        if not self.automation_manager._sleep_with_check(0.5):
                            break
                        self.automation_manager.send_key_press('up', "向上移動（第二次）")
                    
                    # 等待1秒
                    if self.is_running:
                        if not self.automation_manager._sleep_with_check(1.0):
                            break
                    
                    # 防偵測移動
                    if self.is_running and hasattr(self, 'anti_detect_after_fm_var') and self.anti_detect_after_fm_var.get():
                        direction = self.move_direction_var.get() if hasattr(self, 'move_direction_var') else "left"
                        left_time = float(self.left_move_time_var.get()) if hasattr(self, 'left_move_time_var') else 0.1
                        right_time = float(self.right_move_time_var.get()) if hasattr(self, 'right_move_time_var') else 0.1
                        move_time = left_time if direction == "left" else right_time
                        self.automation_manager.execute_anti_detection_movement(direction, move_time)
                
                # 固定來回移動（在施放技能前）
                if self.is_running and hasattr(self, 'fixed_move_var') and self.fixed_move_var.get():
                    # 決定是否執行移動（不是每一輪都移動）
                    # 使用計數器：每3輪執行一次移動（可以調整）
                    should_move = (self.move_cycle_count % 3 == 0)
                    self.move_cycle_count += 1
                    
                    if should_move:
                        # 決定移動方向（左右交替）
                        if self.last_move_direction == 'left':
                            move_direction = 'right'
                        elif self.last_move_direction == 'right':
                            move_direction = 'left'
                        else:
                            # 第一次移動，從左開始
                            move_direction = 'left'
                        
                        # 執行移動
                        left_time = float(self.left_move_time_var.get()) if hasattr(self, 'left_move_time_var') else 0.1
                        right_time = float(self.right_move_time_var.get()) if hasattr(self, 'right_move_time_var') else 0.1
                        move_time = left_time if move_direction == 'left' else right_time
                        
                        self.logger.info(f"執行固定來回移動：{move_direction} ({move_time}秒)")
                        pyautogui.keyDown(move_direction)
                        if not self.automation_manager._sleep_with_check(move_time):
                            pyautogui.keyUp(move_direction)
                            break
                        pyautogui.keyUp(move_direction)
                        
                        # 更新上一次移動方向
                        self.last_move_direction = move_direction
                        
                        # 移動後等待一小段時間
                        if not self.automation_manager._sleep_with_check(0.1):
                            break
                
                # 執行技能
                if self.is_running:
                    # 祈禱
                    prayer_key = self.prayer_key_var.get() if hasattr(self, 'prayer_key_var') else "f1"
                    self.automation_manager.send_key_press(prayer_key, "祈禱")
                    
                    # 技能間隔
                    interval = float(self.blessing_interval_var.get()) if hasattr(self, 'blessing_interval_var') else 0.5
                    if not self.automation_manager._sleep_with_check(interval):
                        break
                
                # 天使祝福
                if self.is_running:
                    angel_key = self.angel_blessing_var.get() if hasattr(self, 'angel_blessing_var') else "f2"
                    self.automation_manager.send_key_press(angel_key, "天使祝福")
                    
                    if not self.automation_manager._sleep_with_check(interval):
                        break
                
                # 自訂技能1
                if self.is_running and hasattr(self, 'custom_skill1_var') and self.custom_skill1_var.get():
                    skill1_key = self.custom_skill1_key_var.get() if hasattr(self, 'custom_skill1_key_var') else "f3"
                    self.automation_manager.send_key_press(skill1_key, "自訂技能1")
                    
                    if not self.automation_manager._sleep_with_check(interval):
                        break
                
                # 自訂技能2
                if self.is_running and hasattr(self, 'custom_skill2_var') and self.custom_skill2_var.get():
                    skill2_key = self.custom_skill2_key_var.get() if hasattr(self, 'custom_skill2_key_var') else "f4"
                    self.automation_manager.send_key_press(skill2_key, "自訂技能2")
                
                # 進入自由市場（如果啟用）
                if self.is_running and hasattr(self, 'enter_fm_var') and self.enter_fm_var.get():
                    # 先檢查並處理提示視窗
                    if not self.automation_manager.handle_dialog_window(max_retries=3):
                        self.logger.warning("處理提示視窗失敗，重新執行離開自由市場流程")
                        # 如果處理失敗，重新執行一輪離開、放技能、進入的流程
                        # 先離開自由市場
                        if self.last_entered_free_market:
                            self.last_entered_free_market = False
                            target_x = self.automation_manager.exit_target_x
                            self.automation_manager.move_to_target_position(target_x)
                            self.automation_manager.send_key_press('up', "向上移動（第一次）")
                            if not self.automation_manager._sleep_with_check(0.5):
                                break
                            self.automation_manager.send_key_press('up', "向上移動（第二次）")
                            if not self.automation_manager._sleep_with_check(1.0):
                                break
                            # 重新執行技能
                            prayer_key = self.prayer_key_var.get() if hasattr(self, 'prayer_key_var') else "f1"
                            self.automation_manager.send_key_press(prayer_key, "祈禱")
                            interval = float(self.blessing_interval_var.get()) if hasattr(self, 'blessing_interval_var') else 0.5
                            if not self.automation_manager._sleep_with_check(interval):
                                break
                            angel_key = self.angel_blessing_var.get() if hasattr(self, 'angel_blessing_var') else "f2"
                            self.automation_manager.send_key_press(angel_key, "天使祝福")
                            if not self.automation_manager._sleep_with_check(interval):
                                break
                            if hasattr(self, 'custom_skill1_var') and self.custom_skill1_var.get():
                                skill1_key = self.custom_skill1_key_var.get() if hasattr(self, 'custom_skill1_key_var') else "f3"
                                self.automation_manager.send_key_press(skill1_key, "自訂技能1")
                                if not self.automation_manager._sleep_with_check(interval):
                                    break
                            if hasattr(self, 'custom_skill2_var') and self.custom_skill2_var.get():
                                skill2_key = self.custom_skill2_key_var.get() if hasattr(self, 'custom_skill2_key_var') else "f4"
                                self.automation_manager.send_key_press(skill2_key, "自訂技能2")
                    
                    fm_wait = float(self.fm_wait_var.get()) if hasattr(self, 'fm_wait_var') else 230.0
                    fm_check_time = float(self.fm_check_time_var.get()) if hasattr(self, 'fm_check_time_var') else 3.0
                    
                    entered = self.automation_manager.enter_free_market(max_retries=5, check_time=fm_check_time)
                    if not entered:
                        # 如果進入自由市場失敗（可能是因為檢測到確認視窗），重新執行一輪
                        self.logger.warning("進入自由市場失敗，重新執行一輪（離開 -> 施放技能 -> 進入）")
                        # 如果之前在自由市場內，先離開
                        if self.last_entered_free_market:
                            self.last_entered_free_market = False
                            if not self.automation_manager.exit_free_market():
                                self.logger.error("離開自由市場失敗，停止自動化")
                                break
                            # 重新施放技能
                            prayer_key = self.prayer_key_var.get() if hasattr(self, 'prayer_key_var') else "f1"
                            self.automation_manager.send_key_press(prayer_key, "祈禱")
                            interval = float(self.blessing_interval_var.get()) if hasattr(self, 'blessing_interval_var') else 0.5
                            if not self.automation_manager._sleep_with_check(interval):
                                break
                            angel_key = self.angel_blessing_var.get() if hasattr(self, 'angel_blessing_var') else "f2"
                            self.automation_manager.send_key_press(angel_key, "天使祝福")
                            if not self.automation_manager._sleep_with_check(interval):
                                break
                            # 重新嘗試進入自由市場
                            entered = self.automation_manager.enter_free_market(max_retries=5, check_time=fm_check_time)
                            if entered:
                                self.last_entered_free_market = True
                    else:
                        self.last_entered_free_market = True
                
                # 等待間隔（自由市場待機時間 ±20秒）
                if self.is_running:
                    base_interval = float(self.fm_wait_var.get()) if hasattr(self, 'fm_wait_var') else 230.0
                    wait_interval = self.automation_manager.get_skill_interval(base_interval)
                    self.logger.info(f"等待 {wait_interval:.1f} 秒後進行下一輪循環")
                    # 使用 update_countdown=True 來更新懸浮視窗的倒數時間
                    # 在開始等待前，立即觸發一次 GUI 更新，確保倒數能立即顯示
                    if self.is_floating and self.floating_window:
                        # 立即更新一次，然後確保更新循環繼續運行
                        self.floating_window.after(0, self.update_countdown)
                    # 確保更新任務正在運行
                    if not self.countdown_update_job:
                        self.countdown_update_job = self.floating_window.after(1000, self.update_countdown)
                    if not self.automation_manager._sleep_with_check(wait_interval, update_countdown=True):
                        break
                        
        except Exception as e:
            self.logger.error(f"自動化循環錯誤: {str(e)}")
        finally:
            # 確保UI狀態更新
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
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
                'left_move_time_var', 'right_move_time_var', 'move_direction_var'
            ]
            
            boolean_vars = [
                'custom_skill1_var', 'custom_skill2_var',
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
        """保存配置"""
        try:
            # 先載入現有配置，保留 detection 和 automation 區塊
            existing_config = self.config_manager.load()
            
            config_data = {
                "window": self.window_var.get() if hasattr(self, 'window_var') else "",
                "skills": {
                    "prayer_key": self.prayer_key_var.get() if hasattr(self, 'prayer_key_var') else "f1",
                    "blessing_interval": self.blessing_interval_var.get() if hasattr(self, 'blessing_interval_var') else "0.5",
                    "custom_skill1_enabled": self.custom_skill1_var.get() if hasattr(self, 'custom_skill1_var') else False,
                    "custom_skill1_key": self.custom_skill1_key_var.get() if hasattr(self, 'custom_skill1_key_var') else "f3",
                    "angel_blessing": self.angel_blessing_var.get() if hasattr(self, 'angel_blessing_var') else "f2",
                    "custom_skill2_enabled": self.custom_skill2_var.get() if hasattr(self, 'custom_skill2_var') else False,
                    "custom_skill2_key": self.custom_skill2_key_var.get() if hasattr(self, 'custom_skill2_key_var') else "f4",
                },
                "parameters": {
                    "fm_wait": self.fm_wait_var.get() if hasattr(self, 'fm_wait_var') else "230",
                    "target_width": self.target_width_var.get() if hasattr(self, 'target_width_var') else "1295",
                    "target_height": self.target_height_var.get() if hasattr(self, 'target_height_var') else "759",
                    "left_move_time": self.left_move_time_var.get() if hasattr(self, 'left_move_time_var') else "0.1",
                    "right_move_time": self.right_move_time_var.get() if hasattr(self, 'right_move_time_var') else "0.1",
                    "fm_check_time": self.fm_check_time_var.get() if hasattr(self, 'fm_check_time_var') else "3.0",
                    "auto_stop_enabled": self.auto_stop_enabled_var.get() if hasattr(self, 'auto_stop_enabled_var') else False,
                    "auto_stop_time": self.auto_stop_time_var.get() if hasattr(self, 'auto_stop_time_var') else "23:59",
                    "enter_fm": self.enter_fm_var.get() if hasattr(self, 'enter_fm_var') else True,
                    "use_floating_window": self.use_floating_window_var.get() if hasattr(self, 'use_floating_window_var') else True,
                    "move_direction": self.move_direction_var.get() if hasattr(self, 'move_direction_var') else "left",
                    "fixed_move": self.fixed_move_var.get() if hasattr(self, 'fixed_move_var') else False,
                    "anti_detect_after_fm": self.anti_detect_after_fm_var.get() if hasattr(self, 'anti_detect_after_fm_var') else False,
                }
            }
            
            # 保留現有的 detection 和 automation 區塊（如果存在）
            if "detection" in existing_config:
                config_data["detection"] = existing_config["detection"]
            if "automation" in existing_config:
                config_data["automation"] = existing_config["automation"]
            
            self.config_manager.save(config_data)
        except Exception as e:
            self.logger.error(f"保存配置失敗: {str(e)}")
    
    def load_config(self):
        """載入配置"""
        config = self.config_manager.load()
        
        if "window" in config and config["window"]:
            if hasattr(self, 'window_var'):
                self.window_var.set(config["window"])
        
        if "skills" in config:
            skills = config["skills"]
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

