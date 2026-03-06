# 程式執行流程說明

## 一、程式啟動流程 (main.py)

### 1. 初始化階段
```
main()
├── initialize_logging()           # 初始化日誌系統
├── create_root_window()           # 創建根視窗 (tk.Tk)
├── initialize_config_manager()    # 初始化配置管理器
├── load_configuration()           # 載入配置檔案 (config.json)
├── initialize_window_manager()    # 初始化視窗管理器
├── initialize_detection_manager() # 初始化檢測管理器
├── initialize_automation_manager()# 初始化自動化管理器
├── create_gui_application()       # 創建GUI應用程式
└── start_main_loop()              # 啟動GUI主循環 (root.mainloop())
```

### 2. GUI初始化 (MapleStoryAutoPrayerGUI.__init__)
```
GUI初始化
├── 設置視窗屬性 (標題、大小、背景色)
├── configure_styles()             # 配置GUI樣式
├── create_widgets()               # 創建所有GUI組件
│   ├── create_window_section()   # 視窗設定區域
│   ├── create_skill_section()    # 技能設定區域
│   ├── create_parameter_section() # 進階設定區域
│   ├── create_action_buttons()   # 操作控制按鈕
│   └── create_log_section()      # 系統日誌區域
├── load_config()                  # 載入配置到GUI變數
├── setup_auto_save_bindings()     # 設置自動保存綁定
└── refresh_windows()              # 刷新遊戲視窗列表
```

## 二、自動化執行流程

### 1. 啟動自動化 (start_automation)
```
用戶點擊 START 按鈕
├── 驗證視窗是否已選擇
├── 設置視窗句柄
├── 調整視窗大小 (1295x759)
├── 保存當前配置
├── 設置運行標誌
│   ├── is_running = True
│   └── automation_manager.is_running = True
├── 更新UI狀態 (禁用START，啟用STOP)
├── 啟動自動化線程
│   └── threading.Thread(target=automation_loop)
└── 啟動定時停止檢查 (如果啟用)
```

### 2. 自動化主循環 (automation_loop)

#### 循環結構
```
while is_running:
    ├── [步驟1] 離開自由市場 (如果上次已進入)
    ├── [步驟2] 固定來回移動 (如果啟用且不進入自由市場)
    ├── [步驟3] 檢查是否在自由市場（在執行技能前）
    ├── [步驟4] 執行技能序列
    ├── [步驟5] 進入自由市場 (如果啟用)
    └── [步驟6] 等待間隔時間
```

#### 詳細步驟說明

**步驟1: 離開自由市場（新邏輯）**
```
if last_entered_free_market:
    ├── 移動到目標位置 (exit_target_x)
    │   └── move_to_target_position()
    │       ├── 檢測血條位置
    │       ├── 如果未檢測到血條
    │       │   ├── 清除位置記錄並重新檢測一次
    │       │   └── 如果重新檢測仍失敗
    │       │       └── 終止流程 (正常終止：可能是角色離開隊伍)
    │       ├── 判斷移動方向 (左/右)
    │       └── 持續移動直到到達目標
    ├── 記錄按上鍵前的血條位置
    │   └── 如果未檢測到血條
    │       └── 終止流程 (正常終止：可能是角色離開隊伍)
    ├── 按上鍵一次 (離開自由市場)
    ├── 等待0.5秒
    ├── 檢查血條位置是否有變化
    │   ├── 如果位置有變化
    │   │   └── 檢查是否已離開自由市場
    │   │       ├── 已離開 → 成功
    │   │       └── 仍在自由市場 → 等待動畫完成後再次檢查
    │   └── 如果位置沒有變化 (仍在原地)
    │       ├── 判斷原因1：向上鍵沒有執行完成
    │       │   ├── 再次執行一次向上鍵
    │       │   ├── 等待0.5秒
    │       │   └── 檢查位置是否變化
    │       │       ├── 有變化且已離開 → 成功
    │       │       └── 仍無變化 → 判斷為原因2
    │       └── 判斷原因2：血條並非玩家位置
    │           ├── 排除當前血條位置 (±30像素)
    │           ├── 尋找下一個目標血條位置
    │           ├── 如果找到下一個血條
    │           │   ├── 更新位置記錄 (detect_hp_bar_position 自動更新)
    │           │   ├── 檢查新血條位置是否在離開位置附近
    │           │   │   ├── 如果不在附近 (距離 > 30px)
    │           │   │   │   ├── 移動到新血條位置
    │           │   │   │   ├── 移動回離開位置 (target_x)
    │           │   │   │   └── 等待一小段時間
    │           │   │   └── 如果在附近 (距離 ≤ 30px)
    │           │   │       └── 不需要移動
    │           │   ├── 再次按上鍵
    │           │   └── 檢查是否已離開
            │           └── 如果沒有下一個血條
            │               └── 終止執行流程 (正常終止：可能是角色離開隊伍)
    └── 防偵測移動 (如果啟用)
        └── execute_anti_detection_movement()
            ├── 隨機移動 0~1 次
            ├── 使用配置的方向 (左/右)
            └── 每次移動後等待間隔時間
```

