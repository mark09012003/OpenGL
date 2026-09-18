"""Floating control window and countdown behavior."""
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

from gui.theme import Theme

class WindowModesMixin:
    def convert_to_floating_window(self):
        """Open a compact translucent control surface above the game."""
        try:
            game_rect = self.window_manager.get_window_rect() or (100, 100, 1295, 759)
            game_x, game_y, game_width, game_height = game_rect
            self.floating_window = tk.Toplevel(self.root)
            window = self.floating_window
            window.title("Artale Control")
            window.overrideredirect(True)
            window.attributes('-topmost', True)
            try:
                window.attributes('-alpha', 0.90)
            except tk.TclError:
                pass
            window.configure(bg=Theme.BORDER_PRIMARY)
            width, height = 270, 202
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = max(8, min(game_x + game_width - width - 12, screen_width - width - 8))
            y = max(8, min(game_y + 12, screen_height - height - 8))
            window.geometry(f"{width}x{height}+{x}+{y}")

            panel = tk.Frame(window, bg=Theme.BACKGROUND_SECONDARY)
            panel.pack(fill='both', expand=True, padx=1, pady=1)
            header = tk.Frame(panel, bg=Theme.BACKGROUND_TERTIARY, height=38)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text='●  AUTOMATION ACTIVE',
                     bg=Theme.BACKGROUND_TERTIARY, fg=Theme.STATUS_SUCCESS,
                     font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'bold')).pack(
                         side='left', padx=12, pady=9)
            for widget in (header,):
                widget.bind('<Button-1>', self._on_floating_window_drag_start)
                widget.bind('<B1-Motion>', self._on_floating_window_drag)
                widget.bind('<ButtonRelease-1>', self._on_floating_window_drag_stop)

            body = tk.Frame(panel, bg=Theme.BACKGROUND_SECONDARY)
            body.pack(fill='both', expand=True, padx=14, pady=10)
            tk.Label(body, text='NEXT CYCLE', bg=Theme.BACKGROUND_SECONDARY,
                     fg=Theme.TEXT_SECONDARY,
                     font=Theme.get_font_config(Theme.FONT_SIZE_SMALL)).pack(anchor='w')
            self.next_cycle_label = tk.Label(body, text='--:--',
                                             bg=Theme.BACKGROUND_SECONDARY,
                                             fg=Theme.TEXT_HIGHLIGHT,
                                             font=(Theme.FONT_MONO, 23, 'bold'))
            self.next_cycle_label.pack(anchor='w', pady=(0, 3))
            self.countdown_label = tk.Label(body, text='00:00:00',
                                            bg=Theme.BACKGROUND_SECONDARY,
                                            fg=Theme.TEXT_SECONDARY,
                                            font=(Theme.FONT_MONO, 10))
            if self.auto_stop_enabled_var.get():
                self.countdown_label.pack(anchor='w', pady=(0, 5))
            buttons = tk.Frame(body, bg=Theme.BACKGROUND_SECONDARY)
            buttons.pack(fill='x', side='bottom')
            for text, command, bg, fg in (
                ('跳過等待', self.skip_current_wait, Theme.BUTTON_SECONDARY, Theme.BUTTON_SECONDARY_TEXT),
                ('停止', self.stop_automation, Theme.BUTTON_DANGER, Theme.BUTTON_DANGER_TEXT),
            ):
                tk.Button(buttons, text=text, command=command, bg=bg, fg=fg,
                          activebackground=Theme.BUTTON_SECONDARY_HOVER if text == '跳過等待' else Theme.BUTTON_DANGER_HOVER,
                          activeforeground=fg, relief='flat', bd=0, cursor='hand2',
                          font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'bold'),
                          padx=8, pady=5).pack(side='left', fill='x', expand=True,
                                               padx=(0, 5) if text == '跳過等待' else (5, 0))
            window.protocol('WM_DELETE_WINDOW', self.stop_automation)
            self.root.withdraw()
            self.is_floating = True
            self.update_countdown()
            self._create_log_floating_window(game_x, game_y, game_width, game_height)
            self.logger.info("懸浮控制窗已啟用")
        except Exception:
            self.logger.exception("建立懸浮控制窗失敗")
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

    def _create_log_floating_window(self, game_x, game_y, game_width, game_height):
        """創建Log懸浮視窗"""
        try:
            # 計算Log懸浮視窗位置（放在遊戲視窗左側）
            log_width = 400
            log_height = 300
            log_x = game_x - log_width - 10
            log_y = game_y + 10

            # 確保視窗不會超出螢幕範圍
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            if log_x < 0:
                log_x = game_x + game_width + 10  # 如果左側放不下，放在右側
            if log_x + log_width > screen_width:
                log_x = screen_width - log_width - 10
            if log_y + log_height > screen_height:
                log_y = screen_height - log_height - 10
            if log_y < 0:
                log_y = 10

            # 創建Log懸浮視窗
            self.log_floating_window = tk.Toplevel()
            self.log_floating_window.title("執行日誌")
            self.log_floating_window.overrideredirect(True)  # 無邊框
            self.log_floating_window.attributes('-topmost', True)  # 置頂
            self.log_floating_window.attributes('-alpha', 0.90)  # 半透明
            self.log_floating_window.configure(bg=Theme.BACKGROUND_PRIMARY)
            self.log_floating_window.geometry(f"{log_width}x{log_height}+{log_x}+{log_y}")

            # 創建標題欄（可拖移）
            title_frame = tk.Frame(self.log_floating_window, bg=Theme.BACKGROUND_SECONDARY, height=30)
            title_frame.pack(fill="x")
            title_frame.pack_propagate(False)

            title_label = tk.Label(
                title_frame,
                text="EVENT STREAM  /  執行日誌",
                bg=Theme.BACKGROUND_SECONDARY,
                fg=Theme.TEXT_PRIMARY,
                font=Theme.get_font_config(Theme.FONT_SIZE_SMALL, 'bold')
            )
            title_label.pack(side="left", padx=10, pady=5)

            # 綁定拖移事件到標題欄
            title_frame.bind('<Button-1>', self._on_log_window_drag_start)
            title_frame.bind('<B1-Motion>', self._on_log_window_drag)
            title_frame.bind('<ButtonRelease-1>', self._on_log_window_drag_stop)
            title_label.bind('<Button-1>', self._on_log_window_drag_start)
            title_label.bind('<B1-Motion>', self._on_log_window_drag)
            title_label.bind('<ButtonRelease-1>', self._on_log_window_drag_stop)

            # 創建文字顯示區域（使用ScrolledText）
            from tkinter import scrolledtext
            self.log_floating_text = scrolledtext.ScrolledText(
                self.log_floating_window,
                bg=Theme.LOG_BACKGROUND,
                fg=Theme.LOG_TEXT,
                font=(Theme.FONT_MONO, Theme.FONT_SIZE_SMALL),
                wrap=tk.WORD,
                state="disabled",
                padx=5,
                pady=5
            )
            self.log_floating_text.pack(fill="both", expand=True)

            # 綁定關閉事件
            self.log_floating_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 不允許關閉，只能通過停止自動化關閉

            self.logger.info(f"已創建Log懸浮視窗，位置: ({log_x}, {log_y}), 大小: {log_width}x{log_height}")

            # 更新TextHandler的log_floating_text引用
            if hasattr(self, 'text_handler'):
                self.text_handler.log_floating_text = self.log_floating_text

        except Exception as e:
            self.logger.error(f"創建Log懸浮視窗失敗: {str(e)}")

    def _on_log_window_drag_start(self, event):
        """開始拖移Log懸浮視窗"""
        if self.log_floating_window:
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.drag_window_x = self.log_floating_window.winfo_x()
            self.drag_window_y = self.log_floating_window.winfo_y()
            self.is_dragging = False

    def _on_log_window_drag(self, event):
        """拖移Log懸浮視窗"""
        if not self.log_floating_window:
            return

        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y

        if not self.is_dragging and (abs(dx) > 5 or abs(dy) > 5):
            self.is_dragging = True

        if self.is_dragging:
            x = self.drag_window_x + dx
            y = self.drag_window_y + dy

            screen_width = self.log_floating_window.winfo_screenwidth()
            screen_height = self.log_floating_window.winfo_screenheight()
            window_width = self.log_floating_window.winfo_width()
            window_height = self.log_floating_window.winfo_height()

            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))

            self.log_floating_window.geometry(f"+{x}+{y}")

    def _on_log_window_drag_stop(self, event):
        """停止拖移Log懸浮視窗"""
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
            # 先清除TextHandler的log_floating_text引用，避免後續日誌寫入嘗試訪問已銷毀的視窗
            if hasattr(self, 'text_handler') and self.text_handler:
                self.text_handler.log_floating_text = None

            # 停止倒數更新
            if self.countdown_update_job and self.floating_window:
                try:
                    self.floating_window.after_cancel(self.countdown_update_job)
                except:
                    pass
                self.countdown_update_job = None

            # 關閉懸浮視窗（使用 try-except 包裹，避免阻塞）
            if self.floating_window:
                try:
                    self.floating_window.destroy()
                except:
                    pass
                self.floating_window = None
            if self.log_floating_window:
                try:
                    self.log_floating_window.destroy()
                except:
                    pass
                self.log_floating_window = None
                self.log_floating_text = None

            # 更新狀態標誌（在銷毀視窗後立即更新，避免後續操作依賴這些標誌）
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

            # 顯示主視窗（使用 try-except 包裹，避免阻塞）
            try:
                self.root.deiconify()
                self.root.lift()
                # focus_force() 在某些情況下可能會阻塞，使用 after() 延遲執行
                self.root.after(10, lambda: self._try_focus_window())
            except Exception as e:
                self.logger.error(f"顯示主視窗失敗: {str(e)}")

            # 使用 after() 延遲記錄日誌，避免在恢復視窗時觸發日誌寫入
            self.root.after(50, lambda: self.logger.info("已恢復正常視窗狀態"))

        except Exception as e:
            # 使用 after() 延遲記錄錯誤，避免阻塞
            self.root.after(50, lambda: self.logger.error(f"恢復正常視窗失敗: {str(e)}"))

    def _try_focus_window(self):
        """嘗試聚焦視窗（使用 try-except 包裹，避免阻塞）"""
        try:
            self.root.focus_force()
        except:
            # focus_force() 失敗時不影響其他操作，靜默忽略
            pass

    def show_faq(self):
        """顯示幫助"""
        faq_text = """使用說明：

1. 選擇視窗：從下拉選單選擇遊戲視窗
2. 設定技能：配置技能1、技能2、技能3、技能4等技能按鍵
3. 設定參數：配置自由市場待機時間等參數
4. 開始自動化：點擊 START 按鈕開始

注意事項：
- 請確保遊戲視窗已啟動
- 使用時請遵守遊戲規則"""
        messagebox.showinfo("使用說明", faq_text)
