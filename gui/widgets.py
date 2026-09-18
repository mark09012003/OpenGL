"""Reusable widgets for the dark desktop interface."""
import tkinter as tk
from tkinter import ttk
from gui.theme import Theme


def parent_background(parent):
    try:
        return parent.cget('bg')
    except (AttributeError, tk.TclError):
        return Theme.BACKGROUND_PRIMARY


class ThemedFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', parent_background(parent))
        super().__init__(parent, **kwargs)


class ThemedLabel(tk.Label):
    def __init__(self, parent, text='', size=None, weight='normal', color=None, **kwargs):
        kwargs.setdefault('bg', parent_background(parent))
        kwargs.setdefault('fg', color or Theme.TEXT_PRIMARY)
        kwargs.setdefault('font', Theme.get_font_config(size, weight))
        super().__init__(parent, text=text, **kwargs)


class ThemedButton(tk.Button):
    COLORS = {
        'primary': (Theme.BUTTON_PRIMARY, Theme.BUTTON_PRIMARY_TEXT, Theme.BUTTON_PRIMARY_HOVER),
        'secondary': (Theme.BUTTON_SECONDARY, Theme.BUTTON_SECONDARY_TEXT, Theme.BUTTON_SECONDARY_HOVER),
        'danger': (Theme.BUTTON_DANGER, Theme.BUTTON_DANGER_TEXT, Theme.BUTTON_DANGER_HOVER),
    }

    def __init__(self, parent, text='', command=None, variant='secondary', size=None,
                 weight='bold', **kwargs):
        bg, fg, active_bg = self.COLORS.get(variant, self.COLORS['secondary'])
        kwargs.setdefault('font', Theme.get_font_config(size or Theme.FONT_SIZE_NORMAL, weight))
        kwargs.setdefault('relief', 'flat')
        kwargs.setdefault('cursor', 'hand2')
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('padx', 12)
        kwargs.setdefault('pady', 9)
        super().__init__(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=active_bg, activeforeground=fg, **kwargs)
        self._normal_bg = bg
        self._hover_bg = active_bg
        self.bind('<Enter>', self._on_enter, add='+')
        self.bind('<Leave>', self._on_leave, add='+')

    def _on_enter(self, _event):
        if self.cget('state') != 'disabled':
            self.configure(bg=self._hover_bg)

    def _on_leave(self, _event):
        self.configure(bg=self._normal_bg)


class ThemedEntry(ttk.Entry):
    pass


class ThemedText(tk.Text):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', Theme.LOG_BACKGROUND)
        kwargs.setdefault('fg', Theme.LOG_TEXT)
        kwargs.setdefault('font', (Theme.FONT_MONO, Theme.FONT_SIZE_SMALL))
        kwargs.setdefault('insertbackground', Theme.INPUT_CARET)
        kwargs.setdefault('selectbackground', Theme.BACKGROUND_TERTIARY)
        kwargs.setdefault('selectforeground', Theme.TEXT_PRIMARY)
        super().__init__(parent, **kwargs)


class ThemedLabelFrame(ttk.LabelFrame):
    pass


class SectionFrame:
    """Flat raised panel with one structural border and a quiet heading."""
    def __init__(self, parent, title='', padding=Theme.PADDING_MEDIUM):
        self.frame = tk.Frame(parent, bg=Theme.BORDER_SECONDARY, bd=0)
        self.frame.pack(fill='x', pady=(0, Theme.PADDING_MEDIUM))
        surface = tk.Frame(self.frame, bg=Theme.BACKGROUND_SECONDARY)
        surface.pack(fill='both', expand=True, padx=1, pady=1)
        header = tk.Frame(surface, bg=Theme.BACKGROUND_SECONDARY)
        header.pack(fill='x', padx=padding, pady=(padding, 6))
        tk.Frame(header, bg=Theme.TEXT_HIGHLIGHT, width=3, height=16).pack(side='left', padx=(0, 9))
        self.title_label = ThemedLabel(header, text=title, size=Theme.FONT_SIZE_NORMAL,
                                       weight='bold', color=Theme.TEXT_PRIMARY)
        self.title_label.pack(side='left')
        self.content_frame = tk.Frame(surface, bg=Theme.BACKGROUND_SECONDARY)
        self.content_frame.pack(fill='both', expand=True, padx=padding, pady=(0, padding))

    def get_frame(self):
        return self.content_frame
