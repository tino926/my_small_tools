## mmex_kivy_app.py 流程邏輯概述

`mmex_kivy_app.py` 是一個使用 Kivy 框架開發的桌面應用程式，用於讀取和顯示 
MoneyManagerEx (MMEX) 資料庫 (`.mmb` 檔案) 中的財務交易記錄。

### 1. 應用程式架構與常數定義

- **模組化設計**:
  - `db_utils.py`: 資料庫工具函數
  - `ui_components.py`: UI 元件類別
  - `visualization.py`: 資料視覺化函數
  - `mmex_kivy_app.py`: 主應用程式程式碼

- **UIConstants 類別**:
  - 集中管理所有 UI 相關常數，包括視窗尺寸、字型大小、元件高度等
  - `TRANSACTION_HEADERS`: 交易表格標題
  - `FILTER_OPTIONS`: 篩選選項
  - `DATE_FORMAT`: 統一的日期格式 ("%Y-%m-%d")

### 2. 應用程式啟動 (`MMEXKivyApp` class)

- **`build()` 方法**:
  - 設定 Kivy 視窗的背景顏色和最小尺寸
  - **載入字型**:
    - 檢查 `UNICODE_FONT_PATH` (預設為 `fonts/NotoSansCJKtc-Regular.otf`) 是否存在
    - 如果字型檔案存在，則透過 `Builder.load_string()` 將此字型設定為各種 Kivy 元件的預設字型
    - 確保對中文字元等的良好支援
  - 建立並回傳主佈局 `MMEXAppLayout` 的實例

### 3. 主佈局初始化 (`MMEXAppLayout.__init__`)

- **狀態變數初始化**:
  - `self.db_path`: 從 `load_db_path()` 載入的資料庫路徑
  - `self.current_sort_column` 和 `self.current_sort_ascending`: 排序狀態
  - `self.all_transactions_df` 和 `self.filtered_transactions_df`: 交易資料框
  - `self.account_tabs`: 帳戶分頁字典

- **UI 元件建立** (透過輔助方法):
  - `_create_date_inputs()`: 建立日期輸入欄位
  - `_create_search_filter_layout()`: 建立搜尋和篩選介面
  - `_create_tabbed_panel()`: 建立分頁面板
  - `_create_exit_button()`: 建立退出按鈕

- **資料初始化**:
  - `load_account_specific_tabs()`: 載入帳戶專用分頁
  - `run_global_query()`: 執行初始全域查詢

### 4. 核心資料擷取函式 (db_utils.py)

所有資料庫函數現在都採用統一的錯誤處理模式，回傳 `(error_message, data)` 元組：

- **`load_db_path()`**:
  - 從 `.env` 檔案載入 `DB_FILE_PATH` 環境變數
  - 包含完整的檔案存在性檢查和錯誤處理

- **`get_all_accounts(db_path)`**:
  - 回傳格式: `(error_message, DataFrame)`
  - 包含資料庫路徑驗證和 SQLite 錯誤處理
  - 查詢帳戶 ID、名稱和初始餘額

- **`get_transactions(db_path, start_date_str, end_date_str, account_id=None)`**:
  - 回傳格式: `(error_message, DataFrame)`
  - 包含完整的參數驗證 (日期格式、邏輯範圍檢查)
  - 支援標籤查詢，在標籤表格不存在時優雅降級
  - 具體的 SQLite 和 Pandas 錯誤處理

- **`calculate_balance_for_account(db_path, account_id, date=None)`**:
  - 回傳格式: `(error_message, balance)`
  - 包含輸入驗證和資料庫檔案存在性檢查
  - 處理帳戶不存在的情況
  - 自動從資料庫讀取初始餘額

### 5. 全域查詢與資料處理

- **`run_global_query()`**:
  - 從日期輸入欄位獲取查詢範圍
  - 呼叫 `get_transactions()` 並處理錯誤回傳
  - 將結果儲存在 `self.all_transactions_df`
  - 自動呼叫 `apply_search_filter()` 更新篩選結果

- **`apply_search_filter()`**:
  - 根據搜尋條件和篩選類型處理資料
  - 更新 `self.filtered_transactions_df`
  - 刷新目前活動分頁的顯示

- **日期驗證與變更處理**:
  - `_validate_date()`: 使用 `UIConstants.DATE_FORMAT` 驗證日期格式
  - `_on_date_change()`: 在日期變更時觸發查詢，包含驗證邏輯

### 6. 分頁管理與切換 (重構後的模組化設計)

