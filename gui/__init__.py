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
        self.auto_stop_timer = None
        self.start_time = None
        
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
        min_threshold = 40
        max_threshold = 43
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
            
            min_threshold = 40
            max_threshold = 43
            
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
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.logger.info("開始自動化流程")
        
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
        self.stop_btn.config(state="disabled")
        self.start_btn.config(state="normal")
    
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
        self.root.after(0, lambda: messagebox.showerror("錯誤", "無法檢測到血條，程式已終止\n請檢查遊戲視窗是否正確顯示"))
        self.root.after(0, self.stop_automation)
    
    def automation_loop(self):
        """自動化循環 - 可隨時終止"""
        try:
            while self.is_running and self.automation_manager.is_running:
                # 檢查是否需要移動（上次循環進入自由市場）
                if self.last_entered_free_market:
                    self.last_entered_free_market = False
                    
                    # 移動到目標位置（固定為 250，容許誤差 ±20）
                    if self.is_running:
                        target_x = 240
                        result = self.automation_manager.move_to_target_position(target_x, tolerance=20)
                        if not result:
                            # 移動失敗（可能是血條檢測失敗）
                            break
                    
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
                "auto_stop_enabled": self.auto_stop_enabled_var.get() if hasattr(self, 'auto_stop_enabled_var') else False,
                "auto_stop_time": self.auto_stop_time_var.get() if hasattr(self, 'auto_stop_time_var') else "23:59",
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
                ("auto_stop_time", "auto_stop_time_var"),
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

