## mmex_kivy_app.py 流程邏輯概述

`mmex_kivy_app.py` 是一個使用 Kivy 框架開發的桌面應用程式，用於讀取和顯示 MoneyManagerEx (MMEX) 資料庫 (`.mmb` 檔案) 中的財務交易記錄。

### 1. 應用程式啟動 (`MMEXKivyApp` class)

-   **`build()` 方法**:
  - 設定 Kivy 視窗的背景顏色 (`Window.clearcolor`)。
  - **載入字型**:
    - 檢查 `UNICODE_FONT_PATH` (預設為 `fonts/NotoSansCJKtc-Regular.otf`) 是否存在。
    - 如果字型檔案存在，則透過 `Builder.load_string()` 將此字型設定為 `Label`, `TextInput`, `Button`, `TabbedPanelHeader` 等 Kivy 元件的預設字型。這確保了對中文字元等的良好支援。
    - 如果字型檔案不存在或載入失敗，會印出警告訊息，Kivy 將使用其預設字型。
  - 建立並回傳主佈局 `MMEXAppLayout` 的實例。

### 2. 主佈局初始化 (`MMEXAppLayout.__init__`)

- 設定佈局方向為垂直 (`orientation="vertical"`)，並設定邊距和間距。
- **載入資料庫路徑**:
  - 呼叫 `load_db_path()` 從專案根目錄下的 `.env` 檔案中讀取 `DB_FILE_PATH`。
  - 將路徑儲存在 `self.db_file_path`。
- **建立 UI 元件**:
  - **資料庫路徑標籤 (`self.db_path_label`)**: 顯示目前使用的資料庫檔案路徑。
  - **日期輸入區塊**:
    - 包含「開始日期」和「結束日期」的 `TextInput` 元件。
    - 預設開始日期為上個月的第一天，結束日期為今天。
    - 綁定 `on_text_validate` 事件到 `trigger_global_query_on_date_change` 方法，當使用者在日期輸入框中按下 Enter 或焦點移開時，會觸發全域查詢。
  - **分頁面板 (`self.tab_panel`)**:
    - 用於顯示「所有交易」和各個帳戶的交易。
    - 綁定 `current_tab` 事件到 `on_tab_switch` 方法，用於處理分頁切換邏輯。
  - **建立「所有交易」分頁 (`_create_all_transactions_tab`)**:
    - 建立一個固定的 `TabbedPanelHeader` 標題為 "All"。
    - 其內容包含一個狀態標籤 (`self.all_transactions_status_label`) 和一個用於顯示交易的 `GridLayout` (`self.all_transactions_grid`)，此網格位於 `ScrollView` 內。
    - 將此分頁設為預設分頁。
  - **載入帳戶專用分頁 (`load_account_specific_tabs`)**:
    - 呼叫 `get_all_accounts()` 從資料庫讀取所有帳戶列表。
    - 如果成功讀取，為每個帳戶動態建立一個 `TabbedPanelHeader`。
    - 每個帳戶分頁的內容是 `AccountTabContent` 類別的實例，其中包含該帳戶的狀態標籤和交易顯示網格。
  - **退出按鈕 (`self.exit_button`)**: 綁定 `on_press` 事件到 `exit_app` 方法。
- **初始資料載入**:
  - 呼叫 `self.run_global_query(None)` 以在應用程式啟動時自動執行一次全域查詢，載入預設日期範圍內的交易。

### 3. 核心資料擷取函式

- **`load_db_path()`**:
  - 從 `.env` 檔案載入 `DB_FILE_PATH` 環境變數。
- **`get_all_accounts(db_file)`**:
  - 連接到指定的 MMEX 資料庫檔案。
  - 執行 SQL 查詢，從 `ACCOUNTLIST_V1` (由 `DB_TABLE_ACCOUNTS` 常數定義) 表格中選取 `ACCOUNTID` 和 `ACCOUNTNAME`。
  - 將查詢結果轉換為 Pandas DataFrame。
  - 回傳錯誤訊息 (如果有的話) 和包含帳戶資料的 DataFrame。
