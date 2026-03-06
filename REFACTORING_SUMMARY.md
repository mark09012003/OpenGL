# 程式重構總結

## 重構目標
將各個執行步驟分門別類，每個動作都列為單一函數，提高程式碼的可讀性、可維護性和可測試性。

## 重構內容

### 1. main.py - 主入口文件
**重構前：** 所有初始化步驟都在 `main()` 函數中
**重構後：** 將初始化步驟拆分為以下獨立函數：
- `initialize_logging()` - 初始化日誌系統
- `create_root_window()` - 創建根視窗
- `initialize_config_manager(logger)` - 初始化配置管理器
- `load_configuration(config_manager)` - 載入配置
- `initialize_window_manager(logger)` - 初始化視窗管理器
- `initialize_detection_manager(window_manager, config, logger)` - 初始化檢測管理器
- `initialize_automation_manager(window_manager, detection_manager, config, logger)` - 初始化自動化管理器
- `create_gui_application(...)` - 創建GUI應用程式
- `start_main_loop(root, logger)` - 啟動主循環

### 2. utils.py - 工具模組
**重構前：** `setup_logging()` 函數包含所有日誌設置邏輯
**重構後：** 拆分為以下函數：
- `get_default_log_level()` - 獲取預設日誌級別
- `get_default_log_format()` - 獲取預設日誌格式
- `create_console_handler()` - 創建控制台日誌處理器
- `create_log_handlers()` - 創建所有日誌處理器
- `configure_logging_basic_config(level, format_str, handlers)` - 配置日誌基本設定
- `get_logger(name)` - 獲取日誌記錄器
- `setup_logging()` - 設定日誌系統（協調上述函數）

### 3. config.py - 配置管理模組
**重構前：** 配置操作都在類方法中
**重構後：** 提取以下獨立函數：
- `create_default_config()` - 創建預設配置字典
- `check_config_file_exists(config_file)` - 檢查配置檔案是否存在
- `read_config_file(config_file)` - 讀取配置檔案內容
- `create_config_copy(config)` - 創建配置的副本
- `merge_top_level_config(default_config, loaded_config)` - 合併頂層配置
- `get_nested_config_keys()` - 獲取需要合併的嵌套配置鍵列表
- `merge_nested_config(merged_config, loaded_config, nested_keys)` - 合併嵌套配置
- `write_config_file(config_file, config_data)` - 寫入配置檔案

### 4. window_manager.py - 視窗管理模組
**重構前：** 視窗操作邏輯混雜在類方法中
**重構後：** 提取以下獨立函數：
- `is_window_visible(hwnd)` - 檢查視窗是否可見
- `get_window_title(hwnd)` - 獲取視窗標題
- `add_window_to_list(hwnd, title, windows)` - 將視窗添加到列表
- `filter_windows_by_prefix(windows, filter_prefix)` - 根據前綴過濾視窗列表
- `validate_window_handle(hwnd)` - 驗證視窗句柄是否有效
- `convert_rect_to_position_size(rect)` - 將視窗矩形轉換為位置和大小
- `check_window_minimized(hwnd)` - 檢查視窗是否最小化
- `restore_minimized_window(hwnd)` - 還原最小化的視窗
- `set_foreground_window(hwnd)` - 設置前景視窗
- `bring_window_to_top(hwnd)` - 將視窗置頂
- `validate_window_dimensions(width, height)` - 驗證視窗尺寸是否有效
- `get_window_position(rect)` - 從矩形獲取視窗位置
- `set_window_position_and_size(hwnd, x, y, width, height)` - 設置視窗位置和大小

