"""Dashboard sections. Widget names are the GUI controller's public bindings."""
import tkinter as tk
from tkinter import ttk
from gui.theme import Theme
from gui.widgets import ThemedFrame, ThemedLabel, ThemedButton, ThemedEntry, ThemedText, SectionFrame


def _label(parent, text, row, column=0, **kwargs):
    return ThemedLabel(parent, text, size=Theme.FONT_SIZE_SMALL,
                       color=Theme.TEXT_SECONDARY, anchor='w', **kwargs).grid(
        row=row, column=column, sticky='w', padx=(0, 7), pady=5)


def create_window_section(parent, app):
    frame = SectionFrame(parent, '01   遊戲視窗').get_frame()
    ThemedLabel(frame, '目標視窗', size=Theme.FONT_SIZE_SMALL,
                color=Theme.TEXT_SECONDARY).pack(anchor='w', pady=(0, 5))
    row = ThemedFrame(frame)
    row.pack(fill='x')
    app.window_var = tk.StringVar()
    app.window_combo = ttk.Combobox(row, textvariable=app.window_var,
                                    state='readonly', width=36)
    app.window_combo.pack(side='left', fill='x', expand=True, padx=(0, 8))
    app.window_combo.bind('<<ComboboxSelected>>', app.on_window_selected)
    ThemedButton(row, '刷新', command=app.refresh_windows,
                 variant='secondary').pack(side='right')
    app.resolution_label = ThemedLabel(frame, '尚未選擇視窗',
                                       size=Theme.FONT_SIZE_SMALL,
                                       color=Theme.STATUS_INFO, anchor='w')
    app.resolution_label.pack(fill='x', pady=(7, 0))


def create_skill_section(parent, app):
    frame = SectionFrame(parent, '02   技能配置').get_frame()
    grid = ThemedFrame(frame)
    grid.pack(fill='x')
    grid.columnconfigure(1, weight=1)
    grid.columnconfigure(3, weight=1)

    _label(grid, '技能 1  /  必須', 0)
    app.prayer_key_var = tk.StringVar(value='f1')
    ThemedEntry(grid, textvariable=app.prayer_key_var, width=11).grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=4)
    app.skill2_enabled_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(grid, text='技能 2', variable=app.skill2_enabled_var).grid(row=0, column=2, sticky='w', pady=4)
    app.angel_blessing_var = tk.StringVar(value='f2')
    ThemedEntry(grid, textvariable=app.angel_blessing_var, width=11).grid(row=0, column=3, sticky='ew', pady=4)

    app.custom_skill1_var = tk.BooleanVar()
    ttk.Checkbutton(grid, text='技能 3', variable=app.custom_skill1_var,
                    command=app.toggle_custom_skill1).grid(row=1, column=0, sticky='w', pady=4)
    app.custom_skill1_key_var = tk.StringVar(value='f3')
    holder1 = ThemedFrame(grid)
    holder1.grid(row=1, column=1, sticky='ew', padx=(0, 15))
    app.custom_skill1_entry = ThemedEntry(holder1, textvariable=app.custom_skill1_key_var, width=11)
    app.custom_skill2_var = tk.BooleanVar()
    ttk.Checkbutton(grid, text='技能 4', variable=app.custom_skill2_var,
                    command=app.toggle_custom_skill2).grid(row=1, column=2, sticky='w', pady=4)
    app.custom_skill2_key_var = tk.StringVar(value='f4')
    holder2 = ThemedFrame(grid)
    holder2.grid(row=1, column=3, sticky='ew')
    app.custom_skill2_entry = ThemedEntry(holder2, textvariable=app.custom_skill2_key_var, width=11)

    _label(grid, '技能間隔  /  秒', 2)
    app.blessing_interval_var = tk.StringVar(value='0.5')
    ThemedEntry(grid, textvariable=app.blessing_interval_var, width=11).grid(row=2, column=1, sticky='ew', padx=(0, 15), pady=4)
    _label(grid, '自身血條 X', 2, 2)
    app.self_bar_x_var = tk.StringVar()
    ThemedEntry(grid, textvariable=app.self_bar_x_var, width=11).grid(row=2, column=3, sticky='ew', pady=4)
    ThemedLabel(frame, '多人場景填入自身血條左端 X；單人可留空',
                size=Theme.FONT_SIZE_SMALL, color=Theme.TEXT_DISABLED).pack(anchor='w', pady=(6, 0))