- **`get_transactions(db_file, start_date_str, end_date_str, account_id=None)`**:
  - *此函數在之前的對話中已被修改以支援標籤 (tags) 的讀取，並在標籤相關表格不存在時優雅地回退。*
  - 驗證日期字串格式。
  - 連接到 MMEX 資料庫。
  - **建構 SQL 查詢**:
    - **主要查詢 (嘗試包含標籤)**:
      - `SELECT` 交易日期 (`TRANSDATE`)、帳戶名稱 (`ACCOUNTNAME`)、收款人 (`PAYEENAME`)、分類 (`CATEGNAME`)、備註 (`NOTES`)、金額 (`TRANSAMOUNT`) 以及使用 `GROUP_CONCAT(DISTINCT tag.TAGNAME)` 彙總的標籤 (`TAGS`)。
      - `FROM CHECKINGACCOUNT_V1` (交易表)。
      - `LEFT JOIN` `ACCOUNTLIST_V1` (帳戶表)、`PAYEE_V1` (收款人表)、`CATEGORY_V1` (分類表)。
      - `LEFT JOIN CHECKINGACCOUNT_TAGS_V1` (交易-標籤對應表) 和 `TAGS_V1` (標籤表) 來獲取標籤資訊。
      - `WHERE TRANSDATE` 在指定的開始和結束日期之間 (結束日期會加一天以包含當天)。
      - 如果提供了 `account_id`，則增加 `AND ACCOUNTID = ?` 的篩選條件。
      - `GROUP BY trans.TRANSID` 以確保每個交易只有一列，並正確彙總標籤。
      - `ORDER BY TRANSDATE ASC, TRANSID ASC`。
    - **備援查詢 (不含標籤)**:
      - 如果上述包含標籤的查詢因為找不到 `CHECKINGACCOUNT_TAGS_V1` 或 `TAGS_V1` 表格而失敗 (捕獲 `sqlite3.OperationalError` 或 `pd.io.sql.DatabaseError`)：
        - 會印出警告訊息。
        - 設定 `tags_column_present = False`。
        - 執行一個不包含標籤相關 `SELECT`、`JOIN` 或 `GROUP BY` 的簡化版 SQL 查詢。
  - 使用 `pd.read_sql_query()` 執行查詢並將結果載入 DataFrame。
  - 回傳錯誤訊息 (如果有的話)、包含交易資料的 DataFrame，以及一個布林值 `tags_column_present` 指示標籤欄位是否成功查詢。

### 4. 全域查詢邏輯 (`run_global_query`)

- 當日期輸入改變或應用程式初次載入時觸發。
- 獲取開始和結束日期輸入框中的值。
- 檢查資料庫路徑是否已設定。
- 更新「所有交易」分頁的狀態標籤為「查詢中...」。
  - 呼叫 `get_transactions()`，傳入 `account_id=None` 以獲取所有帳戶在指定日期範圍內的交易。
  - 將查詢結果 (DataFrame) 儲存在 `self.all_transactions_df`。
  - 將 `get_transactions()` 回傳的 `tags_were_queried_successfully` 標誌儲存在 `self.tags_available_in_current_df`。
  - 如果查詢成功且有資料：
    - 呼叫 `_populate_grid_with_dataframe()` 將 `self.all_transactions_df` 的內容填充到「所有交易」分頁的網格中。
  - 如果查詢失敗或沒有資料，顯示相應的錯誤或提示訊息。
  - 呼叫 `self.on_tab_switch()` 以刷新目前活動分頁的內容 (因為全域資料已更新)。

### 5. 分頁管理與切換

- **`_create_all_transactions_tab()`**: 如上所述，建立固定的「所有交易」分頁。
- **`load_account_specific_tabs()`**:
  - 從資料庫獲取所有帳戶。
  - 為每個帳戶建立一個 `TabbedPanelHeader` (作為分頁標題) 和一個 `AccountTabContent` (作為分頁內容)。
  - 將帳戶 ID 和完整帳戶名稱儲存在 `TabbedPanelHeader` 物件上，方便後續取用。