- **`on_tab_switch(instance, tab)`**: 主要分頁切換處理器
  - 根據分頁類型呼叫對應的更新方法
  - 支援「所有交易」、「圖表」和帳戶專用分頁

- **`_update_all_transactions_tab()`**: 
  - 使用 `populate_grid_with_dataframe()` 更新所有交易網格
  - 顯示篩選後的交易數量
  - 支援排序功能

- **`_update_account_tab(account_name)`**:
  - 根據帳戶名稱篩選交易資料
  - 更新帳戶專用網格和狀態標籤
  - 呼叫 `_update_account_balance()` 更新餘額

- **`_update_account_balance(account_id, account_info, content)`**:
  - 包含日期驗證邏輯
  - 呼叫 `calculate_balance_for_account()` 並處理錯誤
  - 格式化餘額顯示

- **`load_account_specific_tabs()`**:
  - 處理 `get_all_accounts()` 的錯誤回傳
  - 為每個帳戶建立 `AccountTabContent` 實例
  - 將帳戶資訊儲存在 `self.account_tabs` 字典中

### 7. UI 元件建立方法

- **`_create_date_inputs()`**:
  - 建立開始和結束日期輸入欄位
  - 綁定 `_on_date_change` 事件處理器
  - 使用 `UIConstants` 中定義的高度和間距

- **`_create_search_filter_layout()`**:
  - 建立搜尋輸入欄位和篩選按鈕
  - 支援多種篩選類型 (所有欄位、帳戶、收款人等)
  - 包含清除篩選功能

- **`_create_tabbed_panel()`**:
  - 建立主分頁面板
  - 包含「所有交易」、「圖表」和帳戶專用分頁
  - 使用統一的分頁樣式設定

- **`_create_exit_button()`**:
  - 建立退出按鈕並綁定事件

### 8. 資料顯示與排序

- **`populate_grid_with_dataframe()` (來自 ui_components.py)**:
  - 模組化的網格填充函數
  - 支援可點擊的欄位標題進行排序
  - 使用 `UIConstants.TRANSACTION_HEADERS` 定義欄位
  - 自動處理空資料和錯誤狀態

- **排序功能**:
  - `sort_transactions()`: 處理欄位排序邏輯
  - 支援升序/降序切換
  - 記住目前排序狀態

### 9. 搜尋與篩選功能

- **搜尋功能**:
  - `_on_search_change()`: 即時搜尋事件處理
  - 支援多欄位搜尋 (帳戶、收款人、分類、備註、標籤)
  - 不區分大小寫的文字匹配

- **篩選功能**:
  - `_show_filter_options()`: 顯示篩選選項彈出視窗
  - `_select_filter_option()`: 處理篩選選項選擇
  - `_clear_search_filter()`: 清除所有搜尋和篩選條件

### 10. 錯誤處理與使用者介面

- **統一錯誤處理**:
  - 所有資料庫函數都回傳 `(error, data)` 元組
  - 使用 `show_popup()` (來自 ui_components.py) 顯示錯誤訊息
  - 包含具體的錯誤類型處理 (SQLite 錯誤、檔案不存在等)

- **輸入驗證**:
  - `_validate_date()`: 統一的日期格式驗證
  - 資料庫路徑存在性檢查
  - 參數完整性驗證

### 11. 視覺化功能

- **圖表分頁**:
  - 整合 `VisualizationTab` 類別
  - 支援收入/支出趨勢圖表
  - 分類別支出分析

### 12. 組態與常數管理

- **UIConstants 類別**:
  - 集中管理所有 UI 相關常數
  - 包含視窗尺寸、字型大小、元件高度等
  - 統一的交易標題和篩選選項定義

- **模組化設計**:
  - 資料庫操作分離到 `db_utils.py`
  - UI 元件分離到 `ui_components.py`
  - 視覺化功能分離到 `visualization.py`

- **設定檔案**:
  - `.env` 檔案儲存資料庫路徑
  - 字型檔案路徑設定
  - 資料庫結構常數定義

### 13. 程式碼品質改進

- **模組化重構**:
  - 將大型方法拆分為小型輔助方法
  - 提高程式碼可讀性和維護性
  - 減少程式碼重複

- **一致性改進**:
  - 統一的錯誤處理模式
  - 一致的命名慣例
  - 標準化的回傳格式

這個重構後的架構提供了更好的可維護性、錯誤處理和使用者體驗，同時保持了原有的所有功能。
