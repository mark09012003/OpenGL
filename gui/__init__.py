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

from gui.components import (
    create_window_section, create_skill_section, create_parameter_section,
    create_action_buttons, create_log_section
)
from gui.styles import configure_styles
from gui.layout import LayoutManager
from gui.theme import Theme
from gui.widgets import ThemedLabel


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
        
        # 懸浮框相關
        self.overlay_window = None
        self.hp_bar_overlay_window = None
        self.show_overlay = False
        self.overlay_update_thread = None
        self.save_timer = None
        
        # 設定pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 建立GUI
        self.create_widgets()
        
        # 載入配置
        self.load_config()
        
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
    
    def update_overlay_position(self):
        """更新懸浮框位置（簡化版）"""
        # 這裡可以實現懸浮框更新邏輯
        pass
    
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
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.logger.info("開始自動化流程")
        
        thread = threading.Thread(target=self.automation_loop, daemon=True)
        thread.start()
    
    def stop_automation(self):
        """停止自動化"""
        self.is_running = False
        self.automation_manager.is_running = False
        self.show_overlay = False
        self.logger.info("停止自動化流程")
        self.stop_btn.config(state="disabled")
        self.start_btn.config(state="normal")
    
    def automation_loop(self):
        """自動化循環 - 可隨時終止"""
        try:
            while self.is_running and self.automation_manager.is_running:
                # 檢查是否需要移動（上次循環進入自由市場）
                if self.last_entered_free_market:
                    self.last_entered_free_market = False
                    
                    # 移動到目標位置
                    if self.is_running:
                        rect = self.window_manager.get_window_rect()
                        if rect:
                            window_width = rect[2] - rect[0]
                            target_x = window_width / 7 + 50
                            self.automation_manager.move_to_target_position(target_x)
                    
                    # 向上按鍵0.3秒
                    if self.is_running:
                        self.automation_manager.send_key_press('up', "向上移動")
                    
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
                    fm_wait = float(self.fm_wait_var.get()) if hasattr(self, 'fm_wait_var') else 230.0
                    fm_check_time = float(self.fm_check_time_var.get()) if hasattr(self, 'fm_check_time_var') else 3.0
                    
                    entered = self.automation_manager.enter_free_market(max_retries=5, check_time=fm_check_time)
                    if entered:
                        self.last_entered_free_market = True
                
                # 等待間隔（自由市場待機時間 ±20秒）
                if self.is_running:
                    base_interval = float(self.fm_wait_var.get()) if hasattr(self, 'fm_wait_var') else 230.0
                    wait_interval = self.automation_manager.get_skill_interval(base_interval)
                    self.logger.info(f"等待 {wait_interval:.1f} 秒後進行下一輪循環")
                    if not self.automation_manager._sleep_with_check(wait_interval):
                        break
                        
        except Exception as e:
            self.logger.error(f"自動化循環錯誤: {str(e)}")
        finally:
            # 確保UI狀態更新
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.logger.info("自動化循環已結束")
    
    def auto_save_config(self):
        """自動保存配置"""
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(1000, self.save_config)
    
    def save_config(self):
        """保存配置"""
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
                "enter_fm": self.enter_fm_var.get() if hasattr(self, 'enter_fm_var') else True,
                "move_direction": self.move_direction_var.get() if hasattr(self, 'move_direction_var') else "left",
                "fixed_move": self.fixed_move_var.get() if hasattr(self, 'fixed_move_var') else False,
                "anti_detect_after_fm": self.anti_detect_after_fm_var.get() if hasattr(self, 'anti_detect_after_fm_var') else False,
            }
        }
        self.config_manager.save(config_data)
    
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
            ]:
                if key in params and hasattr(self, var_name):
                    getattr(self, var_name).set(params[key])
            
            if "enter_fm" in params and hasattr(self, 'enter_fm_var'):
                self.enter_fm_var.set(params["enter_fm"])
            if "move_direction" in params and hasattr(self, 'move_direction_var'):
                self.move_direction_var.set(params["move_direction"])
            if "fixed_move" in params and hasattr(self, 'fixed_move_var'):
                self.fixed_move_var.set(params["fixed_move"])
            if "anti_detect_after_fm" in params and hasattr(self, 'anti_detect_after_fm_var'):
                self.anti_detect_after_fm_var.set(params["anti_detect_after_fm"])
    
    def on_closing(self):
        """視窗關閉事件"""
        self.is_running = False
        self.automation_manager.is_running = False
        self.show_overlay = False
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
        self.save_config()
        self.root.destroy()

