"""Responsive fixed-window layout for the control dashboard."""
import tkinter as tk
from tkinter import ttk
from gui.theme import Theme
from gui.widgets import ThemedFrame, ThemedLabel


class LayoutManager:
    def __init__(self, root):
        self.root = root
        self.main_container = None
        self.title_frame = None
        self.top_container = None
        self.left_panel = None
        self.right_panel = None
        self.bottom_panel = None

    def create_main_layout(self):
        self.scroller = tk.Canvas(self.root, bg=Theme.BACKGROUND_PRIMARY,
                                  highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.scroller.yview)
        self.scroller.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill='y')
        self.scroller.pack(side='left', fill='both', expand=True)
        self.main_container = ThemedFrame(self.scroller, bg=Theme.BACKGROUND_PRIMARY)
        self._window_id = self.scroller.create_window((Theme.PADDING_LARGE, Theme.PADDING_LARGE),
                                                       window=self.main_container, anchor='nw')
        self.main_container.bind('<Configure>', self._update_scroll_region)
        self.scroller.bind('<Configure>', self._fit_content_width)
        self.root.bind('<MouseWheel>', self._on_mouse_wheel, add='+')
        self.create_title_section()
        self.create_top_section()
        return self.main_container

    def _update_scroll_region(self, _event=None):
        self.scroller.configure(scrollregion=self.scroller.bbox('all'))

    def _fit_content_width(self, event):
        self.scroller.itemconfigure(self._window_id,
                                    width=max(1, event.width - 2 * Theme.PADDING_LARGE))
        self._update_scroll_region()

    def _on_mouse_wheel(self, event):
        if self.scroller.winfo_height() < self.main_container.winfo_reqheight():
            self.scroller.yview_scroll(-1 if event.delta > 0 else 1, 'units')

    def create_title_section(self):
        self.title_frame = tk.Frame(self.main_container, bg=Theme.BACKGROUND_PRIMARY)
        self.title_frame.pack(fill='x', pady=(0, Theme.PADDING_LARGE))
        brand = tk.Frame(self.title_frame, bg=Theme.BACKGROUND_PRIMARY)
        brand.pack(side='left', fill='x', expand=True)
        tk.Frame(brand, bg=Theme.TEXT_HIGHLIGHT, width=4, height=52).pack(side='left', padx=(0, 14))
        titles = tk.Frame(brand, bg=Theme.BACKGROUND_PRIMARY)
        titles.pack(side='left')
        ThemedLabel(titles, 'ARTALE / CONTROL', size=Theme.FONT_SIZE_TITLE,
                    weight='bold', color=Theme.TEXT_PRIMARY).pack(anchor='w')
        ThemedLabel(titles, 'AUTOMATION CONSOLE  ·  WINDOWS',
                    size=Theme.FONT_SIZE_SUBTITLE, color=Theme.TEXT_SECONDARY).pack(anchor='w', pady=(3, 0))
        badge = tk.Frame(self.title_frame, bg=Theme.BACKGROUND_SECONDARY,
                         highlightbackground=Theme.BORDER_PRIMARY, highlightthickness=1)
        badge.pack(side='right', padx=(12, 0))
        ThemedLabel(badge, '●  SYSTEM READY', size=Theme.FONT_SIZE_SMALL,
                    weight='bold', color=Theme.STATUS_SUCCESS,
                    bg=Theme.BACKGROUND_SECONDARY).pack(padx=12, pady=9)
        tk.Frame(self.main_container, bg=Theme.BORDER_SECONDARY, height=1).pack(fill='x', pady=(0, 16))

    def create_top_section(self):
        self.top_container = tk.Frame(self.main_container, bg=Theme.BACKGROUND_PRIMARY)
        self.top_container.pack(fill='both', expand=True)
        self.left_panel = tk.Frame(self.top_container, bg=Theme.BACKGROUND_PRIMARY)
        self.left_panel.pack(side='left', fill='both', expand=True, padx=(0, 8))
        self.right_panel = tk.Frame(self.top_container, bg=Theme.BACKGROUND_PRIMARY, width=320)
        self.right_panel.pack(side='right', fill='y', padx=(8, 0))
        self.right_panel.pack_propagate(False)

    def create_bottom_section(self):
        self.bottom_panel = tk.Frame(self.main_container, bg=Theme.BACKGROUND_PRIMARY)
        self.bottom_panel.pack(fill='both', expand=True, pady=(5, 0))
        return self.bottom_panel

    def get_left_panel(self):
        return self.left_panel

    def get_right_panel(self):
        return self.right_panel

    def get_bottom_panel(self):
        return self.bottom_panel or self.create_bottom_section()


class GridLayout:
    @staticmethod
    def create_grid_row(parent, widgets_config, row=0,
                        padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL):
        for widget, column, sticky, colspan in widgets_config:
            widget.grid(row=row, column=column, padx=padx, pady=pady,
                        sticky=sticky, columnspan=colspan or 1)


class FormLayout:
    @staticmethod
    def create_form_row(parent, label_text, widget, label_width=12,
                        padx=Theme.PADDING_NORMAL, pady=Theme.PADDING_SMALL):
        row = ThemedFrame(parent)
        row.pack(fill='x', pady=(0, pady))
        ThemedLabel(row, label_text, width=label_width, anchor='w').pack(side='left', padx=(0, padx))
        widget.pack(side='left', fill='x', expand=True)
        return row