**步驟2: 固定來回移動**
```
if fixed_move and not enter_fm:
    ├── 決定是否執行移動 (每3輪執行一次)
    ├── 決定移動方向 (左右交替)
    ├── 執行移動 (按方向鍵)
    └── 等待0.1秒
```

**步驟3: 檢查是否在自由市場（在執行技能前）**
```
檢查角色是否在自由市場中
├── check_free_market_entered()
└── 如果在自由市場中
    ├── 移動到目標位置 (exit_target_x)
    ├── 離開自由市場
    │   └── exit_free_market_with_position_check()
    │       └── (使用步驟1的離開邏輯)
    └── 防偵測移動 (如果啟用)
        └── execute_anti_detection_movement()
```

**步驟4: 執行技能序列**
```
技能執行順序:
├── 技能1 (prayer_key, 預設: f1) [必須執行]
│   └── send_key_press()
├── 等待技能間隔
├── 技能2 (angel_blessing, 預設: f2) [可選擇是否施放]
│   └── send_key_press()
├── 等待技能間隔
├── 技能3 (custom_skill1, 預設: f3) [可選擇是否施放]
│   └── send_key_press()
├── 等待技能間隔
└── 技能4 (custom_skill2, 預設: f4) [可選擇是否施放]
    └── send_key_press()
```

**步驟5: 進入自由市場（新邏輯）**
```
if enter_fm:
    └── 進入自由市場 (最多重試3次)
        └── enter_free_market(max_retries=3)
            └── 循環重試 (最多3次)
                ├── 點擊自由市場按鈕一次
                │   └── click_free_market_button()
                ├── 點擊後檢測結果
                │   ├── 結果1：檢測到血條 (成功進入自由市場)
                │   │   ├── 設置 last_entered_free_market = True
                │   │   └── 返回成功
                │   ├── 結果2：檢測到確認視窗 (角色已在自由市場)
                │   │   ├── 關閉確認視窗
                │   │   │   └── handle_dialog_window()
                │   │   ├── 設置 last_entered_free_market = True
                │   │   └── 返回成功
                │   └── 結果3：未檢測到血條也沒檢測到確認視窗 (沒有成功進入)
                │       ├── 重試次數 +1
                │       ├── 如果重試次數 < 3
                │       │   ├── 等待後重試
                │       │   └── 回到點擊按鈕步驟
                │       └── 如果重試次數 = 3
                │           ├── 中斷流程
                │           ├── 設置 is_running = False
                │           └── 顯示錯誤訊息 (錯誤：無法進入自由市場)
```

**步驟6: 等待間隔**
```
等待時間 = 自由市場待機時間 ± 隨機範圍 (20秒)
├── _sleep_with_check()
│   ├── 分段檢查 (每0.1秒)
│   ├── 檢查 is_running 狀態
│   ├── 檢查 skip_wait 標誌
│   └── 更新倒數時間 (用於懸浮視窗顯示)
└── 循環回到步驟1
```

### 3. 停止自動化 (stop_automation)
```
用戶點擊 STOP 按鈕
├── 設置停止標誌
│   ├── is_running = False
│   └── automation_manager.is_running = False
├── 更新UI狀態 (啟用START，禁用STOP)
├── 取消定時停止檢查
└── 自動化循環檢測到停止標誌後退出
    ├── 釋放所有按鍵
    ├── 停止倒數更新
    └── 更新UI狀態
```

## 三、核心功能模組

