"""GUI基礎組件模組 - 基於主題創建標準化組件"""
import tkinter as tk
from tkinter import ttk
from gui.theme import Theme


class ThemedFrame(tk.Frame):
    """主題化Frame"""
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop('bg', Theme.BACKGROUND_PRIMARY)
        super().__init__(parent, bg=bg, **kwargs)


class ThemedLabel(tk.Label):
    """主題化Label"""
    def __init__(self, parent, text="", size=None, weight='normal', 
                 color=None, **kwargs):
        bg = kwargs.pop('bg', Theme.BACKGROUND_PRIMARY)
        fg = kwargs.pop('fg', color or Theme.TEXT_PRIMARY)
        font = kwargs.pop('font', Theme.get_font_config(size, weight))
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font, **kwargs)


class ThemedButton(tk.Button):
    """主題化Button"""
    def __init__(self, parent, text="", command=None,
                 variant='secondary', size=None, weight='bold', **kwargs):
        # 根據變體選擇顏色
        if variant == 'primary':
            bg = Theme.BUTTON_PRIMARY
            fg = Theme.BUTTON_PRIMARY_TEXT
            active_bg = Theme.BUTTON_PRIMARY_HOVER
            active_fg = Theme.BUTTON_PRIMARY_TEXT
        elif variant == 'danger':
            bg = Theme.BUTTON_DANGER
            fg = Theme.BUTTON_DANGER_TEXT
            active_bg = Theme.BUTTON_DANGER_HOVER
            active_fg = Theme.BUTTON_DANGER_TEXT
        else:  # secondary (default)
            bg = Theme.BUTTON_SECONDARY
            fg = Theme.BUTTON_SECONDARY_TEXT
            active_bg = Theme.BUTTON_SECONDARY_HOVER
            active_fg = Theme.TEXT_HIGHLIGHT
        
        # 處理 size 參數
        if size is not None:
            font = Theme.get_font_config(size, weight)
        else:
            font = kwargs.pop('font', Theme.get_font_config(Theme.FONT_SIZE_LARGE, 'bold'))
        
        relief = kwargs.pop('relief', 'flat')
        cursor = kwargs.pop('cursor', 'hand2')
        bd = kwargs.pop('bd', 0)
        highlightthickness = kwargs.pop('highlightthickness', 0)
        
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief=relief, cursor=cursor, bd=bd,
            activebackground=active_bg, activeforeground=active_fg,
            highlightthickness=highlightthickness, **kwargs
        )


class ThemedEntry(ttk.Entry):
    """主題化Entry（使用ttk.Entry，樣式已在styles.py中配置）"""
    pass


class ThemedText(tk.Text):
    """主題化Text"""
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop('bg', Theme.LOG_BACKGROUND)
        fg = kwargs.pop('fg', Theme.LOG_TEXT)
        font = kwargs.pop('font', Theme.get_font_config(Theme.FONT_SIZE_NORMAL))
        insertbackground = kwargs.pop('insertbackground', Theme.INPUT_CARET)
        selectbackground = kwargs.pop('selectbackground', Theme.BACKGROUND_TERTIARY)
        selectforeground = kwargs.pop('selectforeground', Theme.TEXT_PRIMARY)
        
        super().__init__(
            parent, bg=bg, fg=fg, font=font,
            insertbackground=insertbackground,
            selectbackground=selectbackground,
            selectforeground=selectforeground,
            **kwargs
        )


class ThemedLabelFrame(ttk.LabelFrame):
    """主題化LabelFrame（使用ttk.LabelFrame，樣式已在styles.py中配置）"""
    pass


class SectionFrame:
    """區塊框架 - 使用tk.Frame替代ttk.LabelFrame以完全控制背景色"""
    def __init__(self, parent, title="", padding=Theme.PADDING_MEDIUM):
        # 使用tk.Frame替代ttk.LabelFrame
        self.frame = ThemedFrame(parent)
        self.frame.pack(fill="x", pady=(0, Theme.PADDING_MEDIUM))
        
        # 創建標題標籤
        self.title_label = ThemedLabel(
            self.frame,
            text=f"▸ {title}",
            size=Theme.FONT_SIZE_NORMAL,
            weight='bold',
            color=Theme.TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", padx=Theme.PADDING_NORMAL, pady=(Theme.PADDING_NORMAL, Theme.PADDING_SMALL))
        
        # 創建內容容器
        self.content_frame = ThemedFrame(self.frame)
        self.content_frame.pack(fill="both", expand=True, padx=Theme.PADDING_NORMAL, pady=(0, Theme.PADDING_NORMAL))
        
        # 添加邊框效果（使用Frame模擬邊框）
        self._create_border()
    
    def _create_border(self):
        """創建邊框效果"""
        # 在frame底部創建一個帶顏色的邊框線
        border_frame = tk.Frame(
            self.frame,
            bg=Theme.BORDER_PRIMARY,
            height=1
        )
        border_frame.pack(fill="x", side="bottom", padx=0, pady=0)
    
    def get_frame(self):
        """獲取內容Frame（用於放置子控件）"""
        return self.content_frame

