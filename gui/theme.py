"""GUI主題配色模組 - 基礎配色定義"""
from typing import Dict, Tuple


class Theme:
    """主題配色類 - 定義所有顏色常量"""
    
    # ========== 基礎背景色 ==========
    BACKGROUND_PRIMARY = '#0A0E27'      # 主背景（深藍黑）
    BACKGROUND_SECONDARY = '#1A1F3A'    # 次背景（深灰藍）
    BACKGROUND_TERTIARY = '#1A3F5A'     # 第三背景（中灰藍）
    
    # ========== 文字顏色 ==========
    TEXT_PRIMARY = '#00D9FF'            # 主文字（青色）
    TEXT_SECONDARY = '#4A9EFF'          # 次文字（亮藍）
    TEXT_HIGHLIGHT = '#00FFFF'          # 高亮文字（亮青）
    TEXT_DISABLED = '#5A6A7A'           # 禁用文字（灰）
    TEXT_WHITE = '#FFFFFF'               # 白色文字
    
    # ========== 按鈕顏色 ==========
    BUTTON_PRIMARY = '#00D9FF'          # 主按鈕（青色）
    BUTTON_PRIMARY_HOVER = '#00FFFF'     # 主按鈕懸停
    BUTTON_PRIMARY_TEXT = '#0A0E27'      # 主按鈕文字
    
    BUTTON_SECONDARY = '#1A3F5A'         # 次按鈕（灰藍）
    BUTTON_SECONDARY_HOVER = '#2A5F7A'   # 次按鈕懸停
    BUTTON_SECONDARY_TEXT = '#00D9FF'    # 次按鈕文字
    
    BUTTON_DANGER = '#FF3B5C'            # 危險按鈕（紅色）
    BUTTON_DANGER_HOVER = '#FF5C7C'      # 危險按鈕懸停
    BUTTON_DANGER_TEXT = '#FFFFFF'       # 危險按鈕文字
    
    BUTTON_WARNING = '#FFA500'           # 警告按鈕（橙色）
    BUTTON_WARNING_HOVER = '#FFB733'     # 警告按鈕懸停
    
    # ========== 邊框顏色 ==========
    BORDER_PRIMARY = '#00D9FF'           # 主邊框（青色）
    BORDER_SECONDARY = '#4A9EFF'         # 次邊框（亮藍）
    BORDER_FOCUS = '#00FFFF'             # 焦點邊框（亮青）
    
    # ========== 輸入框顏色 ==========
    INPUT_BACKGROUND = '#1A1F3A'         # 輸入框背景
    INPUT_BACKGROUND_FOCUS = '#1A2F4A'   # 輸入框焦點背景
    INPUT_TEXT = '#00D9FF'               # 輸入框文字
    INPUT_CARET = '#00D9FF'              # 輸入框游標
    
    # ========== 日誌區域顏色 ==========
    LOG_BACKGROUND = '#0A0E27'           # 日誌背景
    LOG_TEXT = '#00D9FF'                 # 日誌文字
    LOG_BORDER = '#00D9FF'               # 日誌邊框
    
    # ========== 狀態顏色 ==========
    STATUS_SUCCESS = '#00D9FF'           # 成功狀態（青色）
    STATUS_ERROR = '#FF3B5C'             # 錯誤狀態（紅色）
    STATUS_WARNING = '#FFA500'           # 警告狀態（橙色）
    STATUS_INFO = '#4A9EFF'              # 信息狀態（亮藍）
    
    # ========== 字體配置 ==========
    FONT_FAMILY = 'Consolas'             # 字體家族
    FONT_SIZE_TITLE = 18                 # 標題字體大小
    FONT_SIZE_SUBTITLE = 10              # 副標題字體大小
    FONT_SIZE_NORMAL = 9                 # 正常字體大小
    FONT_SIZE_LARGE = 12                 # 大字體大小
    FONT_SIZE_SMALL = 8                  # 小字體大小
    
    # ========== 間距配置 ==========
    PADDING_SMALL = 3                    # 小間距
    PADDING_NORMAL = 6                   # 正常間距
    PADDING_MEDIUM = 8                   # 中等間距
    PADDING_LARGE = 12                   # 大間距
    
    # ========== 圓角配置 ==========
    BORDER_RADIUS = 0                    # 邊框圓角（tkinter不支持，保留用於未來）
    
    @classmethod
    def get_color_palette(cls) -> Dict[str, str]:
        """獲取完整配色方案字典"""
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
        """獲取字體配置元組"""
        if size is None:
            size = cls.FONT_SIZE_NORMAL
        return (cls.FONT_FAMILY, size, weight)

