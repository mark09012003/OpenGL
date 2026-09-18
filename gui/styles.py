"""ttk styles shared by all control panels."""
from tkinter import ttk
from gui.theme import Theme


def configure_styles():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background=Theme.BACKGROUND_SECONDARY)
    style.configure('TNotebook', background=Theme.BACKGROUND_PRIMARY, borderwidth=0)
    style.configure('TNotebook.Tab', background=Theme.BACKGROUND_TERTIARY,
                    foreground=Theme.TEXT_SECONDARY,
                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'),
                    padding=(18, 9), borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', Theme.BACKGROUND_SECONDARY),
                                            ('active', Theme.BACKGROUND_HOVER)],
              foreground=[('selected', Theme.TEXT_HIGHLIGHT),
                          ('active', Theme.TEXT_PRIMARY)])
    style.configure('TLabelFrame', background=Theme.BACKGROUND_SECONDARY,
                    foreground=Theme.TEXT_PRIMARY, borderwidth=0)
    style.configure('TLabelFrame.Label', background=Theme.BACKGROUND_SECONDARY,
                    foreground=Theme.TEXT_PRIMARY,
                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold'))
    style.configure('TEntry', fieldbackground=Theme.INPUT_BACKGROUND,
                    foreground=Theme.INPUT_TEXT, insertcolor=Theme.INPUT_CARET,
                    borderwidth=1, relief='flat', padding=(8, 7))
    style.map('TEntry', fieldbackground=[('focus', Theme.INPUT_BACKGROUND_FOCUS)],
              bordercolor=[('focus', Theme.BORDER_FOCUS), ('!focus', Theme.BORDER_SECONDARY)])
    style.configure('TCombobox', fieldbackground=Theme.INPUT_BACKGROUND,
                    background=Theme.INPUT_BACKGROUND, foreground=Theme.INPUT_TEXT,
                    arrowcolor=Theme.TEXT_HIGHLIGHT, borderwidth=1, padding=(8, 7))
    style.map('TCombobox', fieldbackground=[('readonly', Theme.INPUT_BACKGROUND)],
              foreground=[('readonly', Theme.INPUT_TEXT)],
              selectbackground=[('readonly', Theme.INPUT_BACKGROUND)],
              selectforeground=[('readonly', Theme.INPUT_TEXT)])
    style.configure('TCheckbutton', background=Theme.BACKGROUND_SECONDARY,
                    foreground=Theme.TEXT_PRIMARY,
                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL), padding=(0, 5))
    style.map('TCheckbutton', background=[('active', Theme.BACKGROUND_SECONDARY)],
              foreground=[('disabled', Theme.TEXT_DISABLED), ('active', Theme.TEXT_HIGHLIGHT)])
    style.configure('TRadiobutton', background=Theme.BACKGROUND_SECONDARY,
                    foreground=Theme.TEXT_PRIMARY,
                    font=Theme.get_font_config(Theme.FONT_SIZE_NORMAL), padding=(0, 3))
    style.map('TRadiobutton', background=[('active', Theme.BACKGROUND_SECONDARY)],
              foreground=[('active', Theme.TEXT_HIGHLIGHT)])
    style.configure('TButton', background=Theme.BUTTON_SECONDARY,
                    foreground=Theme.BUTTON_SECONDARY_TEXT, borderwidth=0,
                    relief='flat', padding=(12, 8))
    style.map('TButton', background=[('active', Theme.BUTTON_SECONDARY_HOVER)])
    style.configure('TScale', background=Theme.BACKGROUND_SECONDARY,
                    troughcolor=Theme.BACKGROUND_TERTIARY, borderwidth=0)
    return style
