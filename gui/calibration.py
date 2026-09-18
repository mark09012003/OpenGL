"""Calibration and HP-bar overlay controls."""
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import Theme
from gui.widgets import ThemedEntry

class CalibrationMixin:
    def toggle_overlay(self):
        """Toggle the position overlay on Tk's event loop."""
        self.show_overlay = not self.show_overlay
        self.overlay_btn.config(text="隱藏位置" if self.show_overlay else "顯示位置")
        if self.show_overlay:
            self.update_overlay_position()
        else:
            if self.overlay_update_job:
                self.root.after_cancel(self.overlay_update_job)
                self.overlay_update_job = None
            if self.hp_bar_overlay_window:
                self.hp_bar_overlay_window.withdraw()

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
        """Refresh once, then schedule the next frame without another thread."""
        if not self.show_overlay:
            return
        try:
            if self.window_manager.is_valid():
                rect = self.window_manager.get_window_rect()
                if rect:
                    window_x, window_y, _, _ = rect
                    self.detection_manager.detect_hp_bar_position()
                    if not self.hp_bar_overlay_window:
                        self._create_hp_bar_overlay_window()
                    if self.hp_bar_overlay_window:
                        self._update_hp_bar_overlay(self.detection_manager.all_candidates,
                                                    window_x, window_y)
                        if self.detection_manager.all_candidates:
                            self.hp_bar_overlay_window.deiconify()
                            self.hp_bar_overlay_window.lift()
            elif self.hp_bar_overlay_window:
                self.hp_bar_overlay_window.withdraw()
        except Exception:
            self.logger.exception("更新血條位置標記失敗")
        finally:
            if self.show_overlay:
                self.overlay_update_job = self.root.after(300, self.update_overlay_position)

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


            if not all_candidates:
                self.hp_bar_overlay_window.withdraw()
                return

            # 從檢測管理器讀取配置的閾值
            min_threshold = self.detection_manager.hp_bar_min_width
            max_threshold = self.detection_manager.hp_bar_max_width

            # Reuse one canvas to avoid destroying widgets every 300 ms.
            if self.hp_bar_overlay_canvas is None:
                self.hp_bar_overlay_canvas = tk.Canvas(
                    self.hp_bar_overlay_window, bg="black", highlightthickness=0,
                    width=window_width, height=window_height
                )
                self.hp_bar_overlay_canvas.pack()
            canvas = self.hp_bar_overlay_canvas
            canvas.config(width=window_width, height=window_height)
            canvas.delete("all")

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
                arrow_color = Theme.STATUS_SUCCESS if is_valid else Theme.STATUS_WARNING

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
        self.calibration_window.geometry("1040x760")
        try:
            self.calibration_window.attributes("-alpha", 0.97)
        except tk.TclError:
            pass
        self.calibration_window.configure(bg=Theme.BACKGROUND_PRIMARY)
        self.calibration_window.protocol("WM_DELETE_WINDOW", self.toggle_calibration)

        # 創建主容器（垂直布局）
        main_container = tk.Frame(self.calibration_window, bg=Theme.BACKGROUND_PRIMARY)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # 創建標籤頁（Notebook）
        notebook = ttk.Notebook(main_container)
        notebook.pack(side="top", fill="both", expand=True, pady=(0, 5))

        # 創建固定的底部按鈕區域
        bottom_btn_frame = tk.Frame(main_container, bg=Theme.BACKGROUND_SECONDARY, height=50)
        bottom_btn_frame.pack(side="bottom", fill="x", pady=5)
        bottom_btn_frame.pack_propagate(False)  # 保持固定高度

        # 載入當前配置
        config = self.config_manager.load()
        detection_config = config.get("detection", {})
        automation_config = config.get("automation", {})

        # 創建變數字典
        self.calibration_vars = {}

        # ========== 標籤頁1: 血條檢測參數 ==========
        tab1 = tk.Frame(notebook, bg=Theme.BACKGROUND_SECONDARY)
        notebook.add(tab1, text="血條檢測")

        # 創建滾動框架
        tab1_canvas = tk.Canvas(tab1, bg=Theme.BACKGROUND_SECONDARY, highlightthickness=0)
        tab1_scrollbar = ttk.Scrollbar(tab1, orient="vertical", command=tab1_canvas.yview)
        tab1_scrollable = tk.Frame(tab1_canvas, bg=Theme.BACKGROUND_SECONDARY)

        tab1_scrollable.bind("<Configure>", lambda e: tab1_canvas.configure(scrollregion=tab1_canvas.bbox("all")))
        tab1_window = tab1_canvas.create_window((0, 0), window=tab1_scrollable, anchor="nw")
        tab1_canvas.bind("<Configure>", lambda event, canvas=tab1_canvas, item=tab1_window: canvas.itemconfigure(item, width=event.width))
        tab1_canvas.configure(yscrollcommand=tab1_scrollbar.set)

        tab1_canvas.pack(side="left", fill="both", expand=True)
        tab1_scrollbar.pack(side="right", fill="y")

        # 創建兩列容器
        detection_left = tk.Frame(tab1_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        detection_left.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        detection_right = tk.Frame(tab1_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        detection_right.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        def create_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_SECONDARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_SECONDARY, fg=Theme.TEXT_PRIMARY, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(detection_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = ThemedEntry(row, textvariable=var, width=9)
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

        # ========== 標籤頁2: 提示視窗檢測參數 ==========
        tab2 = tk.Frame(notebook, bg=Theme.BACKGROUND_SECONDARY)
        notebook.add(tab2, text="提示視窗檢測")

        # 創建滾動框架
        tab2_canvas = tk.Canvas(tab2, bg=Theme.BACKGROUND_SECONDARY, highlightthickness=0)
        tab2_scrollbar = ttk.Scrollbar(tab2, orient="vertical", command=tab2_canvas.yview)
        tab2_scrollable = tk.Frame(tab2_canvas, bg=Theme.BACKGROUND_SECONDARY)

        tab2_scrollable.bind("<Configure>", lambda e: tab2_canvas.configure(scrollregion=tab2_canvas.bbox("all")))
        tab2_window = tab2_canvas.create_window((0, 0), window=tab2_scrollable, anchor="nw")
        tab2_canvas.bind("<Configure>", lambda event, canvas=tab2_canvas, item=tab2_window: canvas.itemconfigure(item, width=event.width))
        tab2_canvas.configure(yscrollcommand=tab2_scrollbar.set)

        tab2_canvas.pack(side="left", fill="both", expand=True)
        tab2_scrollbar.pack(side="right", fill="y")

        # 創建兩列容器
        dialog_left = tk.Frame(tab2_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        dialog_left.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        dialog_right = tk.Frame(tab2_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        dialog_right.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        def create_dialog_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建對話框參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_SECONDARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_SECONDARY, fg=Theme.TEXT_PRIMARY, width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(detection_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = ThemedEntry(row, textvariable=var, width=9)
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
        test_btn_row = tk.Frame(tab2_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        test_btn_row.pack(fill="x", padx=10, pady=10)
        test_dialog_btn = tk.Button(test_btn_row, text="測試檢測提示視窗", command=self.test_dialog_detection,
                                    bg=Theme.BUTTON_SECONDARY, fg=Theme.BUTTON_SECONDARY_TEXT,
                                    activebackground=Theme.BUTTON_SECONDARY_HOVER, activeforeground=Theme.BUTTON_SECONDARY_TEXT,
                                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'), relief='flat', cursor='hand2')
        test_dialog_btn.pack(pady=3)

        # ========== 標籤頁3: 自動化參數 ==========
        tab3 = tk.Frame(notebook, bg=Theme.BACKGROUND_SECONDARY)
        notebook.add(tab3, text="自動化參數")

        # 創建滾動框架
        tab3_canvas = tk.Canvas(tab3, bg=Theme.BACKGROUND_SECONDARY, highlightthickness=0)
        tab3_scrollbar = ttk.Scrollbar(tab3, orient="vertical", command=tab3_canvas.yview)
        tab3_scrollable = tk.Frame(tab3_canvas, bg=Theme.BACKGROUND_SECONDARY)

        tab3_scrollable.bind("<Configure>", lambda e: tab3_canvas.configure(scrollregion=tab3_canvas.bbox("all")))
        tab3_window = tab3_canvas.create_window((0, 0), window=tab3_scrollable, anchor="nw")
        tab3_canvas.bind("<Configure>", lambda event, canvas=tab3_canvas, item=tab3_window: canvas.itemconfigure(item, width=event.width))
        tab3_canvas.configure(yscrollcommand=tab3_scrollbar.set)

        tab3_canvas.pack(side="left", fill="both", expand=True)
        tab3_scrollbar.pack(side="right", fill="y")

        # 創建兩列容器
        automation_left = tk.Frame(tab3_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        automation_left.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        automation_right = tk.Frame(tab3_scrollable, bg=Theme.BACKGROUND_SECONDARY)
        automation_right.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        def create_automation_param_row(parent, label_text, param_key, default_value, has_button=False, button_cmd=None):
            """創建自動化參數行的輔助函數"""
            row = tk.Frame(parent, bg=Theme.BACKGROUND_SECONDARY)
            row.pack(fill="x", padx=5, pady=2)
            tk.Label(row, text=f"{label_text}:", bg=Theme.BACKGROUND_SECONDARY, fg=Theme.TEXT_PRIMARY, width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(automation_config.get(param_key, default_value)))
            self.calibration_vars[param_key] = var
            entry = ThemedEntry(row, textvariable=var, width=9)
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
        create_automation_param_row(automation_left, "防偵測最大移動", "anti_detect_max_moves", 1)
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

        # 保存按鈕（固定在底部，不在滾動區域內）
        save_btn = tk.Button(bottom_btn_frame, text="保存校準數值", command=self.save_calibration_config,
                            bg=Theme.BUTTON_PRIMARY, fg=Theme.BUTTON_PRIMARY_TEXT,
                            activebackground=Theme.BUTTON_PRIMARY_HOVER, activeforeground=Theme.BUTTON_PRIMARY_TEXT,
                            font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'), relief='flat', cursor='hand2',
                            width=20, height=2)
        save_btn.pack(expand=True, pady=10)

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
                line_id = canvas.create_line(0, hp_bar_y, window_width, hp_bar_y, fill=Theme.STATUS_ERROR, width=4, dash=(5, 5), tags="hp_bar_y_line")
                text_id = canvas.create_text(10, hp_bar_y - 15, text=f"Y={hp_bar_y} (可拖動)", fill=Theme.STATUS_ERROR, font=("Consolas", 10, "bold"), anchor="w", tags="hp_bar_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, hp_bar_y - 5, window_width, hp_bar_y + 5,
                                 outline=Theme.STATUS_ERROR, fill=Theme.STATUS_ERROR, width=2, tags="hp_bar_y_handle")

            if self.show_exit_target_x_line:
                # 繪製退出目標X軸參考線（可拖動）
                exit_target_x = getattr(self.automation_manager, 'exit_target_x', None)
                if exit_target_x is None:
                    config = self.config_manager.load()
                    automation_config = config.get("automation", {})
                    exit_target_x = automation_config.get("exit_target_x", 250)
                line_id = canvas.create_line(exit_target_x, 0, exit_target_x, window_height, fill=Theme.STATUS_SUCCESS, width=4, dash=(5, 5), tags="exit_target_x_line")
                text_id = canvas.create_text(exit_target_x + 5, 10, text=f"X={exit_target_x} (可拖動)", fill=Theme.STATUS_SUCCESS, font=("Consolas", 10, "bold"), anchor="w", tags="exit_target_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(exit_target_x - 5, window_height - 20, exit_target_x + 5, window_height,
                                 outline=Theme.STATUS_SUCCESS, fill=Theme.STATUS_SUCCESS, width=2, tags="exit_target_x_handle")

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
                canvas.create_line(fm_button_x, 0, fm_button_x, window_height, fill=Theme.TEXT_HIGHLIGHT, width=3, dash=(3, 3), tags="fm_button_x_line")
                canvas.create_text(fm_button_x + 5, 10, text=f"按鈕X={fm_button_x} (可拖動)", fill=Theme.TEXT_HIGHLIGHT, font=("Consolas", 9, "bold"), anchor="w", tags="fm_button_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(fm_button_x - 5, window_height - 20, fm_button_x + 5, window_height,
                                 outline=Theme.TEXT_HIGHLIGHT, fill=Theme.TEXT_HIGHLIGHT, width=2, tags="fm_button_x_handle")

            if self.show_fm_button_y_line:
                # 繪製自由市場按鈕Y軸參考線（可拖動）
                canvas.create_line(0, fm_button_y, window_width, fm_button_y, fill=Theme.TEXT_HIGHLIGHT, width=3, dash=(3, 3), tags="fm_button_y_line")
                canvas.create_text(10, fm_button_y - 15, text=f"按鈕Y={fm_button_y} (可拖動)", fill=Theme.TEXT_HIGHLIGHT, font=("Consolas", 9, "bold"), anchor="w", tags="fm_button_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, fm_button_y - 5, window_width, fm_button_y + 5,
                                 outline=Theme.TEXT_HIGHLIGHT, fill=Theme.TEXT_HIGHLIGHT, width=2, tags="fm_button_y_handle")

            if self.show_fm_button_marker:
                # 繪製自由市場按鈕位置標記（可拖動）
                canvas.create_oval(fm_button_x - 8, fm_button_y - 8, fm_button_x + 8, fm_button_y + 8,
                                 outline=Theme.TEXT_HIGHLIGHT, width=3, fill="", tags="fm_button_circle")
                canvas.create_text(fm_button_x + 15, fm_button_y, text=f"({fm_button_x}, {fm_button_y}) (可拖動)",
                                 fill=Theme.TEXT_HIGHLIGHT, font=("Consolas", 10, "bold"), anchor="w", tags="fm_button_text")

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
                canvas.create_line(dialog_close_x, 0, dialog_close_x, window_height, fill=Theme.STATUS_INFO, width=3, dash=(3, 3), tags="dialog_close_x_line")
                canvas.create_text(dialog_close_x + 5, 30, text=f"關閉X={dialog_close_x} (可拖動)", fill=Theme.STATUS_INFO, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_close_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(dialog_close_x - 5, window_height - 20, dialog_close_x + 5, window_height,
                                 outline=Theme.STATUS_INFO, fill=Theme.STATUS_INFO, width=2, tags="dialog_close_x_handle")

            if self.show_dialog_close_y_line:
                # 繪製提示框關閉按鈕Y軸參考線（可拖動）
                canvas.create_line(0, dialog_close_y, window_width, dialog_close_y, fill=Theme.STATUS_INFO, width=3, dash=(3, 3), tags="dialog_close_y_line")
                canvas.create_text(10, dialog_close_y - 15, text=f"關閉Y={dialog_close_y} (可拖動)", fill=Theme.STATUS_INFO, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_close_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, dialog_close_y - 5, window_width, dialog_close_y + 5,
                                 outline=Theme.STATUS_INFO, fill=Theme.STATUS_INFO, width=2, tags="dialog_close_y_handle")

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
                canvas.create_line(dialog_check_x, 0, dialog_check_x, window_height, fill=Theme.STATUS_WARNING, width=3, dash=(3, 3), tags="dialog_check_x_line")
                canvas.create_text(dialog_check_x + 5, 50, text=f"檢測X={dialog_check_x} (可拖動)", fill=Theme.STATUS_WARNING, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_x_text")
                # 添加可拖動區域標記
                canvas.create_oval(dialog_check_x - 5, window_height - 20, dialog_check_x + 5, window_height,
                                 outline=Theme.STATUS_WARNING, fill=Theme.STATUS_WARNING, width=2, tags="dialog_check_x_handle")
                if dialog_check_width > 0:
                    right_x = dialog_check_x + dialog_check_width
                    canvas.create_line(right_x, 0, right_x, window_height, fill=Theme.STATUS_WARNING, width=2, dash=(3, 3), tags="dialog_check_x_right_line")
                    canvas.create_text(right_x + 5, 70, text=f"X+寬={right_x}", fill=Theme.STATUS_WARNING, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_x_right_text")

            if self.show_dialog_check_y_line:
                # 繪製檢測區域Y軸參考線（可拖動，顯示區域的上下邊界）
                canvas.create_line(0, dialog_check_y, window_width, dialog_check_y, fill=Theme.STATUS_WARNING, width=3, dash=(3, 3), tags="dialog_check_y_line")
                canvas.create_text(10, dialog_check_y - 15, text=f"檢測Y={dialog_check_y} (可拖動)", fill=Theme.STATUS_WARNING, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_y_text")
                # 添加可拖動區域標記
                canvas.create_oval(window_width - 20, dialog_check_y - 5, window_width, dialog_check_y + 5,
                                 outline=Theme.STATUS_WARNING, fill=Theme.STATUS_WARNING, width=2, tags="dialog_check_y_handle")
                if dialog_check_height > 0:
                    bottom_y = dialog_check_y + dialog_check_height
                    canvas.create_line(0, bottom_y, window_width, bottom_y, fill=Theme.STATUS_WARNING, width=2, dash=(3, 3), tags="dialog_check_y_bottom_line")
                    canvas.create_text(10, bottom_y + 15, text=f"Y+高={bottom_y}", fill=Theme.STATUS_WARNING, font=("Consolas", 9, "bold"), anchor="w", tags="dialog_check_y_bottom_text")

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
                                         fill=Theme.STATUS_WARNING, font=("Consolas", 10, "bold"), anchor="e")
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