- **`on_tab_switch(tab_panel_instance, current_tab_header)`**:
  - 當使用者切換分頁時觸發。
  - **如果切換到「所有交易」分頁**:
    - 使用 `self.all_transactions_df` 和 `self.tags_available_in_current_df` 重新填充其網格 (`self.all_transactions_grid`)。
  - **如果切換到某個帳戶專用分頁**:
    - 檢查 `self.all_transactions_df` 是否存在 (即全域查詢是否已執行)。
    - 如果存在，則從 `self.all_transactions_df` 中篩選出屬於該帳戶的交易記錄 (目前是基於 `ACCOUNTNAME` 進行篩選)。
    - 使用篩選後的 DataFrame 和 `self.tags_available_in_current_df` 填充該帳戶分頁的網格。
    - 如果 `self.all_transactions_df` 不存在，提示使用者先執行全域查詢。

### 6. 資料顯示 (`_populate_grid_with_dataframe`)

- 此輔助函式用於將 DataFrame 中的資料填充到指定的 Kivy `GridLayout` 中。
- **參數**:
  - `target_grid`: 要填充的 `GridLayout` 元件。
  - `df`: 包含交易資料的 Pandas DataFrame。
  - `status_label_widget`: 用於顯示狀態訊息的 `Label` 元件。
  - `tags_available`: 布林值，指示是否應顯示「標籤」欄。
  - `status_message_prefix`: 狀態訊息的前綴。
- **流程**:
  - 清除 `target_grid` 中的所有現有元件。
  - 如果 `df` 為空或 `None`，顯示「無資料」訊息。
  - **動態設定欄數和表頭**:
    - 如果 `tags_available` 為 `True` 且 DataFrame 中存在 "TAGS" 欄，則設定網格為 7 欄，表頭包含 "Tags"。
    - 否則，設定網格為 6 欄，表頭不含 "Tags"。
  - 為每個表頭文字建立 `Label` 並加入網格。
  - 遍歷 DataFrame 的每一列：
    - 格式化日期 (移除時間部分)。
    - 建立包含該行各欄位資料的列表 (根據 `tags_available` 決定是否包含標籤資料)。
    - 為列表中的每個項目建立 `Label` 並加入網格。
  - 更新 `status_label_widget` 的文字，顯示找到的記錄數量或「無記錄」訊息。

### 7. 事件處理

- **日期輸入驗證 (`trigger_global_query_on_date_change`)**: 當日期輸入框失去焦點或按下 Enter 時，呼叫 `run_global_query()`。
- **分頁切換 (`on_tab_switch`)**: 如上所述，處理分頁內容的更新。
- **退出按鈕 (`exit_app`)**: 呼叫 `App.get_running_app().stop()` 關閉應用程式。

### 8. 錯誤處理與彈出視窗

- **`show_popup(title, message)`**:
  - 建立一個包含標題、訊息和關閉按鈕的 `Popup` 元件。
  - 用於向使用者顯示錯誤訊息或提示。
  - 彈出視窗中訊息文字的顏色已調整為 `DEFAULT_TEXT_COLOR_ON_DARK_BG` (白色)，以確保在深色背景下可見。
- 資料庫操作 (如連接、查詢) 和日期解析都包含在 `try-except` 區塊中，捕獲到的錯誤會透過 `show_popup` 顯示給使用者。

### 9. 組態設定

- **`.env` 檔案**: 儲存 `DB_FILE_PATH`，即 MMEX 資料庫檔案的路徑。
- **字型路徑 (`UNICODE_FONT_PATH`)**: 指定用於 UI 的字型檔案路徑。
- **資料庫結構常數**:
  - `DB_TABLE_*` 和 `DB_FIELD_*` 常數定義了 MMEX 資料庫中相關表格和欄位的名稱。這使得在程式碼中引用這些名稱更加方便，並且如果 MMEX 的資料庫結構在未來版本中發生變化，也更容易更新。
  - 包含與交易、帳戶、收款人、分類以及標籤相關的表格和欄位。

這個流程概述應該能幫助開發者理解 `mmex_kivy_app.py` 的主要工作方式和不同部分之間的交互。
