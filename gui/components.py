"""GUI組件模組 - 使用主題系統創建組件"""
import tkinter as tk
from tkinter import ttk
from gui.theme import Theme
from gui.widgets import (
    ThemedFrame, ThemedLabel, ThemedButton, 
    ThemedEntry, ThemedText, ThemedLabelFrame, SectionFrame
)
from gui.layout import GridLayout, FormLayout


def create_window_section(parent, app):
    """建立選擇視窗區域"""
    section = SectionFrame(parent, "視窗設定")
    frame = section.get_frame()
    
    # 視窗選擇行
    row1 = ThemedFrame(frame)
    row1.pack(fill="x", pady=(0, Theme.PADDING_MEDIUM))
    
    ThemedLabel(row1, "遊戲視窗:", size=Theme.FONT_SIZE_NORMAL, weight='bold', width=12, anchor="w").pack(side="left", padx=(0, Theme.PADDING_MEDIUM))
    
    app.window_var = tk.StringVar()
    app.window_combo = ttk.Combobox(row1, textvariable=app.window_var, state="readonly", width=28)
    app.window_combo.pack(side="left", fill="x", expand=True, padx=(0, Theme.PADDING_MEDIUM))
    app.window_combo.bind("<<ComboboxSelected>>", app.on_window_selected)
    
    refresh_btn = ThemedButton(row1, "⟳", command=app.refresh_windows, variant='secondary', width=3)
    refresh_btn.pack(side="right")
    
    # 解析度顯示
    app.resolution_label = ThemedLabel(
        frame, "解析度: 未選擇", 
        size=Theme.FONT_SIZE_NORMAL,
        color=Theme.TEXT_SECONDARY,
        anchor="w"
    )
    app.resolution_label.pack(fill="x", padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)


