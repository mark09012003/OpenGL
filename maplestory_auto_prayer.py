import tkinter as tk
from tkinter import ttk, messagebox
import win32gui
import win32con
import win32api
import pyautogui
import threading
import time
import logging
from datetime import datetime
import os
import random
import json
from PIL import ImageGrab, Image
import numpy as np

class MapleStoryAutoPrayer:
    def __init__(self, root):
        self.root = root
        self.root.title("MapleStory 自動化助手")
        self.root.geometry("900x750")
        self.root.configure(bg='#F5F5F5')
        self.root.minsize(900, 650)
        
        # 控制變數
        self.is_running = False
        self.window_handle = None
        self.window_map = {}
        self.last_entered_free_market = False  # 記錄上次是否成功進入自由市場
        
        # 懸浮框相關變數
        self.overlay_window = None
        self.hp_bar_overlay_window = None  # 血條位置懸浮框
        self.show_overlay = False
        self.overlay_update_thread = None
        
        # 配置檔案路徑
        self.config_file = "config.json"
        
        # 設定日誌
        self.setup_logging()
        
        # 建立GUI
        self.create_widgets()
        
        # 載入配置
        self.load_config()
        
        # 設定自動保存（延遲保存，避免頻繁寫入）
        self.save_timer = None
        
        # 設定pyautogui安全模式
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 綁定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_logging(self):
        """設定日誌系統"""
        # 只使用控制台輸出，不寫入檔案，避免檔案無限變大
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Program started, logging system initialized.")
        
    def create_widgets(self):
        # 主容器
        main_container = tk.Frame(self.root, bg='#F5F5F5')
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 頂部區域 - 左右分欄
        top_container = tk.Frame(main_container, bg='#F5F5F5')
        top_container.pack(fill="both", expand=True)
        
        # 左側面板（主要設定）
        left_panel = tk.Frame(top_container, bg='#F5F5F5')
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 右側面板（操作按鈕和警報）
        right_panel = tk.Frame(top_container, bg='#F5F5F5', width=280)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)
        
        # ========== 左側區域 ==========
        self.create_window_section(left_panel)
        self.create_skill_section(left_panel)
        self.create_parameter_section(left_panel)
        
        # ========== 右側區域 ==========
        self.create_action_buttons(right_panel)
        self.create_alarm_section(right_panel)
        
        # ========== 底部日誌區域 ==========
        self.create_log_section(main_container)
        
        # 初始化時刷新視窗列表
        self.refresh_windows()
    
    def create_window_section(self, parent):
        """建立選擇視窗區域"""
        frame = ttk.LabelFrame(parent, text="視窗設定", padding=12)
        frame.pack(fill="x", pady=(0, 8))
        
        # 視窗選擇
        row1 = tk.Frame(frame, bg='#FFFFFF')
        row1.pack(fill="x", pady=(0, 8))
        tk.Label(row1, text="遊戲視窗:", bg='#FFFFFF', 
                 font=("Microsoft JhengHei", 9, "bold"), width=12, anchor="w").pack(side="left", padx=(0, 8))
        
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(row1, textvariable=self.window_var, 
                                        state="readonly", width=30)
        self.window_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.window_combo.bind("<<ComboboxSelected>>", self.on_window_selected)
        
        refresh_btn = ttk.Button(row1, text="刷新", command=self.refresh_windows, width=8)
        refresh_btn.pack(side="right")
        
        # 解析度顯示
        self.resolution_label = tk.Label(frame, text="解析度: 未選擇", 
                                        bg='#FFFFFF', fg="#666666",
                                        font=("Microsoft JhengHei", 9), anchor="w")
        self.resolution_label.pack(fill="x", pady=(0, 5))
    
    def create_skill_section(self, parent):
        """建立技能快捷鍵區域"""
        frame = ttk.LabelFrame(parent, text="技能設定", padding=12)
        frame.pack(fill="x", pady=(0, 8))
        
        # 祈禱技能
        row1 = tk.Frame(frame, bg='#FFFFFF')
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="祈禱:", bg='#FFFFFF', width=12, anchor="w",
                font=("Microsoft JhengHei", 9)).pack(side="left", padx=(0, 8))
        self.prayer_key_var = tk.StringVar(value="f1")
        ttk.Entry(row1, textvariable=self.prayer_key_var, width=12).pack(side="left")
        
        # 天使祝福
        row2 = tk.Frame(frame, bg='#FFFFFF')
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="天使祝福:", bg='#FFFFFF', width=12, anchor="w",
                font=("Microsoft JhengHei", 9)).pack(side="left", padx=(0, 8))
        self.angel_blessing_var = tk.StringVar(value="f2")
        ttk.Entry(row2, textvariable=self.angel_blessing_var, width=12).pack(side="left")
        
        # 自訂技能1
        row3 = tk.Frame(frame, bg='#FFFFFF')
        row3.pack(fill="x", pady=4)
        self.custom_skill1_var = tk.BooleanVar()
        ttk.Checkbutton(row3, text="自訂技能1", variable=self.custom_skill1_var,
                       style='TCheckbutton', command=self.toggle_custom_skill1,
                       width=12).pack(side="left", padx=(0, 8))
        self.custom_skill1_key_var = tk.StringVar(value="f3")
        self.custom_skill1_entry = ttk.Entry(row3, textvariable=self.custom_skill1_key_var, width=12)
        self.custom_skill1_entry.pack_forget()
        
        # 自訂技能2
        row4 = tk.Frame(frame, bg='#FFFFFF')
        row4.pack(fill="x", pady=4)
        self.custom_skill2_var = tk.BooleanVar()
        ttk.Checkbutton(row4, text="自訂技能2", variable=self.custom_skill2_var,
                       style='TCheckbutton', command=self.toggle_custom_skill2,
                       width=12).pack(side="left", padx=(0, 8))
        self.custom_skill2_key_var = tk.StringVar(value="f4")
        self.custom_skill2_entry = ttk.Entry(row4, textvariable=self.custom_skill2_key_var, width=12)
        self.custom_skill2_entry.pack_forget()
        
        # 祝福施放間隔
        row5 = tk.Frame(frame, bg='#FFFFFF')
        row5.pack(fill="x", pady=4)
        tk.Label(row5, text="技能間隔(秒):", bg='#FFFFFF', width=12, anchor="w",
                font=("Microsoft JhengHei", 9)).pack(side="left", padx=(0, 8))
        self.blessing_interval_var = tk.StringVar(value="0.5")
        ttk.Entry(row5, textvariable=self.blessing_interval_var, width=12).pack(side="left")
    
    def create_parameter_section(self, parent):
        """建立參數設定區域"""
        frame = ttk.LabelFrame(parent, text="進階設定", padding=12)
        frame.pack(fill="x", pady=(0, 8))
        
        # 時間設定 - 使用網格布局
        time_grid = tk.Frame(frame, bg='#FFFFFF')
        time_grid.pack(fill="x", pady=4)
        
        tk.Label(time_grid, text="自由市場待機(秒):", bg='#FFFFFF', width=18, anchor="w",
                font=("Microsoft JhengHei", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.fm_wait_var = tk.StringVar(value="230")
        ttk.Entry(time_grid, textvariable=self.fm_wait_var, width=10).grid(row=0, column=1, padx=5, pady=3)
        
        tk.Label(time_grid, text="檢查時間(秒):", bg='#FFFFFF', width=18, anchor="w",
                font=("Microsoft JhengHei", 9)).grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.fm_check_time_var = tk.StringVar(value="3.0")
        ttk.Entry(time_grid, textvariable=self.fm_check_time_var, width=10).grid(row=0, column=3, padx=5, pady=3)
        
        # 視窗解析度
        res_grid = tk.Frame(frame, bg='#FFFFFF')
        res_grid.pack(fill="x", pady=4)
        tk.Label(res_grid, text="視窗解析度:", bg='#FFFFFF', width=18, anchor="w",
                font=("Microsoft JhengHei", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.target_width_var = tk.StringVar(value="1295")
        ttk.Entry(res_grid, textvariable=self.target_width_var, width=8).grid(row=0, column=1, padx=2, pady=3)
        tk.Label(res_grid, text="×", bg='#FFFFFF', font=("Microsoft JhengHei", 9)).grid(row=0, column=2, padx=2)
        self.target_height_var = tk.StringVar(value="759")
        ttk.Entry(res_grid, textvariable=self.target_height_var, width=8).grid(row=0, column=3, padx=2, pady=3)
        
        # 防偵測移動時間
        move_grid = tk.Frame(frame, bg='#FFFFFF')
        move_grid.pack(fill="x", pady=4)
        tk.Label(move_grid, text="左移時間(秒):", bg='#FFFFFF', width=18, anchor="w",
                font=("Microsoft JhengHei", 9)).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.left_move_time_var = tk.StringVar(value="0.1")
        ttk.Entry(move_grid, textvariable=self.left_move_time_var, width=10).grid(row=0, column=1, padx=5, pady=3)
        
        tk.Label(move_grid, text="右移時間(秒):", bg='#FFFFFF', width=18, anchor="w",
                font=("Microsoft JhengHei", 9)).grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.right_move_time_var = tk.StringVar(value="0.1")
        ttk.Entry(move_grid, textvariable=self.right_move_time_var, width=10).grid(row=0, column=3, padx=5, pady=3)
        
        # 選項區域
        options_frame = tk.Frame(frame, bg='#FFFFFF')
        options_frame.pack(fill="x", pady=8)
        
        self.enter_fm_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="進入自由市場", variable=self.enter_fm_var,
                       style='TCheckbutton').pack(anchor="w", pady=2)
        
        self.anti_detect_after_fm_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="離開自由市場後防偵測移動", 
                       variable=self.anti_detect_after_fm_var, style='TCheckbutton').pack(anchor="w", pady=2)
        
        self.fixed_move_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="固定來回移動(不進自由時)", 
                       variable=self.fixed_move_var, style='TCheckbutton').pack(anchor="w", pady=2)
        
        # 防偵測方向
        direction_frame = tk.Frame(options_frame, bg='#FFFFFF')
        direction_frame.pack(fill="x", pady=4)
        tk.Label(direction_frame, text="防偵測方向:", bg='#FFFFFF',
                font=("Microsoft JhengHei", 9)).pack(side="left", padx=(0, 8))
        self.move_direction_var = tk.StringVar(value="left")
        ttk.Radiobutton(direction_frame, text="左", variable=self.move_direction_var, 
                       value="left").pack(side="left", padx=5)
        ttk.Radiobutton(direction_frame, text="右", variable=self.move_direction_var, 
                       value="right").pack(side="left", padx=5)
    
    def create_alarm_section(self, parent):
        """建立警報設定區域"""
        frame = ttk.LabelFrame(parent, text="警報設定", padding=12)
        frame.pack(fill="x")
        
        volume_frame = tk.Frame(frame, bg='#FFFFFF')
        volume_frame.pack(fill="x", pady=4)
        tk.Label(volume_frame, text="音量:", bg='#FFFFFF', 
                font=("Microsoft JhengHei", 9), width=8, anchor="w").pack(side="left", padx=(0, 8))
        self.alarm_volume_var = tk.DoubleVar(value=0.5)
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, 
                                 variable=self.alarm_volume_var, orient="horizontal", length=150)
        volume_scale.pack(side="left", fill="x", expand=True)
        
        btn_frame = tk.Frame(frame, bg='#FFFFFF')
        btn_frame.pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="測試", command=self.test_alarm, width=10).pack(side="left", padx=2, fill="x", expand=True)
        ttk.Button(btn_frame, text="停止", command=self.stop_alarm, width=10).pack(side="left", padx=2, fill="x", expand=True)
    
    def create_action_buttons(self, parent):
        """建立主要操作按鈕"""
        frame = ttk.LabelFrame(parent, text="操作控制", padding=12)
        frame.pack(fill="x", pady=(0, 8))
        
        self.start_btn = tk.Button(frame, text="▶ 開始自動化", 
                                   command=self.start_automation,
                                   bg="#4CAF50", fg="white", 
                                   font=("Microsoft JhengHei", 11, "bold"),
                                   width=20, height=2, relief="flat",
                                   cursor="hand2")
        self.start_btn.pack(pady=8, fill="x")
        
        self.stop_btn = tk.Button(frame, text="■ 停止流程", 
                                  command=self.stop_automation,
                                  bg="#F44336", fg="white", 
                                  font=("Microsoft JhengHei", 11, "bold"),
                                  width=20, height=2, relief="flat", 
                                  state="disabled", cursor="hand2")
        self.stop_btn.pack(pady=(0, 8), fill="x")
        
        # 懸浮框控制
        self.overlay_btn = ttk.Button(frame, text="顯示角色位置", command=self.toggle_overlay)
        self.overlay_btn.pack(pady=4, fill="x")
        
        ttk.Button(frame, text="? 常見問題", command=self.show_faq).pack(pady=4, fill="x")
    
    def create_log_section(self, parent):
        """建立操作日誌區域"""
        log_frame = ttk.LabelFrame(parent, text="操作日誌", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))
        
        self.log_text = tk.Text(log_frame, height=5, 
                               font=("Consolas", 9),
                               bg="#1E1E1E", fg="#D4D4D4",
                               insertbackground="#D4D4D4",
                               wrap=tk.WORD,
                               state="disabled",
                               spacing1=2,
                               spacing2=1,
                               spacing3=1,
                               relief="flat",
                               borderwidth=0)
        self.log_text.pack(fill="both", expand=True)
        
        # 將日誌輸出到文字區域
        self.setup_log_handler()
    
    def setup_log_handler(self):
        """設定日誌處理器，將日誌輸出到文字區域"""
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
        """列舉所有視窗的回調函數"""
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
        
        # 只顯示以 MapleStory Worlds 開頭的視窗
        target_prefix = "MapleStory Worlds"
        for hwnd, title in windows:
            if title.startswith(target_prefix):
                window_titles.append(title)
                self.window_map[title] = hwnd
        
        self.window_combo['values'] = window_titles
        
        # 自動選擇第一個以 MapleStory Worlds 開頭的視窗（如果存在）
        if window_titles:
            selected_title = window_titles[0]
            self.window_var.set(selected_title)
            self.on_window_selected()
        else:
            self.window_var.set("")
            self.resolution_label.config(
                text="當前視窗解析度: 未找到 MapleStory Worlds 視窗", fg="red")
            self.logger.warning("未找到以 MapleStory Worlds 開頭的視窗")
            messagebox.showwarning("警告", "未找到以 MapleStory Worlds 開頭的視窗，請確保遊戲已啟動")
    
    def on_window_selected(self, event=None):
        """當視窗被選擇時觸發"""
        title = self.window_var.get()
        if title:
            # 驗證是否以 MapleStory Worlds 開頭
            if not title.startswith("MapleStory Worlds"):
                messagebox.showerror("錯誤", "只能選擇以 MapleStory Worlds 開頭的視窗")
                # 重置選擇
                maple_windows = [t for t in self.window_map.keys() if t.startswith("MapleStory Worlds")]
                if maple_windows:
                    self.window_var.set(maple_windows[0])
                    self.select_window_by_title(maple_windows[0])
                else:
                    self.window_var.set("")
                return
            self.select_window_by_title(title)
    
    def select_window_by_title(self, title):
        """根據標題選擇視窗"""
        if title in self.window_map:
            self.window_handle = self.window_map[title]
            # 更新解析度顯示
            try:
                rect = win32gui.GetWindowRect(self.window_handle)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                self.resolution_label.config(
                    text=f"當前視窗解析度: {width}×{height}", fg="green")
                self.logger.info(f"已選擇視窗: {title} ({width}×{height})")
            except:
                self.resolution_label.config(text=f"當前視窗解析度: {title}", fg="green")
    
    def toggle_custom_skill1(self):
        """切換自訂技能1的顯示"""
        if self.custom_skill1_var.get():
            self.custom_skill1_entry.pack(side="left", padx=5)
        else:
            self.custom_skill1_entry.pack_forget()
        # 自動保存配置
        self.auto_save_config()
    
    def toggle_custom_skill2(self):
        """切換自訂技能2的顯示"""
        if self.custom_skill2_var.get():
            self.custom_skill2_entry.pack(side="left", padx=5)
        else:
            self.custom_skill2_entry.pack_forget()
        # 自動保存配置
        self.auto_save_config()
    
    def test_alarm(self):
        """測試警報聲"""
        self.logger.info("測試警報聲")
        # 這裡可以加入實際的警報聲播放邏輯
        messagebox.showinfo("測試", "警報聲測試")
    
    def stop_alarm(self):
        """停止警報聲"""
        self.logger.info("停止警報聲")
    
    def test_hp_bar_detection(self):
        """測試血條檢測功能"""
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        try:
            self.logger.info("開始測試血條檢測...")
            # 將視窗帶到前景
            if not self.bring_window_to_front():
                messagebox.showerror("錯誤", "無法將視窗帶到前景")
                return
            
            time.sleep(0.5)  # 等待視窗切換
            
            # 檢測血條位置
            character_pos = self.detect_hp_bar_position()
            
            if character_pos:
                char_x, char_y = character_pos
                messagebox.showinfo("測試結果", 
                    f"✓ 成功檢測到血條！\n\n"
                    f"人物位置（相對於視窗）：\n"
                    f"X座標: {char_x:.0f}\n"
                    f"Y座標: {char_y:.0f}")
                self.logger.info(f"測試完成 - 人物位置: ({char_x:.0f}, {char_y:.0f})")
            else:
                messagebox.showwarning("測試結果", 
                    "✗ 未檢測到血條\n\n"
                    "請確認：\n"
                    "1. 角色在畫面中可見\n"
                    "2. 角色頭頂有紅色血條\n"
                    "3. 視窗大小正確")
                self.logger.warning("測試完成 - 未檢測到血條")
                
        except Exception as e:
            error_msg = f"測試失敗: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("錯誤", error_msg)
    
    def mark_click_position(self):
        """標記滑鼠點擊位置的XY座標"""
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        try:
            # 顯示提示對話框
            result = messagebox.askokcancel(
                "標記點擊位置",
                "請點擊「確定」後，將滑鼠移動到遊戲視窗中要標記的位置，\n"
                "然後按下「空格鍵」來標記該位置的座標。\n\n"
                "提示：標記後座標會顯示在日誌中。"
            )
            
            if not result:
                return
            
            self.logger.info("等待標記點擊位置...")
            self.logger.info("請將滑鼠移動到目標位置，然後按下「空格鍵」")
            
            # 將視窗帶到前景
            if not self.bring_window_to_front():
                messagebox.showerror("錯誤", "無法將視窗帶到前景")
                return
            
            time.sleep(0.5)  # 等待視窗切換
            
            # 在背景執行緒中等待按鍵
            threading.Thread(target=self._wait_for_space_key, daemon=True).start()
            
        except Exception as e:
            error_msg = f"標記位置失敗: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("錯誤", error_msg)
    
    def _wait_for_space_key(self):
        """等待空格鍵按下，然後獲取滑鼠位置"""
        try:
            # 等待空格鍵按下
            while True:
                # 檢查空格鍵是否被按下
                if win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000:
                    # 獲取當前滑鼠位置（螢幕座標）
                    screen_x, screen_y = win32api.GetCursorPos()
                    
                    # 獲取遊戲視窗的位置和大小
                    rect = win32gui.GetWindowRect(self.window_handle)
                    window_left = rect[0]
                    window_top = rect[1]
                    window_width = rect[2] - rect[0]
                    window_height = rect[3] - rect[1]
                    
                    # 計算相對於遊戲視窗的座標
                    relative_x = screen_x - window_left
                    relative_y = screen_y - window_top
                    
                    # 檢查座標是否在視窗範圍內
                    if 0 <= relative_x <= window_width and 0 <= relative_y <= window_height:
                        # 記錄座標
                        self.logger.info(f"✓ 標記位置成功！")
                        self.logger.info(f"  螢幕座標: ({screen_x}, {screen_y})")
                        self.logger.info(f"  視窗座標（相對於視窗）: ({relative_x:.0f}, {relative_y:.0f})")
                        self.logger.info(f"  視窗大小: {window_width}×{window_height}")
                        
                        # 顯示結果對話框
                        self.root.after(0, lambda: messagebox.showinfo(
                            "標記位置成功",
                            f"✓ 已標記位置！\n\n"
                            f"螢幕座標: ({screen_x}, {screen_y})\n"
                            f"視窗座標（相對於視窗）: ({relative_x:.0f}, {relative_y:.0f})\n"
                            f"視窗大小: {window_width}×{window_height}\n\n"
                            f"詳細資訊已記錄在日誌中。"
                        ))
                    else:
                        self.logger.warning(f"標記位置在視窗範圍外: 視窗座標 ({relative_x:.0f}, {relative_y:.0f})")
                        self.root.after(0, lambda: messagebox.showwarning(
                            "警告",
                            f"標記位置在視窗範圍外！\n\n"
                            f"視窗座標: ({relative_x:.0f}, {relative_y:.0f})\n"
                            f"視窗大小: {window_width}×{window_height}"
                        ))
                    
                    # 等待按鍵釋放，避免重複觸發
                    while win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000:
                        time.sleep(0.01)
                    
                    break
                
                time.sleep(0.01)  # 避免CPU占用過高
                
        except Exception as e:
            error_msg = f"等待按鍵失敗: {str(e)}"
            self.logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))
    
    def test_move_to_target(self):
        """測試移動到目標地點功能"""
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        try:
            self.logger.info("開始測試移動到目標地點...")
            # 將視窗帶到前景
            if not self.bring_window_to_front():
                messagebox.showerror("錯誤", "無法將視窗帶到前景")
                return
            
            time.sleep(0.5)  # 等待視窗切換
            
            # 計算目標位置（視窗寬度的1/7 + 50）
            rect = win32gui.GetWindowRect(self.window_handle)
            window_width = rect[2] - rect[0]
            target_x = window_width / 7 + 50
            
            # 先檢測當前位置
            character_pos = self.detect_hp_bar_position()
            if not character_pos:
                messagebox.showwarning("警告", "無法檢測到血條，無法進行移動測試")
                return
            
            current_x, current_y = character_pos
            distance = abs(current_x - target_x)
            
            # 詢問是否繼續
            result = messagebox.askyesno("確認移動", 
                f"當前人物位置: X={current_x:.0f}\n"
                f"目標位置: X={target_x:.0f}\n"
                f"距離: {distance:.0f}像素\n\n"
                f"是否開始移動？")
            
            if not result:
                return
            
            self.logger.info(f"開始測試移動 - 當前位置: {current_x:.0f}, 目標位置: {target_x:.0f}")
            
            # 在單獨的線程中執行移動，避免阻塞GUI
            def move_thread():
                try:
                    # 執行移動（使用較短的超時時間用於測試）
                    success = self.move_to_target_position(target_x, tolerance=10, max_duration=15)
                    
                    # 在主線程中顯示結果
                    self.root.after(0, lambda: self._show_move_result(success))
                except Exception as e:
                    error_msg = f"移動測試失敗: {str(e)}"
                    self.logger.error(error_msg)
                    self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))
            
            # 啟動移動線程
            move_thread_obj = threading.Thread(target=move_thread, daemon=True)
            move_thread_obj.start()
                
        except Exception as e:
            error_msg = f"測試失敗: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("錯誤", error_msg)
    
    def _show_move_result(self, success):
        """顯示移動測試結果"""
        if success:
            messagebox.showinfo("測試結果", "✓ 成功移動到目標位置！")
            self.logger.info("測試完成 - 成功移動到目標位置")
        else:
            messagebox.showwarning("測試結果", 
                "移動測試完成\n\n"
                "可能原因：\n"
                "1. 移動超時\n"
                "2. 無法持續檢測到血條\n"
                "3. 目標位置無法到達")
            self.logger.warning("測試完成 - 移動未成功")
    
    def create_overlay_window(self):
        """創建懸浮框視窗"""
        if self.overlay_window:
            return
        
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.overrideredirect(True)  # 無邊框
        self.overlay_window.attributes('-topmost', True)  # 置頂
        self.overlay_window.attributes('-alpha', 0.8)  # 半透明
        self.overlay_window.configure(bg='red')
        
        # 創建標記（紅色圓圈）
        canvas = tk.Canvas(self.overlay_window, width=30, height=30, bg='red', highlightthickness=0)
        canvas.pack()
        
        # 繪製圓圈標記
        canvas.create_oval(5, 5, 25, 25, outline='yellow', width=3, fill='red')
        canvas.create_text(15, 15, text='●', font=('Arial', 20), fill='yellow')
        
        self.overlay_window.withdraw()  # 初始隱藏
    
    def _analyze_hp_bar_colors(self, img_array, x_start, x_end, y, height):
        """分析血條區域的顏色組成"""
        try:
            # 提取血條區域的像素
            hp_bar_region = img_array[y:y+height, x_start:x_end+1]
            
            # 計算RGB統計信息（不使用平均值）
            r_values = hp_bar_region[:, :, 0].flatten()
            g_values = hp_bar_region[:, :, 1].flatten()
            b_values = hp_bar_region[:, :, 2].flatten()
            
            r_min, r_max, r_median, r_std = np.min(r_values), np.max(r_values), np.median(r_values), np.std(r_values)
            g_min, g_max, g_median, g_std = np.min(g_values), np.max(g_values), np.median(g_values), np.std(g_values)
            b_min, b_max, b_median, b_std = np.min(b_values), np.max(b_values), np.median(b_values), np.std(b_values)
            
            # 計算中位數RGB值（不使用平均值）
            total_median = r_median + g_median + b_median
            r_ratio = r_median / total_median if total_median > 0 else 0
            g_ratio = g_median / total_median if total_median > 0 else 0
            b_ratio = b_median / total_median if total_median > 0 else 0
            
            # 計算R/G和R/B比值（使用中位數）
            r_g_ratio = r_median / g_median if g_median > 0 else 0
            r_b_ratio = r_median / b_median if b_median > 0 else 0
            
            # 輸出顏色分析結果（使用中位數而非平均值）
            self.logger.info(f"血條顏色分析 - R通道: 最小值={r_min:.0f}, 最大值={r_max:.0f}, 中位數={r_median:.1f}, 標準差={r_std:.1f}, 比例={r_ratio:.2%}")
            self.logger.info(f"血條顏色分析 - G通道: 最小值={g_min:.0f}, 最大值={g_max:.0f}, 中位數={g_median:.1f}, 標準差={g_std:.1f}, 比例={g_ratio:.2%}")
            self.logger.info(f"血條顏色分析 - B通道: 最小值={b_min:.0f}, 最大值={b_max:.0f}, 中位數={b_median:.1f}, 標準差={b_std:.1f}, 比例={b_ratio:.2%}")
            self.logger.info(f"血條顏色分析 - 中位數RGB值: ({r_median:.0f}, {g_median:.0f}, {b_median:.0f})")
            self.logger.info(f"血條顏色分析 - R/G比值: {r_g_ratio:.2f}, R/B比值: {r_b_ratio:.2f}")
            
        except Exception as e:
            self.logger.error(f"分析血條顏色失敗: {str(e)}")
    
    def _show_hp_bar_overlay(self, x_start, x_end, y, height):
        """顯示血條位置的懸浮箭頭標記"""
        try:
            if not self.window_handle:
                return
            
            # 獲取遊戲視窗的絕對位置
            rect = win32gui.GetWindowRect(self.window_handle)
            window_x = rect[0]
            window_y = rect[1]
            
            # 計算血條的中心位置（用於放置箭頭）
            hp_bar_center_x = (x_start + x_end) / 2
            hp_bar_center_y = y + height / 2  # 血條的中心Y位置
            
            # 箭頭大小
            arrow_size = 30
            # 箭頭位置：在血條中心上方
            arrow_x = window_x + hp_bar_center_x
            arrow_y = window_y + hp_bar_center_y - arrow_size - 10  # 箭頭在血條中心上方
            
            # 記錄箭頭位置信息（用於調試）
            self.logger.info(f"箭頭位置 - 血條範圍: X({x_start:.0f}-{x_end:.0f}), Y({y:.0f}-{y+height:.0f}), 血條中心(相對於視窗): ({hp_bar_center_x:.0f}, {hp_bar_center_y:.0f}), 箭頭絕對位置: ({arrow_x:.0f}, {arrow_y:.0f})")
            
            # 記錄箭頭位置信息
            self.logger.info(f"箭頭位置 - 血條中心(相對於視窗): ({hp_bar_center_x:.0f}, {hp_bar_center_y:.0f}), 箭頭絕對位置: ({arrow_x:.0f}, {arrow_y:.0f})")
            
            # 創建或更新血條懸浮框
            if not self.hp_bar_overlay_window:
                self.hp_bar_overlay_window = tk.Toplevel(self.root)
                self.hp_bar_overlay_window.overrideredirect(True)  # 無邊框
                self.hp_bar_overlay_window.attributes('-topmost', True)  # 置頂
                self.hp_bar_overlay_window.attributes('-alpha', 0.9)  # 半透明
                self.hp_bar_overlay_window.configure(bg='yellow')
                
                # 創建畫布來繪製箭頭標記
                canvas = tk.Canvas(self.hp_bar_overlay_window, width=arrow_size, height=arrow_size, 
                                 bg='yellow', highlightthickness=0)
                canvas.pack()
                self.hp_bar_canvas = canvas
            
            # 更新血條懸浮框位置（箭頭中心對齊血條中心）
            self.hp_bar_overlay_window.geometry(f"{arrow_size}x{arrow_size}+{int(arrow_x - arrow_size/2)}+{int(arrow_y)}")
            
            # 清空畫布並繪製向下指向的箭頭
            self.hp_bar_canvas.delete("all")
            # 繪製箭頭（向下指向血條）
            center_x = arrow_size / 2
            center_y = arrow_size / 2
            
            # 繪製向下指向的箭頭（箭頭指向畫布底部，即血條位置）
            arrow_points = [
                center_x, 0,  # 箭頭頂點（上方）
                center_x - 10, arrow_size - 5,  # 左下
                center_x - 3, arrow_size - 5,  # 左下內側
                center_x - 3, arrow_size,  # 底部左
                center_x + 3, arrow_size,  # 底部右
                center_x + 3, arrow_size - 5,  # 右下內側
                center_x + 10, arrow_size - 5,  # 右下
            ]
            
            self.hp_bar_canvas.create_polygon(arrow_points, outline='red', width=2, fill='yellow')
            
            self.hp_bar_overlay_window.deiconify()  # 顯示
            
        except Exception as e:
            self.logger.error(f"顯示血條位置標記失敗: {str(e)}")
    
    def update_overlay_position(self):
        """更新懸浮框位置"""
        while self.show_overlay and self.window_handle:
            try:
                if not self.overlay_window:
                    self.create_overlay_window()
                
                # 檢測角色位置
                character_pos = self.detect_hp_bar_position()
                
                if character_pos:
                    char_x, char_y = character_pos
                    
                    # 獲取遊戲視窗的絕對位置
                    rect = win32gui.GetWindowRect(self.window_handle)
                    window_x = rect[0]
                    window_y = rect[1]
                    
                    # 計算懸浮框的絕對位置（角色位置上方一點）
                    overlay_x = window_x + char_x - 15  # 居中對齊
                    overlay_y = window_y + char_y - 40  # 在角色上方
                    
                    # 更新懸浮框位置
                    self.overlay_window.geometry(f"30x30+{int(overlay_x)}+{int(overlay_y)}")
                    self.overlay_window.deiconify()  # 顯示
                else:
                    # 如果檢測不到，隱藏懸浮框
                    if self.overlay_window:
                        self.overlay_window.withdraw()
                    if self.hp_bar_overlay_window:
                        self.hp_bar_overlay_window.withdraw()
                
                time.sleep(0.3)  # 每0.3秒更新一次
                
            except Exception as e:
                self.logger.error(f"更新懸浮框位置失敗: {str(e)}")
                time.sleep(1)
        
        # 停止時隱藏懸浮框
        if self.overlay_window:
            self.overlay_window.withdraw()
        if self.hp_bar_overlay_window:
            self.hp_bar_overlay_window.withdraw()
    
    def toggle_overlay(self):
        """切換懸浮框顯示/隱藏"""
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        self.show_overlay = not self.show_overlay
        
        if self.show_overlay:
            self.logger.info("顯示角色位置懸浮框")
            self.overlay_btn.config(text="隱藏角色位置懸浮框")
            
            # 確保視窗帶到前景
            self.bring_window_to_front()
            time.sleep(0.3)
            
            # 創建懸浮框
            self.create_overlay_window()
            
            # 啟動更新線程
            if self.overlay_update_thread is None or not self.overlay_update_thread.is_alive():
                self.overlay_update_thread = threading.Thread(target=self.update_overlay_position, daemon=True)
                self.overlay_update_thread.start()
        else:
            self.logger.info("隱藏角色位置懸浮框")
            self.overlay_btn.config(text="顯示角色位置懸浮框")
            
            # 隱藏懸浮框
            if self.overlay_window:
                self.overlay_window.withdraw()
            if self.hp_bar_overlay_window:
                self.hp_bar_overlay_window.withdraw()
    
    def show_faq(self):
        """顯示常見問題"""
        faq_text = """
常見問題：

1. 如何選擇遊戲視窗？
   - 點擊「重新整理視窗」按鈕
   - 從下拉選單中選擇遊戲視窗

2. 如何設定視窗大小？
   - 在「目標視窗解析度」中輸入寬度和高度
   - 選擇視窗後會自動調整大小

3. 如何開始自動化？
   - 選擇視窗並設定參數
   - 點擊「開始自動化流程」按鈕

4. 如何停止自動化？
   - 點擊「停止流程」按鈕

5. 如何測試血條檢測？
   - 點擊「測試血條檢測」按鈕
   - 確保角色在畫面中可見

6. 如何測試移動功能？
   - 點擊「測試移動到目標」按鈕
   - 確認後會自動移動到目標位置
        """
        messagebox.showinfo("常見問題", faq_text)
    
    def bring_window_to_front(self):
        """將視窗帶到前景"""
        if not self.window_handle:
            return False
        
        try:
            if not win32gui.IsWindow(self.window_handle):
                return False
            
            if win32gui.IsIconic(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            
            win32gui.SetForegroundWindow(self.window_handle)
            win32gui.BringWindowToTop(self.window_handle)
            
            return True
        except Exception as e:
            self.logger.error(f"帶到前景失敗: {str(e)}")
            return False
    
    def resize_window(self):
        """重新設定視窗大小"""
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        try:
            width = int(self.target_width_var.get())
            height = int(self.target_height_var.get())
            
            if width <= 0 or height <= 0:
                messagebox.showerror("錯誤", "寬度和高度必須大於0")
                return
            
            rect = win32gui.GetWindowRect(self.window_handle)
            x, y = rect[0], rect[1]
            
            win32gui.SetWindowPos(
                self.window_handle,
                win32con.HWND_TOP,
                x, y,
                width, height,
                win32con.SWP_SHOWWINDOW
            )
            
            self.resolution_label.config(text=f"當前視窗解析度: {width}×{height}", fg="green")
            self.logger.info(f"視窗大小已設定為 {width}×{height}")
            messagebox.showinfo("成功", f"視窗大小已設定為 {width}×{height}")
            
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的數字")
        except Exception as e:
            messagebox.showerror("錯誤", f"設定視窗大小失敗: {str(e)}")
    
    def send_key_press(self, key, skill_name=""):
        """發送按鍵（按壓0.3秒後放開）"""
        if not self.window_handle:
            return False
        
        try:
            if not self.bring_window_to_front():
                return False
            
            time.sleep(0.2)
            
            if not key:
                return False
            
            # 按壓按鍵0.3秒後放開
            pyautogui.keyDown(key)
            time.sleep(0.3)
            pyautogui.keyUp(key)
            
            if skill_name:
                self.logger.info(f"已執行{skill_name}")
            
            return True
        except Exception as e:
            self.logger.error(f"發送按鍵失敗: {str(e)}")
            return False
    
    def send_prayer_key(self):
        """發送祈禱按鍵"""
        key = self.prayer_key_var.get().strip().lower()
        return self.send_key_press(key, "祈禱")
    
    def send_angel_blessing(self):
        """發送天使祝福按鍵"""
        key = self.angel_blessing_var.get().strip().lower()
        return self.send_key_press(key, "天使祝福")
    
    def send_custom_skill1(self):
        """發送自訂技能1按鍵"""
        key = self.custom_skill1_key_var.get().strip().lower()
        return self.send_key_press(key, "自訂技能1")
    
    def send_custom_skill2(self):
        """發送自訂技能2按鍵"""
        key = self.custom_skill2_key_var.get().strip().lower()
        return self.send_key_press(key, "自訂技能2")
    
    def detect_hp_bar_position(self):
        """檢測角色頭頂上方的紅色血條位置，用於判斷人物位置（相對於視窗）"""
        if not self.window_handle:
            return None
        
        try:
            # 獲取視窗位置和大小
            rect = win32gui.GetWindowRect(self.window_handle)
            window_x = rect[0]
            window_y = rect[1]
            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]
            
            # 截圖整個視窗
            screenshot = ImageGrab.grab(bbox=(
                int(window_x), 
                int(window_y), 
                int(window_x + window_width), 
                int(window_y + window_height)
            ))
            
            # 轉換為RGB數組
            img_array = np.array(screenshot)
            
            # 定義紅色血條的顏色範圍（使用區間和占比）
            # 不使用平均值，而是使用顏色區間和範圍內占比來判斷
            r_channel = img_array[:, :, 0]
            g_channel = img_array[:, :, 1]
            b_channel = img_array[:, :, 2]
            
            # 定義紅色區間：血條應該是鮮紅色，不是深紅棕色
            # 血條特徵：R通道高（150-255），G和B通道低（<100），且R明顯大於G和B
            # 排除深紅棕色（G和B較高的情況）
            red_mask = (r_channel >= 150) & (r_channel <= 255) & \
                      (g_channel < 100) & (b_channel < 100) & \
                      (r_channel > g_channel * 1.5) & (r_channel > b_channel * 1.5)
            
            # 只在 y=445 這一行檢查血條
            target_y = 445
            
            # 檢查 y=445 是否在視窗範圍內
            if target_y < 0 or target_y >= window_height:
                self.logger.warning(f"目標Y座標 {target_y} 超出視窗範圍 (0-{window_height-1})")
                return None
            
            # 只在 y=445 這一行檢查紅色像素
            row_red_pixels = np.where(red_mask[target_y, :])[0]
            
            if len(row_red_pixels) == 0:
                self.logger.warning(f"在 y={target_y} 未檢測到紅色像素")
                return None
            
            # 只判斷連續出現的紅色，不判斷大小
            # 找出 y=445 這一行中所有連續的紅色像素區間
            y = target_y
            candidates = []
            
            if len(row_red_pixels) > 0:
                start_x = row_red_pixels[0]
                end_x = row_red_pixels[0]
                
                for i in range(1, len(row_red_pixels)):
                    if row_red_pixels[i] - end_x <= 2:  # 允許2像素間隔
                        end_x = row_red_pixels[i]
                    else:
                        # 找到一個連續的紅色區間，記錄它
                        width = end_x - start_x + 1
                        candidates.append({
                            'y': y,
                            'x_start': start_x,
                            'x_end': end_x,
                            'width': width
                        })
                        start_x = row_red_pixels[i]
                        end_x = row_red_pixels[i]
                
                # 處理最後一個區間
                width = end_x - start_x + 1
                candidates.append({
                    'y': y,
                    'x_start': start_x,
                    'x_end': end_x,
                    'width': width
                })
            
            if not candidates:
                self.logger.warning(f"在 y={target_y} 未找到連續的紅色像素區間")
                return None
            
            # 選擇最長的連續紅色區間（最可能是血條）
            best_candidate = None
            best_width = 0
            
            for candidate in candidates:
                width = candidate['width']
                if width > best_width:
                    best_width = width
                    best_candidate = candidate
            
            if best_candidate is None:
                self.logger.warning("未找到連續的紅色像素區間")
                return None
            
            # 計算血條的中心位置（相對於視窗）
            rect_center_x = (best_candidate['x_start'] + best_candidate['x_end']) / 2
            rect_center_y = best_candidate['y']
            rect_width = best_candidate['width']
            rect_height = 1  # 只檢查一行，高度為1
            
            # 角色位置判斷為連續紅色出現的最左邊
            character_x = best_candidate['x_start']  # 人物水平位置為連續紅色區間的最左邊
            character_y = rect_center_y + rect_height + 15  # 人物位置在血條下方約15像素
            
            # 分析血條區域的顏色組成
            self._analyze_hp_bar_colors(img_array, best_candidate['x_start'], best_candidate['x_end'], 
                                       best_candidate['y'], rect_height)
            
            # 標示血條位置（如果啟用了懸浮框）
            if self.show_overlay:
                self._show_hp_bar_overlay(best_candidate['x_start'], best_candidate['x_end'], 
                                         best_candidate['y'], rect_height)
            
            self.logger.info(f"檢測到血條 - 血條位置: ({best_candidate['x_start']:.0f}, {best_candidate['y']:.0f}) 到 ({best_candidate['x_end']:.0f}, {best_candidate['y']+rect_height:.0f}), 血條中心: ({rect_center_x:.0f}, {rect_center_y:.0f}), 血條寬度: {rect_width:.0f}, 人物位置(相對於視窗): ({character_x:.0f}, {character_y:.0f})")
            return (character_x, character_y)  # 返回人物位置（相對於視窗）
            
        except Exception as e:
            self.logger.error(f"檢測紅色血條位置失敗: {str(e)}")
            return None
    
    def check_free_market_entered(self):
        """檢查是否成功進入自由市場（檢查小地圖）"""
        if not self.window_handle:
            return False
        
        try:
            # 檢查小地圖
            rect = win32gui.GetWindowRect(self.window_handle)
            window_x = rect[0]
            window_y = rect[1]
            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]
            
            # 小地圖區域在左上角
            minimap_x = window_x + window_width * 0.02
            minimap_y = window_y + window_height * 0.05
            minimap_width = window_width * 0.15
            minimap_height = window_height * 0.12
            
            # 截圖小地圖區域
            screenshot = ImageGrab.grab(bbox=(
                int(minimap_x), 
                int(minimap_y), 
                int(minimap_x + minimap_width), 
                int(minimap_y + minimap_height)
            ))
            
            # 轉換為RGB數組
            img_array = np.array(screenshot)
            
            # 檢查小地圖下方文字區域
            text_region_height = int(minimap_height * 0.3)
            text_region = img_array[-text_region_height:, :] if text_region_height > 0 else img_array
            
            # 檢查文字區域的對比度
            gray_values = np.mean(text_region, axis=2)
            avg_brightness = np.mean(gray_values)
            brightness_std = np.std(gray_values)
            high_contrast_pixels = np.sum((gray_values > 200) | (gray_values < 50))
            total_pixels = text_region.shape[0] * text_region.shape[1]
            contrast_ratio = high_contrast_pixels / total_pixels if total_pixels > 0 else 0
            
            self.logger.info(f"小地圖檢測 - 平均亮度: {avg_brightness:.1f}, 亮度標準差: {brightness_std:.1f}, 對比度比例: {contrast_ratio:.2f}")
            
            # 判斷條件
            if contrast_ratio > 0.08 or (avg_brightness > 150 and brightness_std > 30):
                self.logger.info("檢測到可能已進入自由市場（基於小地圖特徵）")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"檢查自由市場狀態失敗: {str(e)}")
            return False
    
    def click_free_market_button(self):
        """點擊自由市場按鈕"""
        if not self.window_handle:
            return False
        
        try:
            if not self.bring_window_to_front():
                return False
            
            time.sleep(0.2)
            
            # 獲取視窗位置
            rect = win32gui.GetWindowRect(self.window_handle)
            window_x = rect[0]
            window_y = rect[1]
            
            # 自由市場按鈕位置（X和Y軸都固定，相對於視窗左上角的固定像素距離）
            button_x_offset = 980  # 固定X軸偏移量（可根據實際情況調整）
            button_y_offset = 720  # 固定Y軸偏移量（可根據實際情況調整）
            button_x = window_x + button_x_offset
            button_y = window_y + button_y_offset
            
            # 點擊按鈕（點擊兩次）
            self.logger.info(f"準備點擊自由市場按鈕 (視窗位置: {window_x}, {window_y}, 按鈕位置: {button_x:.0f}, {button_y:.0f})")
            pyautogui.click(button_x, button_y)
            time.sleep(0.1)  # 兩次點擊之間稍作延遲
            pyautogui.click(button_x, button_y)
            self.logger.info(f"已點擊自由市場按鈕（兩次）")
            
            return True
        except Exception as e:
            self.logger.error(f"點擊自由市場按鈕失敗: {str(e)}")
            return False
    
    def move_to_target_position(self, target_x, tolerance=10, max_duration=30):
        """使用方向鍵移動角色直到紅色矩形到達目標X位置
        
        Args:
            target_x: 目標X座標（相對於視窗）
            tolerance: 允許的誤差範圍（像素）
            max_duration: 最大移動時間（秒）
        """
        if not self.window_handle:
            return False
        
        try:
            if not self.bring_window_to_front():
                return False
            
            start_time = time.time()
            current_key = None  # 當前按下的方向鍵
            
            self.logger.info(f"開始移動到目標位置 X={target_x:.0f} (誤差範圍: ±{tolerance}像素)")
            
            # 使用一個標誌來控制移動（測試模式下不受 is_running 限制）
            move_active = True
            
            while move_active and (time.time() - start_time) < max_duration:
                # 檢測當前人物位置
                character_pos = self.detect_hp_bar_position()
                
                if character_pos is None:
                    self.logger.warning("無法檢測到紅色矩形，繼續嘗試...")
                    # 如果正在移動，先放開按鍵
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    time.sleep(0.5)
                    continue
                
                current_x, current_y = character_pos
                
                # 計算距離目標的距離
                distance = abs(current_x - target_x)
                
                # 如果已經到達目標位置（在誤差範圍內）
                if distance <= tolerance:
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                    # 確保所有方向鍵都已釋放
                    pyautogui.keyUp('left')
                    pyautogui.keyUp('right')
                    self.logger.info(f"已到達目標位置 (當前X: {current_x:.0f}, 目標X: {target_x:.0f}, 距離: {distance:.0f})")
                    return True
                
                # 判斷移動方向並按下對應的方向鍵
                if current_x < target_x:
                    # 需要向右移動
                    if current_key != 'right':
                        # 先放開之前的按鍵
                        if current_key:
                            pyautogui.keyUp(current_key)
                        # 按下右方向鍵
                        pyautogui.keyDown('right')
                        current_key = 'right'
                        self.logger.info(f"開始向右移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f}, 距離: {distance:.0f})")
                elif current_x > target_x:
                    # 需要向左移動
                    if current_key != 'left':
                        # 先放開之前的按鍵
                        if current_key:
                            pyautogui.keyUp(current_key)
                        # 按下左方向鍵
                        pyautogui.keyDown('left')
                        current_key = 'left'
                        self.logger.info(f"開始向左移動 (當前X: {current_x:.0f}, 目標X: {target_x:.0f}, 距離: {distance:.0f})")
                else:
                    # 已經在目標位置，放開按鍵
                    if current_key:
                        pyautogui.keyUp(current_key)
                        current_key = None
                
                # 每0.3秒檢測一次位置
                time.sleep(0.3)
            
            # 超時或停止，確保所有按鍵都已釋放
            if current_key:
                pyautogui.keyUp(current_key)
                current_key = None
            # 確保左右方向鍵都已釋放
            pyautogui.keyUp('left')
            pyautogui.keyUp('right')
            
            if (time.time() - start_time) >= max_duration:
                self.logger.warning(f"移動超時（{max_duration}秒），停止移動")
            else:
                self.logger.info("移動已停止")
            
            return False
            
        except Exception as e:
            self.logger.error(f"移動到目標位置失敗: {str(e)}")
            try:
                # 確保放開所有按鍵
                if current_key:
                    pyautogui.keyUp(current_key)
            except:
                pass
            return False
    
    def enter_free_market(self, max_retries=5):
        """進入自由市場，如果失敗則重試"""
        retry_count = 0
        
        while retry_count < max_retries and self.is_running:
            # 點擊自由市場按鈕
            if not self.click_free_market_button():
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.info(f"點擊失敗，3秒後重試 ({retry_count}/{max_retries})")
                    time.sleep(3)
                continue
            
            # 等待進入檢查時間
            try:
                check_time = float(self.fm_check_time_var.get())
            except ValueError:
                check_time = 3.0
            
            self.logger.info(f"等待 {check_time} 秒檢查是否進入自由市場")
            time.sleep(check_time)
            
            # 檢查是否成功進入
            entered = self.check_free_market_entered()
            if entered:
                self.logger.info("成功進入自由市場")
                # 設置標誌，表示下次循環時需要移動到目標位置
                self.last_entered_free_market = True
                return True
            else:
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.warning(f"未成功進入自由市場，3秒後重試 ({retry_count}/{max_retries})")
                    # 如果檢查失敗，可能是按鈕位置錯誤，嘗試不同的按鈕索引
                    # 這裡可以添加邏輯來嘗試不同的按鈕位置
                    time.sleep(3)
                else:
                    self.logger.error(f"進入自由市場失敗，已重試 {max_retries} 次")
                    self.logger.warning("提示：如果按鈕位置不正確，請檢查按鈕位置計算邏輯")
                    return False
        
        return False
    
    def get_skill_interval(self):
        """獲取技能執行間隔（自由市場待機時間 ±20秒）"""
        try:
            base_interval = float(self.fm_wait_var.get())
            # 隨機 ±20秒
            random_offset = random.uniform(-20, 20)
            interval = max(1.0, base_interval + random_offset)  # 確保至少1秒
            return interval
        except ValueError:
            self.logger.error("自由市場待機時間設定錯誤，使用預設值210秒")
            return 210.0
    
    def wait_interval(self, interval):
        """等待指定間隔時間"""
        elapsed = 0
        while elapsed < interval and self.is_running:
            time.sleep(0.1)
            elapsed += 0.1
    
    def automation_loop(self):
        """自動化循環"""
        while self.is_running:
            try:
                # 0. 如果上次成功進入自由市場，移動到目標位置
                if self.last_entered_free_market:
                    self.logger.info("上次成功進入自由市場，開始移動到目標位置")
                    try:
                        # 獲取視窗寬度
                        rect = win32gui.GetWindowRect(self.window_handle)
                        window_width = rect[2] - rect[0]
                        # 固定目標位置：視窗寬度的1/7 + 50
                        target_x = window_width / 7 + 50
                        self.logger.info(f"開始移動到固定目標位置 X={target_x:.0f} (視窗寬度: {window_width}, 位置: 1/7+50)")
                        
                        # 移動到目標位置
                        if self.move_to_target_position(target_x):
                            # 移動到目標位置後，按方向鍵上0.3秒
                            self.logger.info("已到達目標位置，按下方向鍵上0.3秒")
                            pyautogui.keyDown('up')
                            time.sleep(0.3)
                            pyautogui.keyUp('up')
                            
                            # 等待1秒
                            self.logger.info("等待1秒")
                            time.sleep(1.0)
                            
                            # 如果勾選防偵測，隨機執行0~2次長押方向鍵
                            if self.anti_detect_after_fm_var.get():
                                # 隨機決定執行次數（0~2次）
                                move_count = random.randint(0, 2)
                                self.logger.info(f"防偵測移動：隨機執行 {move_count} 次")
                                
                                if move_count > 0:
                                    # 根據防偵測移動初始方向選擇方向鍵
                                    move_direction = self.move_direction_var.get()
                                    
                                    for i in range(move_count):
                                        # 如果執行多次，交替方向
                                        if move_count > 1 and i > 0:
                                            # 交替方向
                                            move_direction = "right" if move_direction == "left" else "left"
                                        
                                        # 根據方向選擇對應的時間
                                        if move_direction == "left":
                                            move_key = 'left'
                                            try:
                                                move_time = float(self.left_move_time_var.get())
                                            except ValueError:
                                                move_time = 0.1
                                        else:  # right
                                            move_key = 'right'
                                            try:
                                                move_time = float(self.right_move_time_var.get())
                                            except ValueError:
                                                move_time = 0.1
                                        
                                        # 長押方向鍵指定秒數
                                        self.logger.info(f"執行防偵測移動 ({i+1}/{move_count})：長押方向鍵{move_key} {move_time}秒")
                                        pyautogui.keyDown(move_key)
                                        time.sleep(move_time)
                                        pyautogui.keyUp(move_key)
                                        self.logger.info(f"防偵測移動 ({i+1}/{move_count}) 完成，已釋放方向鍵{move_key}")
                                        
                                        # 如果還有下一次，稍作延遲
                                        if i < move_count - 1:
                                            time.sleep(0.1)
                                else:
                                    self.logger.info("防偵測移動：隨機結果為0次，跳過移動")
                        else:
                            self.logger.warning("移動到目標位置失敗，繼續執行技能")
                    except Exception as e:
                        self.logger.error(f"移動到目標位置時發生錯誤: {str(e)}")
                    
                    # 重置標誌
                    self.last_entered_free_market = False
                    
                    if not self.is_running:
                        break
                
                # 1. 執行祈禱
                self.send_prayer_key()
                
                if not self.is_running:
                    break
                
                # 2. 如果有設定天使祝福，執行天使祝福
                angel_key = self.angel_blessing_var.get().strip().lower()
                if angel_key:
                    self.send_angel_blessing()
                    
                    if not self.is_running:
                        break
                
                # 3. 如果啟用自訂技能1，執行自訂技能1
                if self.custom_skill1_var.get():
                    self.send_custom_skill1()
                    
                    if not self.is_running:
                        break
                
                # 4. 如果啟用自訂技能2，執行自訂技能2
                if self.custom_skill2_var.get():
                    self.send_custom_skill2()
                    
                    if not self.is_running:
                        break
                
                # 5. 如果勾選「進入自由」，進入自由市場
                if self.enter_fm_var.get():
                    self.logger.info("準備進入自由市場")
                    self.enter_free_market()
                    
                    if not self.is_running:
                        break
                
                # 6. 所有技能執行完後，等待間隔（自由市場待機時間 ±20秒）
                interval = self.get_skill_interval()
                self.logger.info(f"所有技能執行完成，等待 {interval:.1f} 秒後重新開始循環")
                self.wait_interval(interval)
                    
            except ValueError as e:
                self.logger.error(f"設定值錯誤: {str(e)}")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"自動化錯誤: {str(e)}")
                time.sleep(5)
        
        self.logger.info("自動化已停止")
        self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
        self.root.after(0, lambda: self.start_btn.config(state="normal"))
    
    def start_automation(self):
        """開始自動化"""
        # 如果還沒選擇視窗，嘗試從下拉選單選擇
        if not self.window_handle:
            selected_title = self.window_var.get()
            if selected_title:
                self.select_window_by_title(selected_title)
        
        if not self.window_handle:
            messagebox.showwarning("警告", "請先選擇視窗")
            return
        
        # 驗證視窗是否以 MapleStory Worlds 開頭
        selected_title = self.window_var.get()
        if not selected_title or not selected_title.startswith("MapleStory Worlds"):
            messagebox.showerror("錯誤", "只能選擇以 MapleStory Worlds 開頭的視窗")
            return
        
        # 強制 focus 到視窗
        if self.bring_window_to_front():
            self.logger.info(f"已將 {selected_title} 視窗帶到前景")
        
        # 調整視窗大小到目標解析度
        try:
            target_width = int(self.target_width_var.get())
            target_height = int(self.target_height_var.get())
            if target_width > 0 and target_height > 0:
                rect = win32gui.GetWindowRect(self.window_handle)
                x, y = rect[0], rect[1]
                
                win32gui.SetWindowPos(
                    self.window_handle,
                    win32con.HWND_TOP,
                    x, y,
                    target_width, target_height,
                    win32con.SWP_SHOWWINDOW
                )
                self.logger.info(f"已調整視窗大小為 {target_width}×{target_height}")
                self.resolution_label.config(
                    text=f"當前視窗解析度: {target_width}×{target_height}", fg="green")
                time.sleep(0.3)  # 等待視窗調整完成
        except Exception as e:
            self.logger.error(f"調整視窗大小失敗: {str(e)}")
        
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.logger.info("開始自動化流程")
        
        thread = threading.Thread(target=self.automation_loop, daemon=True)
        thread.start()
    
    def stop_automation(self):
        """停止自動化"""
        self.is_running = False
        # 關閉懸浮框
        self.show_overlay = False
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
        self.logger.info("停止自動化流程")
    
    def auto_save_config(self):
        """自動保存配置（延遲保存）"""
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        # 延遲1秒後保存，避免頻繁寫入
        self.save_timer = self.root.after(1000, self.save_config)
    
    def save_config(self):
        """保存配置到檔案"""
        try:
            config = {
                "window": self.window_var.get() if hasattr(self, 'window_var') else "",
                "skills": {
                    "prayer_key": self.prayer_key_var.get() if hasattr(self, 'prayer_key_var') else "f1",
                    "blessing_interval": self.blessing_interval_var.get() if hasattr(self, 'blessing_interval_var') else "0.5",
                    "custom_skill1_enabled": self.custom_skill1_var.get() if hasattr(self, 'custom_skill1_var') else False,
                    "custom_skill1_key": self.custom_skill1_key_var.get() if hasattr(self, 'custom_skill1_key_var') else "f2",
                    "angel_blessing": self.angel_blessing_var.get() if hasattr(self, 'angel_blessing_var') else "f2",
                    "custom_skill2_enabled": self.custom_skill2_var.get() if hasattr(self, 'custom_skill2_var') else False,
                    "custom_skill2_key": self.custom_skill2_key_var.get() if hasattr(self, 'custom_skill2_key_var') else "f3",
                },
                "parameters": {
                    "fm_wait": self.fm_wait_var.get() if hasattr(self, 'fm_wait_var') else "230",
                    "portal_wait": self.portal_wait_var.get() if hasattr(self, 'portal_wait_var') else "1.5",
                    "target_width": self.target_width_var.get() if hasattr(self, 'target_width_var') else "1295",
                    "target_height": self.target_height_var.get() if hasattr(self, 'target_height_var') else "759",
                    "left_move_time": self.left_move_time_var.get() if hasattr(self, 'left_move_time_var') else "0.1",
                    "right_move_time": self.right_move_time_var.get() if hasattr(self, 'right_move_time_var') else "0.1",
                    "fm_check_time": self.fm_check_time_var.get() if hasattr(self, 'fm_check_time_var') else "3.0",
                    "debug_image": self.debug_image_var.get() if hasattr(self, 'debug_image_var') else False,
                    "enter_fm": self.enter_fm_var.get() if hasattr(self, 'enter_fm_var') else True,
                    "move_direction": self.move_direction_var.get() if hasattr(self, 'move_direction_var') else "left",
                    "fixed_move": self.fixed_move_var.get() if hasattr(self, 'fixed_move_var') else False,
                    "anti_detect_after_fm": self.anti_detect_after_fm_var.get() if hasattr(self, 'anti_detect_after_fm_var') else False,
                    "timed_stop": self.timed_stop_var.get() if hasattr(self, 'timed_stop_var') else False,
                    "stop_time": self.stop_time_var.get() if hasattr(self, 'stop_time_var') else "13:00",
                },
                "alarm": {
                    "volume": self.alarm_volume_var.get() if hasattr(self, 'alarm_volume_var') else 0.5,
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.logger.info("配置已保存")
        except Exception as e:
            self.logger.error(f"保存配置失敗: {str(e)}")
    
    def load_config(self):
        """從檔案載入配置"""
        try:
            if not os.path.exists(self.config_file):
                self.logger.info("配置檔案不存在，使用預設值")
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 載入視窗設定
            if "window" in config and config["window"]:
                self.window_var.set(config["window"])
            
            # 載入技能設定
            if "skills" in config:
                skills = config["skills"]
                if "prayer_key" in skills:
                    self.prayer_key_var.set(skills["prayer_key"])
                if "blessing_interval" in skills:
                    self.blessing_interval_var.set(skills["blessing_interval"])
                if "custom_skill1_enabled" in skills:
                    self.custom_skill1_var.set(skills["custom_skill1_enabled"])
                if "custom_skill1_key" in skills:
                    self.custom_skill1_key_var.set(skills["custom_skill1_key"])
                if "angel_blessing" in skills:
                    self.angel_blessing_var.set(skills["angel_blessing"])
                if "custom_skill2_enabled" in skills:
                    self.custom_skill2_var.set(skills["custom_skill2_enabled"])
                if "custom_skill2_key" in skills:
                    self.custom_skill2_key_var.set(skills["custom_skill2_key"])
                
                # 更新自訂技能顯示狀態
                if skills.get("custom_skill1_enabled", False):
                    self.toggle_custom_skill1()
                if skills.get("custom_skill2_enabled", False):
                    self.toggle_custom_skill2()
            
            # 載入參數設定
            if "parameters" in config:
                params = config["parameters"]
                if "fm_wait" in params:
                    self.fm_wait_var.set(params["fm_wait"])
                if "portal_wait" in params:
                    self.portal_wait_var.set(params["portal_wait"])
                if "target_width" in params:
                    self.target_width_var.set(params["target_width"])
                if "target_height" in params:
                    self.target_height_var.set(params["target_height"])
                if "left_move_time" in params:
                    self.left_move_time_var.set(params["left_move_time"])
                if "right_move_time" in params:
                    self.right_move_time_var.set(params["right_move_time"])
                if "fm_check_time" in params:
                    self.fm_check_time_var.set(params["fm_check_time"])
                if "debug_image" in params:
                    self.debug_image_var.set(params["debug_image"])
                if "enter_fm" in params:
                    self.enter_fm_var.set(params["enter_fm"])
                if "move_direction" in params:
                    self.move_direction_var.set(params["move_direction"])
                if "fixed_move" in params:
                    self.fixed_move_var.set(params["fixed_move"])
                if "anti_detect_after_fm" in params:
                    self.anti_detect_after_fm_var.set(params["anti_detect_after_fm"])
                if "timed_stop" in params:
                    self.timed_stop_var.set(params["timed_stop"])
                if "stop_time" in params:
                    self.stop_time_var.set(params["stop_time"])
            
            # 載入警報設定
            if "alarm" in config:
                if "volume" in config["alarm"]:
                    self.alarm_volume_var.set(config["alarm"]["volume"])
            
            self.logger.info("配置已載入")
        except Exception as e:
            self.logger.error(f"載入配置失敗: {str(e)}")
    
    def on_closing(self):
        """視窗關閉時保存配置"""
        # 停止自動化
        self.is_running = False
        # 關閉懸浮框
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
        # 保存配置
        self.save_config()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MapleStoryAutoPrayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