def create_parameter_section(parent, app):
    frame = SectionFrame(parent, '03   執行參數').get_frame()
    grid = ThemedFrame(frame)
    grid.pack(fill='x')
    grid.columnconfigure(1, weight=1)
    grid.columnconfigure(3, weight=1)

    _label(grid, '循環等待  /  秒', 0)
    app.fm_wait_var = tk.StringVar(value='230')
    ThemedEntry(grid, textvariable=app.fm_wait_var, width=10).grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=4)
    _label(grid, '進入檢查  /  秒', 0, 2)
    app.fm_check_time_var = tk.StringVar(value='3.0')
    ThemedEntry(grid, textvariable=app.fm_check_time_var, width=10).grid(row=0, column=3, sticky='ew', pady=4)

    _label(grid, '左移時間  /  秒', 1)
    app.left_move_time_var = tk.StringVar(value='0.1')
    ThemedEntry(grid, textvariable=app.left_move_time_var, width=10).grid(row=1, column=1, sticky='ew', padx=(0, 15), pady=4)
    _label(grid, '右移時間  /  秒', 1, 2)
    app.right_move_time_var = tk.StringVar(value='0.1')
    ThemedEntry(grid, textvariable=app.right_move_time_var, width=10).grid(row=1, column=3, sticky='ew', pady=4)

    app.target_width_var = tk.StringVar(value='1295')
    app.target_height_var = tk.StringVar(value='759')
    app.auto_stop_enabled_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(grid, text='定時停止', variable=app.auto_stop_enabled_var,
                    command=app.toggle_auto_stop_entry).grid(row=2, column=0, sticky='w', pady=4)
    app.auto_stop_time_var = tk.StringVar(value='23:59')
    app.auto_stop_time_entry = ThemedEntry(grid, textvariable=app.auto_stop_time_var,
                                           width=10, state='disabled')
    app.auto_stop_time_entry.grid(row=2, column=1, sticky='ew', padx=(0, 15), pady=4)
    _label(grid, '24 小時制  /  HH:MM', 2, 2)

    tk.Frame(frame, bg=Theme.BORDER_SECONDARY, height=1).pack(fill='x', pady=(10, 8))
    options = ThemedFrame(frame)
    options.pack(fill='x')
    left = ThemedFrame(options)
    left.pack(side='left', fill='x', expand=True)
    right = ThemedFrame(options)
    right.pack(side='left', fill='x', expand=True)
    app.enter_fm_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(left, text='進入自由市場', variable=app.enter_fm_var).pack(anchor='w')
    app.use_floating_window_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(left, text='使用懸浮控制窗', variable=app.use_floating_window_var).pack(anchor='w')
    app.anti_detect_after_fm_var = tk.BooleanVar()
    ttk.Checkbutton(left, text='離開後輕微移動', variable=app.anti_detect_after_fm_var).pack(anchor='w')
    app.fixed_move_var = tk.BooleanVar()
    ttk.Checkbutton(right, text='固定來回移動', variable=app.fixed_move_var).pack(anchor='w')
    app.move_direction_var = tk.StringVar(value='left')
    direction = ThemedFrame(right)
    direction.pack(anchor='w', pady=(5, 0))
    ThemedLabel(direction, '移動方向', size=Theme.FONT_SIZE_SMALL,
                color=Theme.TEXT_SECONDARY).pack(side='left', padx=(0, 8))
    ttk.Radiobutton(direction, text='左', variable=app.move_direction_var,
                    value='left').pack(side='left')
    ttk.Radiobutton(direction, text='右', variable=app.move_direction_var,
                    value='right').pack(side='left')


def create_action_buttons(parent, app):
    frame = SectionFrame(parent, '操作控制').get_frame()
    ThemedLabel(frame, 'AUTOMATION', size=Theme.FONT_SIZE_SMALL,
                color=Theme.TEXT_SECONDARY).pack(anchor='w', pady=(0, 5))
    ThemedLabel(frame, '準備開始', size=Theme.FONT_SIZE_TITLE,
                weight='bold', color=Theme.TEXT_PRIMARY).pack(anchor='w', pady=(0, 15))
    app.start_btn = ThemedButton(frame, 'START  /  啟動', command=app.start_automation,
                                 variant='primary')
    app.start_btn.pack(fill='x', pady=(0, 9))
    app.stop_btn = ThemedButton(frame, 'STOP  /  停止', command=app.stop_automation,
                                variant='danger', state='disabled')
    app.stop_btn.pack(fill='x', pady=(0, 14))
    tk.Frame(frame, bg=Theme.BORDER_SECONDARY, height=1).pack(fill='x', pady=(0, 12))
    ThemedButton(frame, '測試自由市場辨識', command=app.test_free_market,
                 variant='secondary').pack(fill='x', pady=(0, 8))
    app.overlay_btn = ThemedButton(frame, '顯示血條位置', command=app.toggle_overlay)
    app.overlay_btn.pack(fill='x', pady=(0, 8))
    app.calibration_btn = ThemedButton(frame, '校準畫面座標', command=app.toggle_calibration)
    app.calibration_btn.pack(fill='x', pady=(0, 8))
    ThemedButton(frame, '使用說明', command=app.show_faq).pack(fill='x')


def create_log_section(parent, app):
    frame = SectionFrame(parent, '系統事件').get_frame()
    app.log_text = ThemedText(frame, height=7, wrap=tk.WORD, state='disabled',
                              relief='flat', borderwidth=0, highlightthickness=0,
                              padx=10, pady=8)
    app.log_text.pack(fill='both', expand=True)