def create_skill_section(parent, app):
    """建立技能快捷鍵區域"""
    section = SectionFrame(parent, "技能設定")
    frame = section.get_frame()
    
    skill_grid = ThemedFrame(frame)
    skill_grid.pack(fill="x", pady=Theme.PADDING_SMALL)
    
    # 第一行：祈禱和天使祝福
    ThemedLabel(skill_grid, "祈禱:", width=12, anchor="w").grid(row=0, column=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.prayer_key_var = tk.StringVar(value="f1")
    prayer_entry = ThemedEntry(skill_grid, textvariable=app.prayer_key_var, width=12)
    prayer_entry.grid(row=0, column=1, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    ThemedLabel(skill_grid, "天使祝福:", width=12, anchor="w").grid(row=0, column=2, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.angel_blessing_var = tk.StringVar(value="f2")
    angel_entry = ThemedEntry(skill_grid, textvariable=app.angel_blessing_var, width=12)
    angel_entry.grid(row=0, column=3, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    # 第二行：自訂技能
    row2 = ThemedFrame(skill_grid)
    row2.grid(row=1, column=0, columnspan=4, sticky="ew", padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    app.custom_skill1_var = tk.BooleanVar()
    ttk.Checkbutton(row2, text="自訂技能1", variable=app.custom_skill1_var,
                   style='TCheckbutton', command=app.toggle_custom_skill1,
                   width=12).pack(side="left", padx=(0, Theme.PADDING_MEDIUM))
    app.custom_skill1_key_var = tk.StringVar(value="f3")
    app.custom_skill1_entry = ThemedEntry(row2, textvariable=app.custom_skill1_key_var, width=12)
    app.custom_skill1_entry.pack_forget()
    
    app.custom_skill2_var = tk.BooleanVar()
    ttk.Checkbutton(row2, text="自訂技能2", variable=app.custom_skill2_var,
                   style='TCheckbutton', command=app.toggle_custom_skill2,
                   width=12).pack(side="left", padx=(0, Theme.PADDING_MEDIUM))
    app.custom_skill2_key_var = tk.StringVar(value="f4")
    app.custom_skill2_entry = ThemedEntry(row2, textvariable=app.custom_skill2_key_var, width=12)
    app.custom_skill2_entry.pack_forget()
    
    # 第三行：技能間隔
    ThemedLabel(skill_grid, "技能間隔(秒):", width=12, anchor="w").grid(row=2, column=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.blessing_interval_var = tk.StringVar(value="0.5")
    interval_entry = ThemedEntry(skill_grid, textvariable=app.blessing_interval_var, width=12)
    interval_entry.grid(row=2, column=1, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)


def create_parameter_section(parent, app):
    """建立參數設定區域"""
    section = SectionFrame(parent, "進階設定")
    frame = section.get_frame()
    
    param_grid = ThemedFrame(frame)
    param_grid.pack(fill="x", pady=Theme.PADDING_SMALL)
    
    # 第一行：自由市場待機和檢查時間
    ThemedLabel(param_grid, "自由市場待機(秒):", width=18, anchor="w").grid(row=0, column=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.fm_wait_var = tk.StringVar(value="230")
    ThemedEntry(param_grid, textvariable=app.fm_wait_var, width=10).grid(row=0, column=1, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    ThemedLabel(param_grid, "檢查時間(秒):", width=18, anchor="w").grid(row=0, column=2, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.fm_check_time_var = tk.StringVar(value="3.0")
    ThemedEntry(param_grid, textvariable=app.fm_check_time_var, width=10).grid(row=0, column=3, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    # 第二行：定時停止
    app.auto_stop_enabled_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(param_grid, text="定時停止", variable=app.auto_stop_enabled_var,
                   style='TCheckbutton', command=lambda: app.toggle_auto_stop_entry()).grid(
                   row=1, column=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    
    ThemedLabel(param_grid, "停止時間:", width=12, anchor="w").grid(row=1, column=1, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.auto_stop_time_var = tk.StringVar(value="23:59")
    app.auto_stop_time_entry = ThemedEntry(param_grid, textvariable=app.auto_stop_time_var, width=10, state="disabled")
    app.auto_stop_time_entry.grid(row=1, column=2, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    ThemedLabel(param_grid, "(時:分)", width=8, anchor="w", color=Theme.TEXT_SECONDARY).grid(row=1, column=3, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    
    # 第三行：防偵測移動時間（視窗解析度已固定為1295x759，不再顯示在UI）
    # 固定解析度：1295 x 759
    app.target_width_var = tk.StringVar(value="1295")
    app.target_height_var = tk.StringVar(value="759")
    
    ThemedLabel(param_grid, "左移時間(秒):", width=18, anchor="w").grid(row=2, column=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.left_move_time_var = tk.StringVar(value="0.1")
    ThemedEntry(param_grid, textvariable=app.left_move_time_var, width=10).grid(row=2, column=1, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    ThemedLabel(param_grid, "右移時間(秒):", width=18, anchor="w").grid(row=2, column=2, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL, sticky="w")
    app.right_move_time_var = tk.StringVar(value="0.1")
    ThemedEntry(param_grid, textvariable=app.right_move_time_var, width=10).grid(row=2, column=3, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL)
    
    # 選項區域
    options_frame = ThemedFrame(frame)
    options_frame.pack(fill="x", pady=Theme.PADDING_NORMAL)
    
    left_options = ThemedFrame(options_frame)
    left_options.pack(side="left", fill="x", expand=True, padx=(0, Theme.PADDING_MEDIUM))
    
    right_options = ThemedFrame(options_frame)
    right_options.pack(side="left", fill="x", expand=True, padx=(Theme.PADDING_MEDIUM, 0))
    
    app.enter_fm_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(left_options, text="進入自由市場", variable=app.enter_fm_var,
                   style='TCheckbutton').pack(anchor="w", pady=Theme.PADDING_SMALL)
    
    app.use_floating_window_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(left_options, text="使用懸浮視窗", variable=app.use_floating_window_var,
                   style='TCheckbutton').pack(anchor="w", pady=Theme.PADDING_SMALL)
    
    app.anti_detect_after_fm_var = tk.BooleanVar()
    ttk.Checkbutton(left_options, text="離開自由市場後防偵測", 
                   variable=app.anti_detect_after_fm_var, style='TCheckbutton').pack(anchor="w", pady=Theme.PADDING_SMALL)
    
    app.fixed_move_var = tk.BooleanVar()
    ttk.Checkbutton(right_options, text="固定來回移動", 
                   variable=app.fixed_move_var, style='TCheckbutton').pack(anchor="w", pady=Theme.PADDING_SMALL)
    
    # 防偵測方向
    direction_frame = ThemedFrame(right_options)
    direction_frame.pack(fill="x", pady=Theme.PADDING_SMALL)
    ThemedLabel(direction_frame, "防偵測方向:").pack(side="left", padx=(0, Theme.PADDING_MEDIUM))
    app.move_direction_var = tk.StringVar(value="left")
    ttk.Radiobutton(direction_frame, text="左", variable=app.move_direction_var, 
                   value="left").pack(side="left", padx=Theme.PADDING_NORMAL)
    ttk.Radiobutton(direction_frame, text="右", variable=app.move_direction_var, 
                   value="right").pack(side="left", padx=Theme.PADDING_NORMAL)


def create_action_buttons(parent, app):
    """建立主要操作按鈕"""
    section = SectionFrame(parent, "操作控制")
    frame = section.get_frame()
    
    app.start_btn = ThemedButton(frame, "▶ START", command=app.start_automation, 
                                 variant='primary', width=18, height=2)
    app.start_btn.pack(pady=Theme.PADDING_NORMAL, fill="x")
    
    app.stop_btn = ThemedButton(frame, "■ STOP", command=app.stop_automation, 
                                variant='danger', width=18, height=2, state="disabled")
    app.stop_btn.pack(pady=(0, Theme.PADDING_NORMAL), fill="x")
    
    # 測試自由市場按鈕
    test_fm_btn = ThemedButton(frame, "測試自由市場", command=app.test_free_market, 
                               variant='secondary', size=Theme.FONT_SIZE_NORMAL)
    test_fm_btn.pack(pady=(0, Theme.PADDING_NORMAL), fill="x")
    
    btn_row = ThemedFrame(frame)
    btn_row.pack(fill="x", pady=Theme.PADDING_SMALL)
    
    app.overlay_btn = ThemedButton(btn_row, "顯示位置", command=app.toggle_overlay, variant='secondary')
    app.overlay_btn.pack(side="left", fill="x", expand=True, padx=(0, Theme.PADDING_SMALL))
    
    help_btn = ThemedButton(btn_row, "? HELP", command=app.show_faq, variant='secondary')
    help_btn.pack(side="left", fill="x", expand=True, padx=(Theme.PADDING_SMALL, 0))


def create_log_section(parent, app):
    """建立操作日誌區域"""
    section = SectionFrame(parent, "系統日誌")
    frame = section.get_frame()
    
    # 日誌容器使用邊框顏色作為背景（用於邊框效果）
    log_container = tk.Frame(frame, bg=Theme.LOG_BORDER, bd=1)
    log_container.pack(fill="both", expand=True)
    
    app.log_text = ThemedText(
        log_container, height=12,
        wrap=tk.WORD,
        state="disabled",
        spacing1=1,
        spacing2=1,
        spacing3=1,
        relief="flat",
        borderwidth=0,
        highlightthickness=2,
        highlightbackground=Theme.LOG_BORDER,
        highlightcolor=Theme.BORDER_FOCUS
    )
    app.log_text.pack(fill="both", expand=True, padx=2, pady=2)
