"""GUI樣式配置模組 - 基於主題配色應用樣式"""
from tkinter import ttk
from gui.theme import Theme


def configure_styles():
    """配置所有ttk控件樣式，基於主題配色"""
    style = ttk.Style()
    style.theme_use('clam')
    
    # ========== LabelFrame 樣式 ==========
    # 注意：ttk.LabelFrame的內部Frame背景色無法通過樣式直接設置
    # 需要在創建後直接訪問內部Frame並設置背景色
    style.configure('TLabelFrame', 
                   background=Theme.BACKGROUND_PRIMARY, 
                   foreground=Theme.TEXT_PRIMARY, 
                   borderwidth=1, 
                   relief='flat')
    style.configure('TLabelFrame.Label', 
                   background=Theme.BACKGROUND_PRIMARY, 
                   foreground=Theme.TEXT_PRIMARY,
                   font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'))
    style.map('TLabelFrame', 
             background=[('', Theme.BACKGROUND_PRIMARY)],
             bordercolor=[('', Theme.BORDER_PRIMARY)])
    
    # ========== Frame 樣式 ==========
    style.configure('TFrame', 
                   background=Theme.BACKGROUND_PRIMARY)
    
    # ========== Button 樣式 ==========
    style.configure('TButton', 
                   background=Theme.BUTTON_SECONDARY, 
                   foreground=Theme.BUTTON_SECONDARY_TEXT,
                   borderwidth=1, 
                   relief='flat', 
                   padding=Theme.PADDING_NORMAL)
    style.map('TButton', 
             background=[('active', Theme.BUTTON_SECONDARY_HOVER), 
                        ('pressed', Theme.BUTTON_SECONDARY)],
             foreground=[('active', Theme.TEXT_HIGHLIGHT), 
                        ('pressed', Theme.BUTTON_SECONDARY_TEXT)])
    
    # ========== Entry 樣式 ==========
    style.configure('TEntry', 
                   fieldbackground=Theme.INPUT_BACKGROUND, 
                   foreground=Theme.INPUT_TEXT,
                   borderwidth=1, 
                   relief='flat', 
                   insertcolor=Theme.INPUT_CARET)
    style.map('TEntry', 
             fieldbackground=[('focus', Theme.INPUT_BACKGROUND_FOCUS), 
                             ('!focus', Theme.INPUT_BACKGROUND)],
             bordercolor=[('focus', Theme.BORDER_FOCUS), 
                         ('!focus', Theme.BORDER_PRIMARY)])
    
    # ========== Checkbutton 樣式 ==========
    style.configure('TCheckbutton', 
                   background=Theme.BACKGROUND_PRIMARY, 
                   foreground=Theme.TEXT_PRIMARY,
                   focuscolor='none')
    style.map('TCheckbutton',
             background=[('active', Theme.BACKGROUND_PRIMARY), 
                        ('selected', Theme.BACKGROUND_PRIMARY)],
             foreground=[('active', Theme.TEXT_HIGHLIGHT), 
                        ('selected', Theme.TEXT_PRIMARY)])
    
    # ========== Radiobutton 樣式 ==========
    style.configure('TRadiobutton', 
                   background=Theme.BACKGROUND_PRIMARY, 
                   foreground=Theme.TEXT_PRIMARY,
                   focuscolor='none')
    style.map('TRadiobutton',
             background=[('active', Theme.BACKGROUND_PRIMARY), 
                        ('selected', Theme.BACKGROUND_PRIMARY)],
             foreground=[('active', Theme.TEXT_HIGHLIGHT), 
                        ('selected', Theme.TEXT_PRIMARY)])
    
    # ========== Combobox 樣式 ==========
    style.configure('TCombobox', 
                   fieldbackground=Theme.INPUT_BACKGROUND, 
                   foreground=Theme.INPUT_TEXT,
                   borderwidth=1, 
                   arrowcolor=Theme.TEXT_PRIMARY)
    style.map('TCombobox',
             fieldbackground=[('readonly', Theme.INPUT_BACKGROUND), 
                             ('focus', Theme.INPUT_BACKGROUND_FOCUS)],
             bordercolor=[('focus', Theme.BORDER_FOCUS), 
                         ('!focus', Theme.BORDER_PRIMARY)])
    
    # ========== Scale 樣式 ==========
    style.configure('TScale', 
                   background=Theme.BACKGROUND_PRIMARY, 
                   troughcolor=Theme.BACKGROUND_SECONDARY,
                   borderwidth=0, 
                   sliderthickness=12)
    
    return style