### 1. 視窗管理 (WindowManager)
```
功能:
├── 列舉遊戲視窗
├── 設置當前操作視窗
├── 獲取視窗位置和大小
├── 調整視窗大小
└── 將視窗帶到前景
```

### 2. 圖像檢測 (DetectionManager)
```
功能:
├── detect_hp_bar_position()
│   ├── 截取視窗截圖
│   ├── 檢測紅色血條 (在配置的Y軸位置)
│   ├── 找出連續紅色像素區間
│   ├── 過濾候選 (根據寬度、位置)
│   └── 返回角色位置 (x, y)
├── check_free_market_entered()
│   └── 檢測是否在自由市場內
└── detect_dialog_window()
    └── 檢測提示視窗是否存在
```

### 3. 自動化操作 (AutomationManager)
```
功能:
├── send_key_press()              # 發送按鍵
├── move_to_target_position()     # 移動到目標位置
├── enter_free_market()           # 進入自由市場
├── exit_free_market()            # 離開自由市場
├── click_free_market_button()   # 點擊自由市場按鈕
├── handle_dialog_window()        # 處理提示視窗
├── execute_anti_detection_movement() # 防偵測移動 (隨機移動 0~1 次)
└── _sleep_with_check()           # 可中斷的等待
```

## 四、配置管理流程

### 1. 載入配置
```
啟動時:
├── ConfigManager.load()
│   ├── 檢查 config.json 是否存在
│   ├── 讀取配置檔案
│   ├── 合併預設值
│   └── 返回配置字典
└── GUI載入配置到變數
    └── load_config()
```

### 2. 保存配置
```
自動保存 (當變數改變時):
├── auto_save_config()
│   ├── 收集所有GUI變數
│   ├── 構建配置字典
│   └── ConfigManager.save()
└── 手動保存 (關閉視窗時)
    └── on_closing()
        └── save_config()
```

## 五、錯誤處理機制

### 1. 血條檢測失敗
```
檢測失敗時:
├── 清除位置記錄
├── 重新檢測
├── 如果仍然失敗:
│   ├── 設置 is_running = False
│   ├── 顯示錯誤訊息
│   └── 終止自動化循環
```

### 2. 進入自由市場失敗
```
失敗處理:
├── 檢查是否剛離開自由市場
├── 重新執行整輪邏輯 (離開 -> 技能 -> 進入)
└── 如果重試後仍失敗，記錄警告並繼續
```

### 3. 視窗無效
```
檢查機制:
├── 每次操作前檢查視窗是否有效
├── 如果無效:
│   ├── 記錄錯誤
│   └── 返回 False
```

## 六、執行流程圖

```
啟動程式
    ↓
初始化所有管理器
    ↓
創建GUI
    ↓
等待用戶操作
    ↓
[用戶點擊 START]
    ↓
驗證視窗 → 設置視窗 → 調整大小
    ↓
啟動自動化線程
    ↓
┌─────────────────────┐
│   自動化主循環       │
│                     │
│ 1. 離開自由市場?    │
│ 2. 固定移動?        │
│ 3. 執行技能         │
│ 4. 進入自由市場?    │
│ 5. 等待間隔         │
│                     │
│    (循環)           │
└─────────────────────┘
    ↓
[用戶點擊 STOP 或發生錯誤]
    ↓
設置停止標誌
    ↓
釋放資源
    ↓
更新UI狀態
    ↓
結束
```

## 七、關鍵變數說明

### 運行狀態
- `is_running`: GUI層的運行標誌
- `automation_manager.is_running`: 自動化管理器的運行標誌
- `last_entered_free_market`: 標記上次循環是否進入自由市場

### 配置變數
- `prayer_key_var`: 技能1快捷鍵
- `angel_blessing_var`: 技能2快捷鍵
- `custom_skill1_key_var`: 技能3快捷鍵
- `custom_skill2_key_var`: 技能4快捷鍵
- `fm_wait_var`: 自由市場待機時間
- `enter_fm_var`: 是否進入自由市場
- `fixed_move_var`: 是否固定來回移動

### 檢測相關
- `detection_manager.last_character_x`: 上次檢測到的角色X位置
- `detection_manager.last_hp_bar_info`: 上次檢測到的血條信息

## 八、線程安全

- GUI操作在主線程 (tkinter主循環)
- 自動化操作在獨立線程
- 使用 `root.after()` 確保GUI更新在主線程執行
- 使用標誌變數控制線程同步
