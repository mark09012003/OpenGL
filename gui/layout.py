"""GUI布局模組 - 定義標準化布局系統"""
import tkinter as tk
from gui.theme import Theme
from gui.widgets import ThemedFrame, ThemedLabel, SectionFrame


class LayoutManager:
    """布局管理器 - 管理整體布局結構"""
    
    def __init__(self, root):
        self.root = root
        self.main_container = None
        self.title_frame = None
        self.top_container = None
        self.left_panel = None
        self.right_panel = None
        self.bottom_panel = None
    
    def create_main_layout(self):
        """創建主布局結構"""
        # 主容器
        self.main_container = ThemedFrame(self.root)
        self.main_container.pack(
            fill="both", expand=True, 
            padx=Theme.PADDING_LARGE, 
            pady=Theme.PADDING_LARGE
        )
        
        # 標題區域
        self.create_title_section()
        
        # 頂部區域（左右分欄）
        self.create_top_section()
        
        return self.main_container
    
    def create_title_section(self):
        """創建標題區域"""
        self.title_frame = ThemedFrame(self.main_container)
        self.title_frame.pack(fill="x", pady=(0, Theme.PADDING_LARGE))
        
        title_label = ThemedLabel(
            self.title_frame, 
            text="MAPLESTORY 自動化控制系統",
            size=Theme.FONT_SIZE_TITLE,
            weight='bold',
            color=Theme.TEXT_PRIMARY
        )
        title_label.pack()
        
        subtitle = ThemedLabel(
            self.title_frame,
            text="AUTOMATION CONTROL SYSTEM",
            size=Theme.FONT_SIZE_SUBTITLE,
            color=Theme.TEXT_SECONDARY
        )
        subtitle.pack()
    
    def create_top_section(self):
        """創建頂部區域（左右分欄）"""
        self.top_container = ThemedFrame(self.main_container)
        self.top_container.pack(fill="both", expand=True, pady=(0, Theme.PADDING_MEDIUM))
        
        # 左側面板
        self.left_panel = ThemedFrame(self.top_container)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, Theme.PADDING_LARGE))
        
        # 右側面板
        self.right_panel = ThemedFrame(self.top_container, width=300)
        self.right_panel.pack(side="right", fill="y", padx=(Theme.PADDING_LARGE, 0))
        self.right_panel.pack_propagate(False)
    
    def create_bottom_section(self):
        """創建底部區域"""
        self.bottom_panel = ThemedFrame(self.main_container)
        self.bottom_panel.pack(fill="both", expand=True, pady=(Theme.PADDING_MEDIUM, 0))
        return self.bottom_panel
    
    def get_left_panel(self):
        """獲取左側面板"""
        return self.left_panel
    
    def get_right_panel(self):
        """獲取右側面板"""
        return self.right_panel
    
    def get_bottom_panel(self):
        """獲取底部面板"""
        return self.bottom_panel or self.create_bottom_section()


class GridLayout:
    """網格布局助手"""
    
    @staticmethod
    def create_grid_row(parent, widgets_config, row=0, padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL):
        """
        創建網格行
        
        Args:
            parent: 父容器
            widgets_config: 組件配置列表，每個元素為 (widget, column, sticky, colspan)
            row: 行號
            padx: 水平間距
            pady: 垂直間距
        """
        for widget, column, sticky, colspan in widgets_config:
            widget.grid(
                row=row, column=column,
                padx=padx, pady=pady,
                sticky=sticky,
                columnspan=colspan if colspan else 1
            )


class FormLayout:
    """表單布局助手"""
    
    @staticmethod
    def create_form_row(parent, label_text, widget, label_width=12, 
                       padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL):
        """
        創建表單行（標籤 + 控件）
        
        Args:
            parent: 父容器
            label_text: 標籤文字
            widget: 控件
            label_width: 標籤寬度
            padx: 水平間距
            pady: 垂直間距
        """
        row = ThemedFrame(parent)
        row.pack(fill="x", pady=(0, pady))
        
        label = ThemedLabel(
            row, text=label_text,
            size=Theme.FONT_SIZE_NORMAL,
            width=label_width,
            anchor="w"
        )
        label.pack(side="left", padx=(0, padx))
        
        widget.pack(side="left", fill="x", expand=True)
        
        return row

