# GUI架構說明

## 設計理念

從基礎配色開始，逐層向上構建GUI系統，確保：
- **一致性**：所有組件使用統一的配色和樣式
- **可維護性**：配色集中管理，易於修改
- **可擴展性**：組件化設計，易於添加新功能

## 架構層次

```
┌─────────────────────────────────────┐
│   components.py (組件組合層)        │  ← 使用基礎組件組合功能區塊
├─────────────────────────────────────┤
│   layout.py (布局系統層)            │  ← 定義標準化布局結構
├─────────────────────────────────────┤
│   widgets.py (基礎組件層)           │  ← 主題化基礎組件
├─────────────────────────────────────┤
│   styles.py (樣式應用層)            │  ← 將主題應用到ttk控件
├─────────────────────────────────────┤
│   theme.py (配色定義層)              │  ← 基礎配色常量定義
└─────────────────────────────────────┘
```

## 模組說明

### 1. theme.py - 配色定義層
**職責**：定義所有顏色常量、字體、間距等基礎配置

**主要內容**：
- 背景色：PRIMARY, SECONDARY, TERTIARY
- 文字色：PRIMARY, SECONDARY, HIGHLIGHT
- 按鈕色：PRIMARY, SECONDARY, DANGER
- 邊框色、輸入框色、狀態色等
- 字體配置、間距配置

**使用方式**：
```python
from gui.theme import Theme

# 使用顏色
bg = Theme.BACKGROUND_PRIMARY
text_color = Theme.TEXT_PRIMARY

# 使用字體
font = Theme.get_font_config(Theme.FONT_SIZE_NORMAL, 'bold')
```

### 2. styles.py - 樣式應用層
**職責**：將主題配色應用到ttk控件樣式

**主要內容**：
- 配置所有ttk控件樣式（Button, Entry, Checkbutton等）
- 定義hover、focus等狀態樣式
- 返回配置好的Style對象

**使用方式**：
```python
from gui.styles import configure_styles

configure_styles()  # 在應用啟動時調用一次
```

### 3. widgets.py - 基礎組件層
**職責**：創建主題化的基礎組件類

**主要組件**：
- `ThemedFrame`：主題化Frame
- `ThemedLabel`：主題化Label
- `ThemedButton`：主題化Button（支持primary/secondary/danger變體）
- `ThemedEntry`：主題化Entry
- `ThemedText`：主題化Text
- `ThemedLabelFrame`：主題化LabelFrame
- `SectionFrame`：統一的區塊容器

**使用方式**：
```python
from gui.widgets import ThemedButton, ThemedLabel

button = ThemedButton(parent, "按鈕", command=callback, variant='primary')
label = ThemedLabel(parent, "標籤", size=Theme.FONT_SIZE_LARGE)
```

### 4. layout.py - 布局系統層
**職責**：定義標準化布局結構和布局助手

**主要類**：
- `LayoutManager`：管理整體布局結構
  - `create_main_layout()`：創建主布局
  - `create_title_section()`：創建標題區域
  - `create_top_section()`：創建頂部區域（左右分欄）
  - `get_left_panel()` / `get_right_panel()`：獲取面板
  
- `GridLayout`：網格布局助手
- `FormLayout`：表單布局助手

**使用方式**：
```python
from gui.layout import LayoutManager

layout = LayoutManager(root)
layout.create_main_layout()
left_panel = layout.get_left_panel()
```

### 5. components.py - 組件組合層
**職責**：使用基礎組件和布局系統組合功能區塊

**主要函數**：
- `create_window_section()`：視窗設定區塊
- `create_skill_section()`：技能設定區塊
- `create_parameter_section()`：參數設定區塊
- `create_alarm_section()`：警報設定區塊
- `create_action_buttons()`：操作按鈕區塊
- `create_log_section()`：日誌區塊

**特點**：
- 使用`SectionFrame`創建統一的區塊容器
- 使用`ThemedLabel`、`ThemedButton`等主題化組件
- 使用`Theme`常量定義間距和顏色

### 6. __init__.py - GUI主類
**職責**：整合所有模組，創建完整的GUI應用

**主要內容**：
- `MapleStoryAutoPrayerGUI`類
- 整合所有管理器（config, window, detection, automation）
- 使用LayoutManager創建布局
- 調用components函數創建各個區塊

## 配色方案

### 主色調
- **背景**：深藍黑 (#0A0E27) - 科技感深色背景
- **主色**：青色 (#00D9FF) - 科技感主色調
- **輔色**：亮藍 (#4A9EFF) - 輔助色調

### 按鈕變體
- **Primary**：青色按鈕，用於主要操作（START）
- **Secondary**：灰藍按鈕，用於次要操作
- **Danger**：紅色按鈕，用於危險操作（STOP）

## 擴展指南

### 添加新顏色
在`theme.py`中添加新的顏色常量：
```python
NEW_COLOR = '#HEXCODE'
```

### 添加新組件
在`widgets.py`中創建新的主題化組件類：
```python
class ThemedNewWidget(tk.Widget):
    def __init__(self, parent, **kwargs):
        # 使用Theme常量配置樣式
        super().__init__(parent, bg=Theme.BACKGROUND_PRIMARY, ...)
```

### 添加新區塊
在`components.py`中添加新函數：
```python
def create_new_section(parent, app):
    section = SectionFrame(parent, "新區塊標題")
    frame = section.get_frame()
    # 使用Themed組件創建內容
```

## 優勢

1. **統一配色**：所有顏色在theme.py中集中管理
2. **易於修改**：只需修改theme.py即可改變整個應用配色
3. **組件化**：每個組件都是獨立的，易於重用
4. **層次清晰**：從配色到組件到布局，層次分明
5. **類型安全**：使用類常量，避免硬編碼顏色值


