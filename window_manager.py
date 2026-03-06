"""視窗管理模組"""
import win32gui
import win32con
import logging
from typing import Optional, Dict, Tuple


def is_window_visible(hwnd):
    """檢查視窗是否可見"""
    return win32gui.IsWindowVisible(hwnd)


def get_window_title(hwnd):
    """獲取視窗標題"""
    return win32gui.GetWindowText(hwnd)


def add_window_to_list(hwnd, title, windows):
    """將視窗添加到列表"""
    if title:
        windows.append((hwnd, title))


def filter_windows_by_prefix(windows, filter_prefix):
    """根據前綴過濾視窗列表"""
    filtered_windows = []
    for hwnd, title in windows:
        if title.startswith(filter_prefix):
            filtered_windows.append((hwnd, title))
    return filtered_windows


def validate_window_handle(hwnd):
    """驗證視窗句柄是否有效"""
    return hwnd and win32gui.IsWindow(hwnd)


def convert_rect_to_position_size(rect):
    """將視窗矩形轉換為位置和大小"""
    return (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])


def check_window_minimized(hwnd):
    """檢查視窗是否最小化"""
    return win32gui.IsIconic(hwnd)


def restore_minimized_window(hwnd):
    """還原最小化的視窗"""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)


def set_foreground_window(hwnd):
    """設置前景視窗"""
    win32gui.SetForegroundWindow(hwnd)


def bring_window_to_top(hwnd):
    """將視窗置頂"""
    win32gui.BringWindowToTop(hwnd)


def validate_window_dimensions(width, height):
    """驗證視窗尺寸是否有效"""
    return width > 0 and height > 0


def get_window_position(rect):
    """從矩形獲取視窗位置"""
    return rect[0], rect[1]


def set_window_position_and_size(hwnd, x, y, width, height):
    """設置視窗位置和大小"""
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x, y,
        width, height,
        win32con.SWP_SHOWWINDOW
    )


class WindowManager:
    """視窗管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.window_handle = None
        self.window_map = {}
    
    def enum_windows_callback(self, hwnd, windows):
        """列舉視窗的回調函數"""
        if is_window_visible(hwnd):
            title = get_window_title(hwnd)
            add_window_to_list(hwnd, title, windows)
        return True
    
    def get_windows(self, filter_prefix="MapleStory Worlds"):
        """獲取所有視窗列表，過濾以指定前綴開頭的視窗"""
        windows = []
        win32gui.EnumWindows(self.enum_windows_callback, windows)
        
        # 過濾視窗
        filtered_windows = filter_windows_by_prefix(windows, filter_prefix)
        
        return filtered_windows
    
    def set_window(self, hwnd):
        """設置當前操作的視窗"""
        if validate_window_handle(hwnd):
            self.window_handle = hwnd
            return True
        return False
    
    def get_window_handle(self):
        """獲取當前視窗句柄"""
        return self.window_handle
    
    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """獲取視窗位置和大小 (x, y, width, height)"""
        if not self.window_handle:
            return None
        
        try:
            rect = win32gui.GetWindowRect(self.window_handle)
            return convert_rect_to_position_size(rect)
        except Exception as e:
            self.logger.error(f"獲取視窗位置失敗: {str(e)}")
            return None
    
    def bring_to_front(self):
        """將視窗帶到前景"""
        if not self.window_handle:
            return False
        
        try:
            if not win32gui.IsWindow(self.window_handle):
                return False
            
            if check_window_minimized(self.window_handle):
                restore_minimized_window(self.window_handle)
            
            set_foreground_window(self.window_handle)
            bring_window_to_top(self.window_handle)
            
            return True
        except Exception as e:
            self.logger.error(f"帶到前景失敗: {str(e)}")
            return False
    
    def resize(self, width: int, height: int):
        """重新設定視窗大小"""
        if not self.window_handle:
            return False
        
        try:
            if not validate_window_dimensions(width, height):
                self.logger.error("寬度和高度必須大於0")
                return False
            
            rect = win32gui.GetWindowRect(self.window_handle)
            x, y = get_window_position(rect)
            
            set_window_position_and_size(self.window_handle, x, y, width, height)
            
            self.logger.info(f"視窗大小已設定為 {width}×{height}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定視窗大小失敗: {str(e)}")
            return False
    
    def is_valid(self):
        """檢查視窗是否有效"""
        if not self.window_handle:
            return False
        
        try:
            return win32gui.IsWindow(self.window_handle)
        except:
            return False