### 5. detection.py - 圖像檢測模組
**重構前：** 檢測邏輯複雜且冗長
**重構後：** 提取以下輔助函數：
- `get_detection_config_value(config, key, default_value)` - 從配置中獲取檢測參數值
- `extract_rgb_channels(img_array)` - 從圖像數組中提取RGB通道
- `create_red_mask(...)` - 創建紅色血條的顏色遮罩
- `validate_target_y_coordinate(target_y, window_height)` - 驗證目標Y座標是否在視窗範圍內
- `find_red_pixels_in_row(red_mask, target_y)` - 在指定Y軸位置查找紅色像素
- `create_candidate_interval(start_x, end_x, y)` - 創建候選區間字典
- `find_continuous_red_intervals(row_red_pixels, y, pixel_gap_tolerance)` - 找出連續的紅色像素區間
- `filter_candidates_by_width(candidates, min_width, max_width)` - 根據寬度過濾候選
- `is_candidate_in_exclude_range(candidate, exclude_x_range)` - 檢查候選是否在排除範圍內
- `calculate_distance(x1, x2)` - 計算兩個X座標之間的距離
- `is_candidate_close_to_last_position(candidate, last_character_x, character_x_tolerance)` - 檢查候選是否接近上次位置
- `separate_candidates_by_priority(...)` - 將候選分為高優先級和低優先級
- `find_closest_candidate(candidates, last_character_x, character_x_tolerance)` - 找到與上次位置最接近的候選
- `calculate_character_position(candidate, character_y_offset)` - 計算角色位置
- `create_hp_bar_info(candidate, character_x, character_y)` - 創建血條信息字典
- `grab_window_screenshot(window_x, window_y, window_width, window_height)` - 截取視窗截圖
- `convert_screenshot_to_array(screenshot)` - 將截圖轉換為數組
- `check_dialog_region_in_bounds(...)` - 檢查對話框檢測區域是否在視窗範圍內
- `grab_dialog_region_screenshot(...)` - 截取對話框檢測區域的截圖
- `calculate_color_match_ratio(...)` - 計算顏色匹配比例
- `calculate_average_rgb(img_array)` - 計算圖像的平均RGB值

### 6. automation.py - 自動化邏輯模組
**重構前：** 自動化操作邏輯複雜
**重構後：** 提取以下輔助函數：
- `get_automation_config_value(config, key, default_value)` - 從配置中獲取自動化參數值
- `configure_pyautogui_safety()` - 配置pyautogui安全模式
- `validate_key(key)` - 驗證按鍵是否有效
- `press_key_down(key)` - 按下按鍵
- `press_key_up(key)` - 釋放按鍵
- `calculate_sleep_chunks(sleep_time, chunk_size)` - 計算睡眠分塊數量
- `calculate_chunk_duration(sleep_time, sleep_chunks)` - 計算每個分塊的持續時間
- `calculate_remaining_time(duration, elapsed)` - 計算剩餘時間
- `calculate_button_absolute_position(window_x, window_y, button_x, button_y)` - 計算按鈕的絕對座標
- `click_button(button_x, button_y)` - 點擊按鈕
- `calculate_exclude_range(target_x, tolerance)` - 計算排除範圍
- `calculate_distance_to_target(current_x, target_x)` - 計算到目標位置的距離
- `is_position_reached(current_x, target_x, tolerance)` - 檢查是否已到達目標位置
- `determine_movement_direction(current_x, target_x)` - 判斷移動方向
- `release_all_movement_keys()` - 釋放所有移動按鍵
- `calculate_skill_interval(base_interval, random_range)` - 計算技能執行間隔
- `generate_random_move_count(min_moves, max_moves)` - 生成隨機移動次數
- `get_move_key_for_direction(direction)` - 根據方向獲取移動按鍵
- `calculate_dialog_button_absolute_position(...)` - 計算對話框按鈕的絕對座標

## 重構優勢

1. **可讀性提升**：每個函數職責單一，函數名稱清晰表達功能
2. **可維護性提升**：修改某個功能時只需關注對應的函數
3. **可測試性提升**：每個函數都可以獨立測試
4. **可重用性提升**：輔助函數可以在多處重用
5. **代碼組織更清晰**：相關功能分門別類，易於查找和理解

## 注意事項

- 所有重構後的代碼都通過了 linter 檢查，沒有語法錯誤
- 保持了原有的功能邏輯不變
- 函數參數和返回值保持一致
- 日誌記錄和錯誤處理邏輯保持不變
