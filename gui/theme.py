"""Central visual tokens for the desktop control panel."""
from typing import Dict, Tuple


class Theme:
    # Deep neutral surfaces keep the screen readable under window opacity.
    BACKGROUND_PRIMARY = '#09121E'
    BACKGROUND_SECONDARY = '#132232'
    BACKGROUND_TERTIARY = '#1B3043'
    BACKGROUND_HOVER = '#223B50'

    TEXT_PRIMARY = '#EAF7FB'
    TEXT_SECONDARY = '#96AFC0'
    TEXT_HIGHLIGHT = '#64E3DB'
    TEXT_DISABLED = '#647C8D'
    TEXT_WHITE = '#FFFFFF'

    BUTTON_PRIMARY = '#5ADBD2'
    BUTTON_PRIMARY_HOVER = '#86EEE6'
    BUTTON_PRIMARY_TEXT = '#09121E'
    BUTTON_SECONDARY = '#20394D'
    BUTTON_SECONDARY_HOVER = '#2D5065'
    BUTTON_SECONDARY_TEXT = '#D8EDF2'
    BUTTON_DANGER = '#8B344A'
    BUTTON_DANGER_HOVER = '#AB465D'
    BUTTON_DANGER_TEXT = '#FFFFFF'
    BUTTON_WARNING = '#E8AD60'
    BUTTON_WARNING_HOVER = '#F2C483'

    BORDER_PRIMARY = '#2B5264'
    BORDER_SECONDARY = '#254353'
    BORDER_FOCUS = '#65E3DB'

    INPUT_BACKGROUND = '#0D1C2A'
    INPUT_BACKGROUND_FOCUS = '#142A3A'
    INPUT_TEXT = '#EDF8FA'
    INPUT_CARET = '#66E9DF'

    LOG_BACKGROUND = '#0A1723'
    LOG_TEXT = '#BFD4DE'
    LOG_BORDER = '#254353'

    STATUS_SUCCESS = '#70D6B2'
    STATUS_ERROR = '#EF8194'
    STATUS_WARNING = '#E8AD60'
    STATUS_INFO = '#79B8E5'

    FONT_FAMILY = 'Microsoft JhengHei UI'
    FONT_MONO = 'Consolas'
    FONT_SIZE_TITLE = 21
    FONT_SIZE_SUBTITLE = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_LARGE = 11
    FONT_SIZE_SMALL = 9

    PADDING_SMALL = 4
    PADDING_NORMAL = 8
    PADDING_MEDIUM = 12
    PADDING_LARGE = 18
    BORDER_RADIUS = 0

    @classmethod
    def get_color_palette(cls) -> Dict[str, str]:
        return {
            'bg_primary': cls.BACKGROUND_PRIMARY,
            'bg_secondary': cls.BACKGROUND_SECONDARY,
            'bg_tertiary': cls.BACKGROUND_TERTIARY,
            'text_primary': cls.TEXT_PRIMARY,
            'text_secondary': cls.TEXT_SECONDARY,
            'text_highlight': cls.TEXT_HIGHLIGHT,
            'button_primary': cls.BUTTON_PRIMARY,
            'button_secondary': cls.BUTTON_SECONDARY,
            'button_danger': cls.BUTTON_DANGER,
            'border_primary': cls.BORDER_PRIMARY,
            'input_bg': cls.INPUT_BACKGROUND,
            'log_bg': cls.LOG_BACKGROUND,
        }

    @classmethod
    def get_font_config(cls, size: int = None, weight: str = 'normal') -> Tuple[str, int, str]:
        return (cls.FONT_FAMILY, size or cls.FONT_SIZE_NORMAL, weight)
