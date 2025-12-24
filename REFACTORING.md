# 程式重構說明

## 重構結構

程式已拆分成以下模組：

### 核心模組

1. **`config.py`** - 配置管理
   - `ConfigManager`: 處理配置的保存和載入

2. **`window_manager.py`** - 視窗管理
   - `WindowManager`: 處理視窗列舉、選擇、調整大小、置前等操作

3. **`detection.py`** - 圖像檢測
   - `DetectionManager`: 處理HP條檢測、自由市場檢測等圖像識別功能

4. **`automation.py`** - 自動化邏輯
   - `AutomationManager`: 處理技能執行、移動、進入自由市場等自動化操作

5. **`utils.py`** - 工具函數
   - `setup_logging()`: 日誌系統初始化

### GUI模組

6. **`gui/styles.py`** - GUI樣式配置
   - `configure_styles()`: 配置深色科技風格的主題

7. **`gui/components.py`** - GUI組件（待完成）
   - 需要從原始文件遷移所有GUI組件創建函數

8. **`gui/__init__.py`** - GUI主類（待完成）
   - 需要從原始文件遷移主GUI類

### 入口文件

9. **`main.py`** - 主入口
   - 整合所有模組並啟動應用程式

## 待完成工作

### 1. GUI組件遷移

需要從 `maplestory_auto_prayer.py` 遷移以下GUI相關方法到 `gui/components.py`:

- `create_widgets()`
- `create_window_section()`
- `create_skill_section()`
- `create_parameter_section()`
- `create_alarm_section()`
- `create_action_buttons()`
- `create_log_section()`
- `_set_label_frame_bg()`

### 2. GUI主類創建

需要創建 `gui/__init__.py`，包含：

- 主GUI類（從原始文件的 `MapleStoryAutoPrayer` 類遷移）
- 整合所有管理器（ConfigManager, WindowManager, DetectionManager, AutomationManager）
- 實現所有GUI事件處理方法

### 3. 懸浮框模組（可選）

如果需要，可以創建 `overlay.py` 來處理懸浮框相關功能。

## 使用方式

完成GUI遷移後，可以通過以下方式運行：

```bash
python main.py
```

## 模組依賴關係

```
main.py
├── utils.py (日誌)
├── config.py (配置)
├── window_manager.py (視窗)
├── detection.py (檢測，依賴 window_manager)
├── automation.py (自動化，依賴 window_manager, detection)
└── gui/
    ├── styles.py (樣式)
    ├── components.py (組件，依賴所有管理器)
    └── __init__.py (主GUI類，依賴所有模組)
```

## 注意事項

1. 原始文件 `maplestory_auto_prayer.py` 保留作為參考
2. 遷移GUI時需要確保所有變數和方法都正確連接
3. 測試時確保所有功能正常運作

