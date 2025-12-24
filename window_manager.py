"""視窗管理模組"""
import win32gui
import win32con
import logging
from typing import Optional, Dict, Tuple


class WindowManager:
    """視窗管理器"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.window_handle = None
        self.window_map = {}
    
    def enum_windows_callback(self, hwnd, windows):
        """列舉視窗的回調函數"""
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
        return True
    
    def get_windows(self, filter_prefix="MapleStory Worlds"):
        """獲取所有視窗列表，過濾以指定前綴開頭的視窗"""
        windows = []
        win32gui.EnumWindows(self.enum_windows_callback, windows)
        
        # 過濾視窗
        filtered_windows = []
        for hwnd, title in windows:
            if title.startswith(filter_prefix):
                filtered_windows.append((hwnd, title))
        
        return filtered_windows
    
    def set_window(self, hwnd):
        """設置當前操作的視窗"""
        if hwnd and win32gui.IsWindow(hwnd):
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
            return (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
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
            
            if win32gui.IsIconic(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            
            win32gui.SetForegroundWindow(self.window_handle)
            win32gui.BringWindowToTop(self.window_handle)
            
            return True
        except Exception as e:
            self.logger.error(f"帶到前景失敗: {str(e)}")
            return False
    
    def resize(self, width: int, height: int):
        """重新設定視窗大小"""
        if not self.window_handle:
            return False
        
        try:
            if width <= 0 or height <= 0:
                self.logger.error("寬度和高度必須大於0")
                return False
            
            rect = win32gui.GetWindowRect(self.window_handle)
            x, y = rect[0], rect[1]
            
            win32gui.SetWindowPos(
                self.window_handle,
                win32con.HWND_TOP,
                x, y,
                width, height,
                win32con.SWP_SHOWWINDOW
            )
            
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

